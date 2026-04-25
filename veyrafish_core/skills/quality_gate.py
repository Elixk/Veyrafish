# -*- coding: utf-8 -*-
"""QualityGateSkill — 通用输出质量检查（借鉴 verification-loop 的质量门禁思路）。"""

from __future__ import annotations

from loguru import logger
from pydantic import BaseModel

from veyrafish_core.skill import Skill, SkillContext
from veyrafish_core.skills._models import QualityGateInput, QualityGateOutput, QualityIssue

_DEFAULT_PROFILE = {
    "min_length": 50,
    "criteria": [
        "内容不为空",
        "长度达到最小要求",
        "不含明显幻觉或无意义重复",
    ],
}

_QUALITY_PROFILES = {
    "summary": {
        "min_length": 80,
        "criteria": [
            "内容不为空",
            "长度达到摘要最小要求",
            "保留关键事实或不确定性",
            "不含明显重复",
        ],
    },
    "report_section": {
        "min_length": 180,
        "criteria": [
            "章节内容完整",
            "表达具有结构性",
            "包含来源、证据或数据支撑信号",
            "不含明显重复",
        ],
    },
    "evidence": {
        "min_length": 30,
        "criteria": [
            "证据内容不为空",
            "能定位来源或支撑文本",
            "表达尽量客观",
        ],
    },
}


class QualityGateSkill(Skill):
    """
    内容质量检查 Skill，借鉴 verification-loop 的"验证前不声明完成"原则。

    支持规则检查（快速）+ LLM 评估（深度）双模式。
    """

    name = "quality_gate"
    description = "对 LLM 生成内容进行质量检查，识别内容过短/空/幻觉风险等问题"
    version = "0.1.0"
    tags = ["quality", "verification", "gate"]
    input_schema = QualityGateInput
    output_schema = QualityGateOutput

    def execute(self, input: QualityGateInput, ctx: SkillContext) -> QualityGateOutput:
        issues = []
        score = 1.0
        content_type_used, profile = self._resolve_profile(input.content_type)
        criteria_used = input.criteria or profile["criteria"]
        min_length = max(input.min_length, profile["min_length"])
        content = input.content or ""

        # ---- 规则检查（无需 LLM） ----
        if not content.strip():
            issues.append(QualityIssue(
                issue_type="empty",
                description="内容为空",
                severity="error",
            ))
            score -= 0.5

        if len(content) < min_length:
            issues.append(QualityIssue(
                issue_type="too_short",
                description=f"内容长度 {len(content)} 字符，低于最小要求 {min_length}",
                severity="warning",
            ))
            score -= 0.2

        head = content[:10]
        if head and content.count(head) > 3 and len(content) > 30:
            issues.append(QualityIssue(
                issue_type="repetition",
                description="检测到内容重复，可能存在循环生成",
                severity="warning",
            ))
            score -= 0.15

        if content_type_used in {"report_section", "evidence"} and not self._has_support_signal(content):
            issues.append(QualityIssue(
                issue_type="weak_support",
                description="缺少明确的来源、证据或数据支撑信号",
                severity="warning",
            ))
            score -= 0.15

        if content_type_used == "summary" and not self._has_summary_signal(content):
            issues.append(QualityIssue(
                issue_type="missing_summary_focus",
                description="摘要缺少关键结论、冲突或不确定性表达，信息密度偏低",
                severity="info",
            ))
            score -= 0.05

        # ---- LLM 深度评估（可选，不阻塞） ----
        if ctx.llm_client and len(content) > 100:
            try:
                score = self._llm_score(input, ctx, score)
            except Exception as exc:
                logger.debug(f"[QualityGateSkill] LLM 评估失败，跳过：{exc}")

        score = max(0.0, min(1.0, score))
        passed = score >= 0.5 and not any(i.severity == "error" for i in issues)

        suggestions = []
        if score < 0.6:
            suggestions.append("建议重新生成或补充更多信息")
        if any(i.issue_type == "too_short" for i in issues):
            suggestions.append("建议增加搜索结果数量或扩大搜索范围")
        if any(i.issue_type == "weak_support" for i in issues):
            suggestions.append("建议补充来源、引用或支撑文本")
        if any(i.issue_type == "missing_summary_focus" for i in issues):
            suggestions.append("建议明确关键结论、冲突点或不确定性")

        return QualityGateOutput(
            passed=passed,
            score=round(score, 3),
            content_type_used=content_type_used,
            criteria_used=criteria_used,
            issues=issues,
            suggestions=suggestions,
        )

    def _resolve_profile(self, content_type: str) -> tuple[str, dict]:
        if content_type in _QUALITY_PROFILES:
            return content_type, _QUALITY_PROFILES[content_type]
        return "summary", _QUALITY_PROFILES.get("summary", _DEFAULT_PROFILE)

    @staticmethod
    def _has_support_signal(content: str) -> bool:
        support_markers = ("http", "来源", "证据", "数据", "根据", "报道", "引用")
        return any(marker in content for marker in support_markers)

    @staticmethod
    def _has_summary_signal(content: str) -> bool:
        summary_markers = ("结论", "显示", "表明", "冲突", "不确定", "风险", "主要")
        return any(marker in content for marker in summary_markers)

    def _llm_score(self, input: QualityGateInput, ctx: SkillContext, base_score: float) -> float:
        """使用 LLM 对内容质量做 0~1 评分。"""
        prompt = (
            f"请评估以下{input.content_type}内容的质量，给出 0.0~1.0 的评分（只输出数字）。\n\n"
            f"内容：\n{input.content[:1000]}"
        )
        raw = ctx.llm_client.invoke(prompt)
        try:
            return float(raw.strip().split()[0])
        except Exception:
            return base_score

    def on_error(self, error: Exception, input: BaseModel, ctx: SkillContext) -> QualityGateOutput:
        return QualityGateOutput(
            passed=False,
            score=0.0,
            issues=[QualityIssue(issue_type="check_failed", description=str(error), severity="error")],
        )
