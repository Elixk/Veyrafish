# -*- coding: utf-8 -*-
"""GapFinderSkill — 证据缺口发现（借鉴 research-ideation 的 Gap Analysis）。"""

from __future__ import annotations

import re

from loguru import logger
from pydantic import BaseModel

from veyrafish_core.skill import Skill, SkillContext
from veyrafish_core.skills._models import GapFinderOutput, GapInput, ResearchGap

_SYSTEM_PROMPT = """你是一位专业的研究顾问，擅长发现信息缺口和矛盾。

给定多个研究引擎的当前总结和核心研究问题，请：
1. 识别 2-4 个重要的信息缺口（尚未被充分研究的方面）
2. 发现不同引擎/总结之间的矛盾或不一致点
3. 对每个缺口给出具体的补充检索建议

输出 JSON：
{
  "gaps": [
    {
      "description": "缺口描述",
      "suggested_query": "建议补充的检索词",
      "gap_type": "coverage/conflict/recency",
      "priority": "high/medium/low"
    }
  ],
  "conflict_notes": ["矛盾描述1", "矛盾描述2"],
  "overall_coverage": "当前证据覆盖度评估（一句话）"
}"""


class GapFinderSkill(Skill):
    """
    证据缺口发现 Skill，借鉴 research-ideation 的 Gap Analysis 思路。

    用于 ForumEngine 分析三引擎的当前研究状态，
    发现尚未覆盖的信息缺口并建议补充检索方向。
    """

    name = "gap_finder"
    description = "分析多引擎研究总结，发现信息缺口、矛盾点，并建议补充检索方向"
    version = "0.1.0"
    tags = ["analysis", "gap_analysis", "forum", "research"]
    input_schema = GapInput
    output_schema = GapFinderOutput

    def execute(self, input: GapInput, ctx: SkillContext) -> GapFinderOutput:
        if ctx.llm_client is None:
            return self._fallback(input, reason="LLM 不可用，使用启发式缺口分析")

        engine_labels = self._build_engine_labels(input)
        summaries_text = "\n\n".join(
            f"【{label}】\n{summary}"
            for label, summary in zip(engine_labels, input.summaries)
        )

        user_msg = (
            f"研究问题：{input.research_question}\n\n"
            f"当前各引擎总结：\n{summaries_text}"
        )

        try:
            result = ctx.llm_client.invoke_structured(
                prompt=user_msg,
                system_prompt=_SYSTEM_PROMPT,
                output_model=GapFinderOutput,
            )
            if isinstance(result, GapFinderOutput):
                return self._normalize_output(result, input)
        except Exception as exc:
            logger.warning(f"[GapFinderSkill] 结构化输出失败：{exc}")

        return self._fallback(input, reason="结构化分析失败，已使用启发式缺口分析")

    def on_error(self, error: Exception, input: BaseModel, ctx: SkillContext) -> GapFinderOutput:
        return GapFinderOutput(gaps=[], conflict_notes=[f"缺口分析失败：{error}"])

    def _normalize_output(self, output: GapFinderOutput, input: GapInput) -> GapFinderOutput:
        fallback = self._fallback(input, reason="启发式规则已补齐 gap_type")
        if not output.gaps:
            output.gaps = fallback.gaps
        for gap in output.gaps:
            gap.description = " ".join(str(gap.description or "").split()).strip()[:220]
            gap.suggested_query = " ".join(str(gap.suggested_query or "").split()).strip()[:180]
            gap.gap_type = self._normalize_gap_type(gap, fallback)
            gap.priority = self._normalize_priority(gap.priority, gap.gap_type)
        output.gaps = self._dedupe_gaps(output.gaps)
        if not output.overall_coverage:
            output.overall_coverage = fallback.overall_coverage
        merged_conflicts = [*output.conflict_notes, *fallback.conflict_notes]
        output.conflict_notes = self._normalize_notes(merged_conflicts)
        return output

    def _fallback(self, input: GapInput, reason: str) -> GapFinderOutput:
        gaps: list[ResearchGap] = []
        conflict_notes = self._detect_conflicts(input.summaries)

        if not input.summaries or any(len(summary.strip()) < 20 for summary in input.summaries):
            gaps.append(ResearchGap(
                description="现有总结覆盖度不足，仍有关键事实、主体或结论未被充分展开",
                suggested_query=f"{input.research_question} 核心事实 数据 官方来源",
                gap_type="coverage",
                priority="high",
            ))

        if conflict_notes:
            gaps.append(ResearchGap(
                description="不同引擎总结之间存在方向性冲突，需要补充权威来源核验",
                suggested_query=f"{input.research_question} 官方回应 权威数据 对比",
                gap_type="conflict",
                priority="high",
            ))

        if self._needs_recency_gap(input):
            gaps.append(ResearchGap(
                description="当前总结缺少明确的近期时间锚点，无法判断结论是否仍然有效",
                suggested_query=f"{input.research_question} 最新 近7天 近30天",
                gap_type="recency",
                priority="medium",
            ))

        if not gaps:
            gaps.append(ResearchGap(
                description="当前总结基本完整，但仍建议做一次补充检索确认边缘信息",
                suggested_query=f"{input.research_question} 补充信息 交叉验证",
                gap_type="coverage",
                priority="low",
            ))

        coverage = "覆盖度有限，建议优先补齐高优先级缺口"
        if len(gaps) == 1 and gaps[0].priority == "low":
            coverage = "覆盖度较好，仅存在低优先级补充空间"
        elif len(gaps) <= 2 and not conflict_notes:
            coverage = "覆盖度中等，仍需补充部分事实或时效信息"

        if reason:
            coverage = f"{coverage}（{reason}）"
        return GapFinderOutput(gaps=gaps, conflict_notes=conflict_notes, overall_coverage=coverage)

    def _needs_recency_gap(self, input: GapInput) -> bool:
        text = " ".join([input.research_question, *input.summaries])
        query_mentions_recency = any(token in input.research_question for token in ("最新", "近期", "最近", "本周", "本月"))
        has_date_anchor = bool(re.search(r"20\d{2}[-/年]\d{1,2}([-/月]\d{1,2})?", text))
        return query_mentions_recency and not has_date_anchor

    @staticmethod
    def _detect_conflicts(summaries: list[str]) -> list[str]:
        conflict_notes = []
        joined = "\n".join(summaries)
        opposite_pairs = [
            ("增长", "下降"),
            ("上涨", "下跌"),
            ("支持", "反对"),
            ("positive", "negative"),
        ]
        for positive, negative in opposite_pairs:
            if positive in joined and negative in joined:
                conflict_notes.append(f"检测到方向性冲突：同时出现“{positive}”与“{negative}”")
        return conflict_notes

    def _build_engine_labels(self, input: GapInput) -> list[str]:
        labels = [" ".join(str(name or "").split()).strip() for name in input.engine_names]
        normalized = [label for label in labels if label]
        while len(normalized) < len(input.summaries):
            normalized.append(f"引擎{len(normalized) + 1}")
        return normalized[: len(input.summaries)]

    def _normalize_gap_type(self, gap: ResearchGap, fallback: GapFinderOutput) -> str:
        if gap.gap_type in {"coverage", "conflict", "recency"}:
            return gap.gap_type
        text = " ".join([gap.description, gap.suggested_query]).lower()
        if any(token in text for token in ("冲突", "矛盾", "对立", "核验")):
            return "conflict"
        if any(token in text for token in ("最新", "近期", "最近", "本周", "本月", "近7天", "近30天")):
            return "recency"
        if fallback.gaps:
            return fallback.gaps[0].gap_type
        return "coverage"

    @staticmethod
    def _normalize_priority(priority: str, gap_type: str) -> str:
        normalized = str(priority or "").strip().lower()
        if normalized in {"high", "medium", "low"}:
            return normalized
        if gap_type == "conflict":
            return "high"
        if gap_type == "recency":
            return "medium"
        return "medium"

    @staticmethod
    def _dedupe_gaps(gaps: list[ResearchGap]) -> list[ResearchGap]:
        deduped_map: dict[tuple[str, str], ResearchGap] = {}
        priority_rank = {"high": 3, "medium": 2, "low": 1}
        for gap in gaps:
            key = (gap.description, gap.suggested_query)
            if not gap.description:
                continue
            existing = deduped_map.get(key)
            if existing is None:
                deduped_map[key] = gap
                continue

            if priority_rank.get(gap.priority, 0) > priority_rank.get(existing.priority, 0):
                deduped_map[key] = gap
                continue

            if (
                priority_rank.get(gap.priority, 0) == priority_rank.get(existing.priority, 0)
                and existing.gap_type != "conflict"
                and gap.gap_type == "conflict"
            ):
                deduped_map[key] = gap

        return list(deduped_map.values())

    @staticmethod
    def _normalize_notes(notes: list[str]) -> list[str]:
        normalized = []
        seen = set()
        for note in notes:
            text = " ".join(str(note or "").split()).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            normalized.append(text[:220])
        return normalized
