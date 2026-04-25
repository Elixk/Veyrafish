# -*- coding: utf-8 -*-
"""SentimentAnalysisSkill — 跨引擎情感分析（从 InsightEngine 泛化）。"""

from __future__ import annotations

from loguru import logger
from pydantic import BaseModel

from veyrafish_core.skill import Skill, SkillContext
from veyrafish_core.skills._models import (
    SentimentInput,
    SentimentOutput,
    SentimentResult,
)


class SentimentAnalysisSkill(Skill):
    """
    情感分析 Skill。

    优先使用 InsightEngine 的 WeiboMultilingualSentiment（如果可用），
    降级时使用 LLM 零样本情感判断。
    """

    name = "sentiment_analysis"
    description = "对文本列表进行情感分析（positive/negative/neutral），支持中英文及22种语言"
    version = "0.1.0"
    tags = ["sentiment", "analysis", "nlp"]
    input_schema = SentimentInput
    output_schema = SentimentOutput

    def execute(self, input: SentimentInput, ctx: SkillContext) -> SentimentOutput:
        if not input.texts:
            return SentimentOutput(results=[], overall_sentiment="neutral")

        # 尝试使用 InsightEngine 的专用情感分析器
        try:
            from InsightEngine.tools import multilingual_sentiment_analyzer  # type: ignore
            results = self._analyze_with_specialist(input.texts, multilingual_sentiment_analyzer)
            return self._make_output(results)
        except Exception:
            pass  # 降级到 LLM

        # LLM 零样本情感分析
        if ctx.llm_client:
            try:
                return self._analyze_with_llm(input, ctx)
            except Exception as exc:
                logger.warning(f"[SentimentAnalysisSkill] LLM 情感分析失败：{exc}")

        # 最终兜底：全部返回 neutral
        results = [
            SentimentResult(text=t, sentiment="neutral", score=0.0, confidence=0.3)
            for t in input.texts
        ]
        return self._make_output(results)

    def _analyze_with_specialist(self, texts, analyzer) -> list:
        results = []
        for text in texts:
            r = analyzer.analyze(text)
            results.append(SentimentResult(
                text=text,
                sentiment=self._normalize_sentiment(r.get("sentiment")),
                score=self._normalize_score(r.get("score", 0.0)),
                confidence=self._normalize_confidence(r.get("confidence", 0.7)),
            ))
        return results

    def _analyze_with_llm(self, input: SentimentInput, ctx: SkillContext) -> SentimentOutput:
        import json
        texts_formatted = "\n".join(f"{i+1}. {t[:200]}" for i, t in enumerate(input.texts))
        prompt = (
            f"请对以下 {len(input.texts)} 条文本进行情感分析。\n"
            f"语言：{input.language}\n\n"
            f"{texts_formatted}\n\n"
            f"以 JSON 数组返回，每项包含 text/sentiment/score/confidence 字段。"
        )
        raw = ctx.llm_client.invoke(prompt)
        try:
            data = json.loads(raw)
            results = [
                self._make_result_from_item(item, fallback_text)
                for item, fallback_text in zip(data, input.texts)
            ]
            if len(results) < len(input.texts):
                results.extend(
                    SentimentResult(
                        text=text,
                        sentiment="neutral",
                        score=0.0,
                        confidence=0.3,
                    )
                    for text in input.texts[len(results):]
                )
        except Exception:
            results = [
                SentimentResult(text=t, sentiment="neutral", score=0.0, confidence=0.3)
                for t in input.texts
            ]
        return self._make_output(results)

    @classmethod
    def _make_output(cls, results: list) -> SentimentOutput:
        if not results:
            return SentimentOutput(results=[], overall_sentiment="neutral")
        normalized_results = [
            SentimentResult(
                text=result.text,
                sentiment=cls._normalize_sentiment(result.sentiment),
                score=cls._normalize_score(result.score),
                confidence=cls._normalize_confidence(result.confidence),
            )
            for result in results
        ]
        scores = [r.score for r in normalized_results]
        avg = sum(scores) / len(scores)
        overall = cls._infer_overall_sentiment(avg)
        return SentimentOutput(results=normalized_results, overall_sentiment=overall)

    @classmethod
    def _make_result_from_item(cls, item, fallback_text: str) -> SentimentResult:
        text = str(item.get("text", "")).strip() if isinstance(item, dict) else ""
        return SentimentResult(
            text=text or fallback_text,
            sentiment=cls._normalize_sentiment(item.get("sentiment") if isinstance(item, dict) else None),
            score=cls._normalize_score(item.get("score", 0.0) if isinstance(item, dict) else 0.0),
            confidence=cls._normalize_confidence(
                item.get("confidence", 0.5) if isinstance(item, dict) else 0.5
            ),
        )

    @staticmethod
    def _normalize_sentiment(sentiment) -> str:
        normalized = str(sentiment or "").strip().lower()
        alias_map = {
            "positive": "positive",
            "pos": "positive",
            "正面": "positive",
            "积极": "positive",
            "negative": "negative",
            "neg": "negative",
            "负面": "negative",
            "消极": "negative",
            "neutral": "neutral",
            "neu": "neutral",
            "中性": "neutral",
        }
        return alias_map.get(normalized, "neutral")

    @staticmethod
    def _normalize_score(score) -> float:
        try:
            value = float(score)
        except Exception:
            value = 0.0
        return max(-1.0, min(1.0, value))

    @staticmethod
    def _normalize_confidence(confidence) -> float:
        try:
            value = float(confidence)
        except Exception:
            value = 0.5
        return max(0.0, min(1.0, value))

    @staticmethod
    def _infer_overall_sentiment(avg_score: float) -> str:
        return "positive" if avg_score > 0.1 else ("negative" if avg_score < -0.1 else "neutral")

    def on_error(self, error: Exception, input: BaseModel, ctx: SkillContext) -> SentimentOutput:
        return SentimentOutput(results=[], overall_sentiment="neutral", error=str(error))
