# -*- coding: utf-8 -*-
"""EvidenceExtractSkill — 从原文提取结构化证据（借鉴 citation-verification 的严谨性）。"""

from __future__ import annotations

import re

from loguru import logger
from pydantic import BaseModel

from veyrafish_core.skill import Skill, SkillContext
from veyrafish_core.skills._models import (
    EvidenceGap,
    EvidenceExtractInput,
    EvidenceExtractOutput,
    ExtractedEvidence,
)

_SYSTEM_PROMPT = """你是一位信息提取专家，擅长从文本中提取结构化证据。

给定一段原文，请：
1. 提取 2-5 条关键证据声明（每条一句话，客观陈述）
2. 为每条证据标注情感倾向：positive / negative / neutral
3. 评估每条证据的可信度（0.0~1.0）
4. 发现原文中未覆盖的重要信息缺口

输出 JSON 格式：
{
  "evidences": [
    {
      "claim": "具体的证据声明",
      "supporting_text": "原文摘录",
      "confidence": 0.8,
      "sentiment": "positive",
      "source_url": "来源 URL（可选）",
      "source_title": "来源标题（可选）"
    }
  ],
  "gaps": ["缺口1", "缺口2"]
}"""


class EvidenceExtractSkill(Skill):
    """从搜索结果/总结中提取结构化证据，借鉴 citation-verification 的验证严谨性。"""

    name = "evidence_extract"
    description = "从原文内容中提取结构化证据声明，标注情感和置信度，并发现信息缺口"
    version = "0.1.0"
    tags = ["evidence", "extraction", "analysis", "citation"]
    input_schema = EvidenceExtractInput
    output_schema = EvidenceExtractOutput

    def execute(self, input: EvidenceExtractInput, ctx: SkillContext) -> EvidenceExtractOutput:
        if ctx.llm_client is None:
            return self._fallback_output(input, reason="LLM 不可用，使用启发式证据提取")

        user_msg = (
            f"来源：{input.source_title or input.source_url or '未知'}\n"
            f"{'论点：' + input.claim + chr(10) if input.claim else ''}"
            f"原文内容：\n{input.content[:3000]}"
        )

        try:
            result = ctx.llm_client.invoke_structured(
                prompt=user_msg,
                system_prompt=_SYSTEM_PROMPT,
                output_model=EvidenceExtractOutput,
            )
            if isinstance(result, EvidenceExtractOutput):
                return self._normalize_output(result, input)
        except Exception as exc:
            logger.warning(f"[EvidenceExtractSkill] 结构化提取失败：{exc}")

        return self._fallback_output(input, reason="结构化提取失败，使用启发式证据提取")

    def _normalize_output(
        self,
        output: EvidenceExtractOutput,
        input: EvidenceExtractInput,
    ) -> EvidenceExtractOutput:
        """补齐来源字段并限制 confidence，保证证据可追溯。"""
        normalized = []
        for evidence in output.evidences:
            evidence.confidence = max(0.0, min(1.0, float(evidence.confidence)))
            evidence.claim = " ".join(evidence.claim.split())[:200]
            if not evidence.source_url:
                evidence.source_url = input.source_url
            if not evidence.source_title:
                evidence.source_title = input.source_title
            if not evidence.supporting_text:
                evidence.supporting_text = input.content[:200]
            evidence.supporting_text = " ".join(evidence.supporting_text.split())[:240]
            evidence.sentiment = self._normalize_sentiment(evidence.sentiment)
            evidence.claim_relation = self._infer_claim_relation(evidence.claim, input.claim)
            evidence.tags = list(dict.fromkeys([
                *(evidence.tags or []),
                "source_bound" if (evidence.source_url or evidence.source_title) else "source_missing",
            ]))
            normalized.append(evidence)
        output.evidences = normalized
        output.gap_details = self._build_gap_details(input, normalized)
        existing_gap_text = self._normalize_gap_text(output.gaps)
        derived_gap_text = [gap.description for gap in output.gap_details]
        output.gaps = list(dict.fromkeys([*existing_gap_text, *derived_gap_text]))
        return output

    def on_error(self, error: Exception, input: BaseModel, ctx: SkillContext) -> EvidenceExtractOutput:
        return EvidenceExtractOutput(gaps=[f"证据提取失败：{error}"])

    def _fallback_output(self, input: EvidenceExtractInput, reason: str) -> EvidenceExtractOutput:
        evidences = []
        for sentence in self._split_sentences(input.content):
            evidence_claim = input.claim.strip() if input.claim and len(evidences) == 0 else sentence[:160]
            evidences.append(ExtractedEvidence(
                claim=evidence_claim,
                supporting_text=sentence[:240],
                source_url=input.source_url,
                source_title=input.source_title,
                confidence=0.45,
                claim_relation=self._infer_claim_relation(evidence_claim, input.claim),
                tags=["heuristic_fallback"],
            ))
            if len(evidences) >= 3:
                break

        output = EvidenceExtractOutput(evidences=evidences)
        normalized = self._normalize_output(output, input)
        if reason:
            normalized.gaps.append(reason)
        return normalized

    def _build_gap_details(
        self,
        input: EvidenceExtractInput,
        evidences: list[ExtractedEvidence],
    ) -> list[EvidenceGap]:
        gaps = []
        if not input.source_url and not input.source_title:
            gaps.append(EvidenceGap(
                gap_type="missing_source",
                description="当前输入缺少明确来源标识，证据可追溯性不足",
            ))
        if not re.search(r"20\d{2}[-/年]\d{1,2}([-/月]\d{1,2})?", input.content):
            gaps.append(EvidenceGap(
                gap_type="missing_time",
                description="原文中缺少明确时间锚点，难以判断证据时效性",
            ))
        if input.claim and not any(e.claim_relation == "supports_input_claim" for e in evidences):
            gaps.append(EvidenceGap(
                gap_type="claim_alignment",
                description="提取结果与输入 claim 的对齐度不足，仍需补充直接支撑证据",
            ))
        if len(evidences) <= 1:
            gaps.append(EvidenceGap(
                gap_type="missing_counter_evidence",
                description="当前仅提取到较少证据，缺少交叉来源或反向证据视角",
            ))
        if len(input.content.strip()) < 80:
            gaps.append(EvidenceGap(
                gap_type="missing_scope",
                description="原文范围较窄，可能无法覆盖 claim 的完整上下文",
            ))
        return gaps

    @staticmethod
    def _infer_claim_relation(evidence_claim: str, input_claim: str) -> str:
        if not input_claim:
            return "derived_fact"
        evidence_text = evidence_claim.lower()
        claim_text = input_claim.lower()
        if claim_text in evidence_text or evidence_text in claim_text:
            return "supports_input_claim"
        evidence_tokens = {token for token in re.split(r"\W+", evidence_text) if token}
        claim_tokens = {token for token in re.split(r"\W+", claim_text) if token}
        if claim_tokens and len(evidence_tokens & claim_tokens) >= max(1, len(claim_tokens) // 2):
            return "supports_input_claim"
        return "unclear"

    @staticmethod
    def _split_sentences(content: str) -> list[str]:
        parts = re.split(r"[。\n.!?；;]+", content)
        sentences = []
        for part in parts:
            text = " ".join(part.strip().split())
            if len(text) >= 12:
                sentences.append(text)
        if not sentences and content.strip():
            sentences.append(content.strip()[:180])
        return sentences

    @staticmethod
    def _normalize_sentiment(sentiment: str | None) -> str | None:
        if sentiment is None:
            return None
        normalized = str(sentiment).strip().lower()
        if normalized in {"positive", "negative", "neutral"}:
            return normalized
        return None

    @staticmethod
    def _normalize_gap_text(gaps: list[str]) -> list[str]:
        normalized = []
        seen = set()
        for gap in gaps:
            text = " ".join(str(gap or "").split()).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            normalized.append(text[:220])
        return normalized
