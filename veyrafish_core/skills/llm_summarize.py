# -*- coding: utf-8 -*-
"""LLMSummarizeSkill — 证据约束的首次总结 / 反思更新。"""

from __future__ import annotations

from loguru import logger
from pydantic import BaseModel

from veyrafish_core.skill import Skill, SkillContext
from veyrafish_core.skills._models import SummarizeInput, SummarizeOutput

_FIRST_SUMMARY_SYSTEM = """你是“首轮证据压缩器”，不是自由写作者。

任务：
给定一个段落主题 paragraph_title 和一组搜索结果 search_results，
只提取与该主题直接相关的事实、数据、主体、观点和未决问题，
生成可被后续报告写作消费的结构化摘要。

硬性规则：
1. 只能使用输入中明确出现的信息，不得补充外部常识，不得脑补因果。
2. 优先保留时间、主体、事件、数字、结论、来源共识。
3. 多个结果重复表达同一事实时，应合并为一条 key_point。
4. 结果之间存在冲突时，不要强行统一，写入 conflicts。
5. 证据不足以支持明确结论时，summary 保守表达，并写入 uncertainties。
6. summary 必须紧扣 paragraph_title，不得扩展到其他主题。
7. key_points 必须是可被引用的事实或观点，不能写空泛套话。
8. confidence 是 0~1 小数，表示摘要被输入证据支撑的充分程度。

输出 JSON 字段：
summary, key_points, conflicts, uncertainties, entities, confidence。"""

_REFLECTION_SYSTEM = """你是“增量修订器”，不是重写器。

任务：
给定旧摘要 previous_summary、旧关键点 previous_key_points 和新搜索结果 new_search_results，
对已有结论做增量更新：补充缺失信息、修正错误、强化或削弱已有判断，
并明确说明更新原因。

硬性规则：
1. 先判断新证据与旧摘要的关系：强化 / 修正 / 否定 / 无新增价值。
2. 不要简单重写旧摘要；必须体现更新痕迹。
3. 新证据与旧结论冲突时，保留冲突并说明原因，不得强行融合。
4. 新证据只是重复旧信息时，不要重复写入 key_points。
5. 新证据提升确定性时可提高 confidence；制造冲突或不确定性时应降低 confidence。
6. 所有新增内容必须来自 new_search_results。
7. 输出必须适合被后续 report skill 直接消费。

输出 JSON 字段：
summary, key_points, retained_points, new_points, revised_points,
conflicts, uncertainties, change_log, entities, confidence。"""


class LLMSummarizeSkill(Skill):
    """LLM 驱动的证据摘要 Skill，区分首轮压缩与增量修订。"""

    name = "llm_summarize"
    description = "使用 LLM 对搜索结果做证据约束摘要，支持首轮压缩和增量修订"
    version = "0.1.0"
    tags = ["llm", "summarize", "analysis"]
    input_schema = SummarizeInput
    output_schema = SummarizeOutput

    def execute(self, input: SummarizeInput, ctx: SkillContext) -> SummarizeOutput:
        if ctx.llm_client is None:
            return self._fallback_output(input, reason="LLM 客户端不可用，已使用规则降级摘要")

        is_reflection = input.mode == "reflection_summary"
        system = _REFLECTION_SYSTEM if is_reflection else _FIRST_SUMMARY_SYSTEM
        content_text = "\n---\n".join(input.content[:20])  # 最多取 20 条

        if is_reflection:
            user_msg = (
                f"paragraph_title：{input.paragraph_title or '未指定'}\n"
                f"previous_summary：{input.existing_summary or '无'}\n"
                f"previous_key_points：{input.existing_key_points}\n"
                f"new_search_results：\n{content_text}"
            )
        else:
            user_msg = (
                f"paragraph_title：{input.paragraph_title or '未指定'}\n"
                f"search_results：\n{content_text}"
            )

        try:
            result = ctx.llm_client.invoke_structured(
                prompt=user_msg,
                system_prompt=system,
                output_model=SummarizeOutput,
            )
            if isinstance(result, SummarizeOutput):
                return self._normalize_output(result, input)
        except Exception as exc:
            logger.warning(f"[LLMSummarizeSkill] 结构化输出失败：{exc}，尝试普通调用")

        try:
            raw = ctx.llm_client.invoke(system_prompt=system, user_prompt=user_msg)
            return self._normalize_output(
                SummarizeOutput(
                    summary=raw or "总结生成失败",
                    confidence=0.5,
                    uncertainties=["LLM 未返回结构化字段，已降级为纯文本摘要"],
                ),
                input,
            )
        except Exception as exc2:
            logger.error(f"[LLMSummarizeSkill] 普通调用也失败：{exc2}")
            return self._fallback_output(input, reason=f"LLM 调用失败：{exc2}")

    def _normalize_output(
        self,
        output: SummarizeOutput,
        input: SummarizeInput | None = None,
    ) -> SummarizeOutput:
        """收紧 LLM 输出，避免 confidence 越界、列表污染或反思痕迹丢失。"""
        output.confidence = max(0.0, min(1.0, float(output.confidence)))
        output.key_points = self._normalize_list(output.key_points, limit=8)
        output.conflicts = self._normalize_list(output.conflicts, limit=6)
        output.uncertainties = self._normalize_list(output.uncertainties, limit=6)
        output.entities = self._normalize_list(output.entities, limit=8)
        output.retained_points = self._normalize_list(output.retained_points, limit=8)
        output.new_points = self._normalize_list(output.new_points, limit=8)
        output.revised_points = self._normalize_list(output.revised_points, limit=8)
        output.change_log = self._normalize_list(output.change_log, limit=8)
        if not output.key_points and output.summary:
            output.key_points = [output.summary[:160]]

        if input and input.mode == "reflection_summary":
            self._backfill_reflection_fields(output, input)
        return output

    def _fallback_output(self, input: SummarizeInput, reason: str) -> SummarizeOutput:
        """
        无 LLM 或 LLM 失败时的保守降级。

        只压缩输入片段，不补充外部事实；reflection 模式保留旧结论并列出新增片段。
        """
        facts = self._clean_content(input.content)
        if input.mode == "reflection_summary":
            retained = list(input.existing_key_points)
            new_points = [p for p in facts if p not in retained][:5]
            pieces = []
            if input.existing_summary:
                pieces.append(input.existing_summary.strip())
            if new_points:
                pieces.append("新增证据提示：" + "；".join(new_points[:3]))
            summary = "；".join(pieces) or "未获得足够新证据，无法修订旧摘要"
            return self._normalize_output(
                SummarizeOutput(
                    summary=summary,
                    key_points=(retained + new_points)[:8],
                    retained_points=retained,
                    new_points=new_points,
                    change_log=[reason],
                    confidence=0.35 if facts else 0.0,
                    uncertainties=[reason] if reason else [],
                ),
                input,
            )

        summary = "；".join(facts[:3]) if facts else "输入证据为空，无法生成摘要"
        return self._normalize_output(
            SummarizeOutput(
                summary=summary,
                key_points=facts[:8],
                confidence=0.35 if facts else 0.0,
                uncertainties=[reason] if reason else [],
            ),
            input,
        )

    @staticmethod
    def _clean_content(content: list[str]) -> list[str]:
        """将输入证据片段压缩成短事实候选，供降级路径使用。"""
        cleaned = []
        seen = set()
        for item in content:
            text = " ".join(str(item or "").split())
            if not text:
                continue
            text = text[:180]
            if text in seen:
                continue
            seen.add(text)
            cleaned.append(text)
            if len(cleaned) >= 10:
                break
        return cleaned

    @staticmethod
    def _normalize_list(items: list[str], limit: int) -> list[str]:
        normalized = []
        seen = set()
        for item in items:
            text = " ".join(str(item or "").split()).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            normalized.append(text[:220])
            if len(normalized) >= limit:
                break
        return normalized

    def _backfill_reflection_fields(self, output: SummarizeOutput, input: SummarizeInput) -> None:
        existing = self._normalize_list(list(input.existing_key_points), limit=8)
        current = self._normalize_list(list(output.key_points), limit=8)

        if not output.retained_points and existing:
            output.retained_points = [item for item in existing if item in current][:8]
        if not output.new_points and current:
            output.new_points = [item for item in current if item not in existing][:8]
        if not output.change_log and output.summary:
            output.change_log = ["反思摘要已生成，但变更痕迹由规范化阶段补齐"]
