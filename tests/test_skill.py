# -*- coding: utf-8 -*-
"""
tests/test_skill.py — Wave 2 验证：Skill 基类 + SkillRegistry + 核心 Skill
"""

import pytest
from types import SimpleNamespace
from pydantic import BaseModel

from veyrafish_core.skill import Skill, SkillBudget, SkillContext
from veyrafish_core.skills._models import (
    QueryRewriteInput,
    QueryRewriteOutput,
    QualityGateInput,
    QualityGateOutput,
    WebSearchInput,
    WebSearchOutput,
    SummarizeInput,
    SummarizeOutput,
    EvidenceExtractInput,
    EvidenceExtractOutput,
    EvidenceGap,
    ExtractedEvidence,
    GapInput,
    ResearchGap,
    GapFinderOutput,
    SentimentInput,
    SentimentOutput,
    SentimentResult,
)
from veyrafish_core.skills._registry import SkillRegistry
from veyrafish_core.skills.query_rewrite import QueryRewriteSkill
from veyrafish_core.skills.quality_gate import QualityGateSkill
from veyrafish_core.skills.web_search import WebSearchSkill
from veyrafish_core.skills.llm_summarize import LLMSummarizeSkill
from veyrafish_core.skills.evidence_extract import EvidenceExtractSkill
from veyrafish_core.skills.gap_finder import GapFinderSkill
from veyrafish_core.skills.sentiment_analysis import SentimentAnalysisSkill


# ---------------------------------------------------------------------------
# 辅助：具体 Skill 实现（用于测试基类行为）
# ---------------------------------------------------------------------------

class _EchoInput(BaseModel):
    text: str


class _EchoOutput(BaseModel):
    echoed: str


class _EchoSkill(Skill):
    name = "echo"
    description = "原样返回输入文本"
    version = "0.1.0"
    tags = ["test", "utility"]
    input_schema = _EchoInput
    output_schema = _EchoOutput

    def execute(self, input: _EchoInput, ctx: SkillContext) -> _EchoOutput:
        return _EchoOutput(echoed=input.text)


class _FailSkill(Skill):
    name = "fail"
    description = "总是失败"
    tags = ["test"]
    input_schema = _EchoInput
    output_schema = _EchoOutput

    def execute(self, input: _EchoInput, ctx: SkillContext) -> _EchoOutput:
        raise RuntimeError("故意失败")


class _FailWithFallbackSkill(_FailSkill):
    name = "fail_with_fallback"

    def on_error(self, error: Exception, input: BaseModel, ctx: SkillContext) -> _EchoOutput:
        return _EchoOutput(echoed=f"降级：{error}")


# ---------------------------------------------------------------------------
# Skill 基类
# ---------------------------------------------------------------------------

class TestSkillBase:
    def test_to_metadata_contains_required_fields(self):
        skill = _EchoSkill()
        meta = skill.to_metadata()
        assert meta["name"] == "echo"
        assert meta["description"] == "原样返回输入文本"
        assert meta["version"] == "0.1.0"
        assert "test" in meta["tags"]
        assert "input_schema" in meta
        assert "output_schema" in meta

    def test_execute_returns_correct_output(self):
        skill = _EchoSkill()
        ctx = SkillContext()
        result = skill.execute(_EchoInput(text="hello"), ctx)
        assert isinstance(result, _EchoOutput)
        assert result.echoed == "hello"

    def test_validate_input_default_true(self):
        skill = _EchoSkill()
        assert skill.validate_input(_EchoInput(text="x")) is True

    def test_on_error_default_returns_none(self):
        skill = _EchoSkill()
        result = skill.on_error(RuntimeError("err"), _EchoInput(text="x"), SkillContext())
        assert result is None


class TestSkillContext:
    def test_default_fields(self):
        ctx = SkillContext()
        assert ctx.task_id is None
        assert ctx.llm_client is None
        assert ctx.budget is not None

    def test_with_task_id_returns_new_instance(self):
        ctx = SkillContext()
        ctx2 = ctx.with_task_id("tid-001")
        assert ctx2.task_id == "tid-001"
        assert ctx.task_id is None  # 原对象不变

    def test_budget_defaults(self):
        budget = SkillBudget()
        assert budget.max_tokens is None
        assert budget.max_retries == 3


# ---------------------------------------------------------------------------
# SkillRegistry
# ---------------------------------------------------------------------------

class TestSkillRegistry:
    def _make_registry(self) -> SkillRegistry:
        reg = SkillRegistry()
        reg.register(_EchoSkill())
        return reg

    def test_register_and_has(self):
        reg = self._make_registry()
        assert reg.has("echo")
        assert not reg.has("nonexistent")

    def test_get_returns_skill(self):
        reg = self._make_registry()
        skill = reg.get("echo")
        assert isinstance(skill, _EchoSkill)

    def test_get_missing_returns_none(self):
        reg = SkillRegistry()
        assert reg.get("ghost") is None

    def test_list_all(self):
        reg = self._make_registry()
        listing = reg.list()
        assert len(listing) == 1
        assert listing[0]["name"] == "echo"

    def test_list_by_tag(self):
        reg = SkillRegistry()
        reg.register(_EchoSkill())
        reg.register(_FailSkill())
        utility_skills = reg.list(tag="utility")
        assert len(utility_skills) == 1
        assert utility_skills[0]["name"] == "echo"

    def test_list_by_nonexistent_tag_returns_empty(self):
        reg = self._make_registry()
        assert reg.list(tag="nonexistent_tag") == []

    def test_names(self):
        reg = SkillRegistry()
        reg.register(_EchoSkill())
        reg.register(_FailSkill())
        assert set(reg.names()) == {"echo", "fail"}

    def test_duplicate_register_raises(self):
        reg = self._make_registry()
        with pytest.raises(ValueError, match="已注册"):
            reg.register(_EchoSkill())

    def test_register_or_replace(self):
        reg = self._make_registry()
        reg.register_or_replace(_EchoSkill())  # 不应抛出
        assert reg.has("echo")

    def test_unregister(self):
        reg = self._make_registry()
        assert reg.unregister("echo") is True
        assert not reg.has("echo")

    def test_unregister_nonexistent_returns_false(self):
        reg = SkillRegistry()
        assert reg.unregister("ghost") is False

    def test_len(self):
        reg = SkillRegistry()
        assert len(reg) == 0
        reg.register(_EchoSkill())
        assert len(reg) == 1

    def test_execute_via_registry(self):
        reg = self._make_registry()
        ctx = SkillContext()
        result = reg.execute("echo", _EchoInput(text="world"), ctx)
        assert isinstance(result, _EchoOutput)
        assert result.echoed == "world"

    def test_execute_missing_skill_raises(self):
        reg = SkillRegistry()
        with pytest.raises(KeyError, match="未注册"):
            reg.execute("ghost", _EchoInput(text="x"), SkillContext())

    def test_execute_with_fallback_on_error(self):
        reg = SkillRegistry()
        reg.register(_FailWithFallbackSkill())
        ctx = SkillContext()
        result = reg.execute("fail_with_fallback", _EchoInput(text="x"), ctx)
        assert isinstance(result, _EchoOutput)
        assert "降级" in result.echoed

    def test_execute_raises_when_no_fallback(self):
        reg = SkillRegistry()
        reg.register(_FailSkill())
        with pytest.raises(RuntimeError, match="故意失败"):
            reg.execute("fail", _EchoInput(text="x"), SkillContext())

    def test_register_empty_name_raises(self):
        class _NoName(Skill):
            name = ""
            description = "test"
            input_schema = _EchoInput
            output_schema = _EchoOutput

            def execute(self, input, ctx):
                return _EchoOutput(echoed="")

        reg = SkillRegistry()
        with pytest.raises(ValueError, match="name 不能为空"):
            reg.register(_NoName())


# ---------------------------------------------------------------------------
# Default Registry
# ---------------------------------------------------------------------------

class TestDefaultRegistry:
    def test_default_registry_has_all_builtin_skills(self):
        from veyrafish_core.skills import default_registry
        expected = {
            "web_search", "query_rewrite", "llm_summarize",
            "evidence_extract", "sentiment_analysis",
            "gap_finder", "quality_gate",
        }
        assert expected.issubset(set(default_registry.names()))

    def test_default_registry_list_returns_metadata(self):
        from veyrafish_core.skills import default_registry
        listing = default_registry.list()
        assert len(listing) >= 7
        names = {m["name"] for m in listing}
        assert "quality_gate" in names


# ---------------------------------------------------------------------------
# QueryRewriteSkill（启发式约束与工具选择）
# ---------------------------------------------------------------------------

class TestQueryRewriteSkill:
    def test_execute_without_llm_returns_constraints_and_selection_rule(self):
        skill = QueryRewriteSkill()
        result = skill.execute(
            QueryRewriteInput(
                original_query="最近一周微博上关于 Veyrafish 的讨论趋势",
                context="关注舆情热点变化",
                search_tools_available=["basic_search", "comprehensive_search", "search_topic_globally"],
            ),
            SkillContext(),
        )
        assert isinstance(result, QueryRewriteOutput)
        assert result.selection_rule
        assert result.search_tool in {"comprehensive_search", "search_topic_globally", "basic_search"}
        assert result.platform == "weibo"
        assert result.constraints
        assert result.time_period == "week"

    def test_normalize_replaces_unknown_tool_with_available_one(self):
        skill = QueryRewriteSkill()
        normalized = skill._normalize_output(
            QueryRewriteOutput(
                rewritten_query="x",
                search_tool="unknown_tool",
                reasoning="",
            ),
            QueryRewriteInput(
                original_query="最新新闻",
                search_tools_available=["basic_search", "comprehensive_search"],
            ),
        )
        assert normalized.search_tool in {"basic_search", "comprehensive_search"}
        assert normalized.selection_rule

    def test_normalize_derives_constraints_from_final_fields(self):
        skill = QueryRewriteSkill()
        normalized = skill._normalize_output(
            QueryRewriteOutput(
                rewritten_query="Veyrafish 微博 舆情",
                search_tool="basic_search",
                reasoning="使用微博平台约束",
                platform="weibo",
                start_date="2026-04-01",
                end_date="2026-04-07",
                time_period="week",
                constraints=[],
            ),
            QueryRewriteInput(
                original_query="Veyrafish 舆情",
                search_tools_available=["basic_search"],
            ),
        )
        assert "platform=weibo" in normalized.constraints
        assert "date_range=2026-04-01..2026-04-07" in normalized.constraints
        assert "time_period=week" in normalized.constraints


# ---------------------------------------------------------------------------
# QualityGateSkill（无需 LLM 的纯规则检查）
# ---------------------------------------------------------------------------

class TestQualityGateSkill:
    def _skill(self) -> QualityGateSkill:
        return QualityGateSkill()

    def _ctx(self) -> SkillContext:
        return SkillContext()  # 不传 llm_client，纯规则模式

    def test_pass_normal_content(self):
        result = self._skill().execute(
            QualityGateInput(content="这是一段足够长的正常内容，包含有意义的信息。" * 3, min_length=50),
            self._ctx(),
        )
        assert isinstance(result, QualityGateOutput)
        assert result.passed is True
        assert result.score > 0.5

    def test_fail_empty_content(self):
        result = self._skill().execute(
            QualityGateInput(content="", min_length=10),
            self._ctx(),
        )
        assert result.passed is False
        issue_types = [i.issue_type for i in result.issues]
        assert "empty" in issue_types

    def test_fail_too_short(self):
        result = self._skill().execute(
            QualityGateInput(content="短", min_length=100),
            self._ctx(),
        )
        issue_types = [i.issue_type for i in result.issues]
        assert "too_short" in issue_types

    def test_on_error_returns_failed_output(self):
        result = self._skill().on_error(RuntimeError("test"), QualityGateInput(content="x"), self._ctx())
        assert result.passed is False
        assert result.score == 0.0

    def test_score_clamped_between_0_and_1(self):
        result = self._skill().execute(
            QualityGateInput(content="x" * 200, min_length=50),
            self._ctx(),
        )
        assert 0.0 <= result.score <= 1.0

    def test_report_section_requires_support_signal(self):
        result = self._skill().execute(
            QualityGateInput(content="这是一个较长章节，但是只有泛泛表述，没有任何可核验的材料，也没有具体数字或可追溯线索。" * 5, content_type="report_section"),
            self._ctx(),
        )
        issue_types = [i.issue_type for i in result.issues]
        assert result.content_type_used == "report_section"
        assert result.criteria_used
        assert "weak_support" in issue_types

    def test_unknown_content_type_falls_back_to_summary_profile(self):
        result = self._skill().execute(
            QualityGateInput(
                content="这是一段长度刚过默认值但达不到摘要要求的内容，用来验证未知类型是否真的回退到 summary profile。",
                content_type="unknown_type",
            ),
            self._ctx(),
        )
        issue_types = [i.issue_type for i in result.issues]
        assert result.content_type_used == "summary"
        assert "too_short" in issue_types
        assert any("摘要最小要求" in criteria for criteria in result.criteria_used)


# ---------------------------------------------------------------------------
# WebSearchSkill（mock provider，验证降级）
# ---------------------------------------------------------------------------

class TestWebSearchSkill:
    def test_on_error_returns_empty_output(self):
        skill = WebSearchSkill()
        result = skill.on_error(RuntimeError("网络错误"), WebSearchInput(query="test"), SkillContext())
        assert isinstance(result, WebSearchOutput)
        assert result.results == []
        assert result.error is not None

    def test_execute_without_config_returns_clear_provider_error(self):
        skill = WebSearchSkill()
        ctx = SkillContext()  # 无 config，HTTP 调用会失败
        result = skill.execute(WebSearchInput(query="Veyrafish"), ctx)
        assert isinstance(result, WebSearchOutput)
        assert result.provider_used == "anspire"
        assert "ANSPIRE_API_KEY" in (result.error or "")

    def test_resolve_provider_normalizes_aliases_from_input_and_config(self):
        skill = WebSearchSkill()
        assert skill._resolve_provider(
            WebSearchInput(query="Veyrafish", provider="BochaAI"),
            SkillContext(),
        ) == "bocha"
        assert skill._resolve_provider(
            WebSearchInput(query="Veyrafish"),
            SkillContext(config=SimpleNamespace(SEARCH_TOOL_TYPE="TavilySearch")),
        ) == "tavily"

    def test_execute_normalizes_and_dedupes_results(self):
        skill = WebSearchSkill()

        def fake_search(provider, input, ctx):
            assert provider == "anspire"
            return [
                skill._make_result("", " https://example.com/a ", " First ", 1.2),
                skill._make_result("Example A", "https://example.com/a", "Duplicate", 0.4),
                skill._make_result(" ", " ", " ", -1),
                skill._make_result("", "https://example.com/b", "", "bad"),
            ]

        skill._search = fake_search  # type: ignore[method-assign]
        result = skill.execute(
            WebSearchInput(query="Veyrafish", max_results=5),
            SkillContext(config=SimpleNamespace(ANSPIRE_API_KEY="token")),
        )
        assert result.error is None
        assert result.total_found == 2
        assert result.results[0].title == "example.com"
        assert result.results[0].score == 1.0
        assert result.results[1].score == 0.0

    def test_execute_with_unknown_provider_returns_structured_error(self):
        skill = WebSearchSkill()
        result = skill.execute(
            WebSearchInput(query="Veyrafish", provider="unknown-provider"),
            SkillContext(config=SimpleNamespace(ANSPIRE_API_KEY="token")),
        )
        assert result.results == []
        assert result.provider_used == "unknownprovider"
        assert "未知 Provider" in (result.error or "")


# ---------------------------------------------------------------------------
# GapFinderSkill（无 LLM 降级路径）
# ---------------------------------------------------------------------------

class TestGapFinderSkill:
    def test_execute_without_llm_returns_fallback(self):
        skill = GapFinderSkill()
        result = skill.execute(
            GapInput(summaries=["摘要1", "摘要2"], research_question="测试问题"),
            SkillContext(),
        )
        assert isinstance(result, GapFinderOutput)
        assert "不可用" in result.overall_coverage or len(result.gaps) >= 0
        assert result.gaps
        assert result.gaps[0].gap_type in {"coverage", "conflict", "recency"}

    def test_on_error_returns_empty_gaps(self):
        skill = GapFinderSkill()
        result = skill.on_error(RuntimeError("err"), GapInput(summaries=[], research_question=""), SkillContext())
        assert isinstance(result, GapFinderOutput)

    def test_recency_gap_detected_when_question_requires_latest_info(self):
        skill = GapFinderSkill()
        result = skill.execute(
            GapInput(
                summaries=["该产品口碑整体较好，但未说明近期变化"],
                research_question="该产品最新一周的舆情变化是什么？",
            ),
            SkillContext(),
        )
        gap_types = [gap.gap_type for gap in result.gaps]
        assert "recency" in gap_types

    def test_normalize_infers_gap_type_priority_and_dedupes(self):
        skill = GapFinderSkill()
        result = skill._normalize_output(
            GapFinderOutput(
                gaps=[
                    ResearchGap.model_construct(
                        description="不同来源结论存在冲突，需要补充核验",
                        suggested_query="权威来源 核验",
                        gap_type="",
                        priority="",
                    ),
                    ResearchGap(
                        description="不同来源结论存在冲突，需要补充核验",
                        suggested_query="权威来源 核验",
                        gap_type="coverage",
                        priority="low",
                    ),
                ],
                conflict_notes=["  检测到冲突  ", "检测到冲突"],
                overall_coverage="",
            ),
            GapInput(
                summaries=["来源A显示增长", "来源B显示下降"],
                research_question="测试问题",
            ),
        )
        assert len(result.gaps) == 1
        assert result.gaps[0].gap_type == "conflict"
        assert result.gaps[0].priority == "high"
        assert result.conflict_notes == ["检测到冲突", "检测到方向性冲突：同时出现“增长”与“下降”"]

    def test_fallback_puts_reason_in_coverage_not_conflict_notes(self):
        skill = GapFinderSkill()
        result = skill._fallback(
            GapInput(summaries=["过短"], research_question="测试问题"),
            reason="LLM 不可用，使用启发式缺口分析",
        )
        assert "LLM 不可用" in result.overall_coverage
        assert all("LLM 不可用" not in note for note in result.conflict_notes)

    def test_build_engine_labels_fills_missing_names(self):
        skill = GapFinderSkill()
        labels = skill._build_engine_labels(
            GapInput(
                summaries=["摘要1", "摘要2", "摘要3"],
                research_question="测试问题",
                engine_names=["Insight"],
            )
        )
        assert labels == ["Insight", "引擎2", "引擎3"]


# ---------------------------------------------------------------------------
# SentimentAnalysisSkill（增强型规范化与降级）
# ---------------------------------------------------------------------------

class TestSentimentAnalysisSkill:
    def _skill(self) -> SentimentAnalysisSkill:
        return SentimentAnalysisSkill()

    def test_execute_without_texts_returns_neutral_empty_output(self):
        result = self._skill().execute(SentimentInput(texts=[]), SkillContext())
        assert isinstance(result, SentimentOutput)
        assert result.results == []
        assert result.overall_sentiment == "neutral"

    def test_make_output_normalizes_aliases_and_bounds(self):
        result = self._skill()._make_output(
            [
                SentimentResult(text="a", sentiment="正面", score=3.0, confidence=1.5),
                SentimentResult(text="b", sentiment="NEG", score=-2.0, confidence=-1.0),
            ]
        )
        assert result.results[0].sentiment == "positive"
        assert result.results[0].score == 1.0
        assert result.results[0].confidence == 1.0
        assert result.results[1].sentiment == "negative"
        assert result.results[1].score == -1.0
        assert result.results[1].confidence == 0.0

    def test_make_result_from_item_uses_fallback_text_and_normalizes(self):
        result = self._skill()._make_result_from_item(
            {
                "text": "",
                "sentiment": "中性",
                "score": "0.25",
                "confidence": "0.8",
            },
            "fallback text",
        )
        assert result.text == "fallback text"
        assert result.sentiment == "neutral"
        assert result.score == 0.25
        assert result.confidence == 0.8

    def test_on_error_returns_structured_failure(self):
        result = self._skill().on_error(RuntimeError("oops"), SentimentInput(texts=["x"]), SkillContext())
        assert result.overall_sentiment == "neutral"
        assert result.error == "oops"


# ---------------------------------------------------------------------------
# LLMSummarizeSkill（无 LLM 降级路径）
# ---------------------------------------------------------------------------

class TestLLMSummarizeSkill:
    def test_execute_without_llm_returns_conservative_fallback(self):
        skill = LLMSummarizeSkill()
        result = skill.execute(
            SummarizeInput(content=["搜索结果1", "搜索结果2"], paragraph_title="测试"),
            SkillContext(),
        )
        assert isinstance(result, SummarizeOutput)
        assert result.confidence > 0.0
        assert result.key_points == ["搜索结果1", "搜索结果2"]
        assert "LLM 客户端不可用" in result.uncertainties[0]

    def test_invalid_mode_rejected_by_schema(self):
        with pytest.raises(Exception):
            SummarizeInput(content=["x"], mode="free_write")

    def test_confidence_bounds_enforced_by_schema(self):
        with pytest.raises(Exception):
            SummarizeOutput(summary="x", confidence=1.2)

    def test_reflection_without_llm_preserves_delta_contract(self):
        skill = LLMSummarizeSkill()
        result = skill.execute(
            SummarizeInput(
                content=["新增证据A"],
                paragraph_title="测试",
                existing_summary="旧摘要",
                existing_key_points=["旧结论"],
                mode="reflection_summary",
            ),
            SkillContext(),
        )
        assert result.retained_points == ["旧结论"]
        assert result.new_points == ["新增证据A"]
        assert result.change_log

    def test_first_summary_output_supports_evidence_contract_fields(self):
        result = SummarizeOutput(
            summary="A 事件在输入证据中被多次提及",
            key_points=["A 事件发生"],
            conflicts=["来源1与来源2对时间表述不同"],
            uncertainties=["缺少官方确认"],
            entities=["A"],
            confidence=0.8,
        )
        assert result.conflicts
        assert result.uncertainties
        assert result.entities == ["A"]

    def test_reflection_summary_output_supports_delta_fields(self):
        result = SummarizeOutput(
            summary="旧结论被新证据部分修订",
            retained_points=["旧结论1仍成立"],
            new_points=["新增事实1"],
            revised_points=["旧结论2 -> 修订后结论2"],
            change_log=["因为新证据X，所以修订旧结论2"],
            confidence=0.7,
        )
        assert result.retained_points
        assert result.new_points
        assert result.revised_points
        assert result.change_log

    def test_normalize_clamps_confidence_and_backfills_key_points(self):
        skill = LLMSummarizeSkill()
        result = skill._normalize_output(
            SummarizeOutput.model_construct(summary="只有摘要", confidence=1.5, key_points=[])
        )
        assert result.confidence == 1.0
        assert result.key_points == ["只有摘要"]

    def test_reflection_normalize_backfills_delta_fields_and_dedupes_lists(self):
        skill = LLMSummarizeSkill()
        result = skill._normalize_output(
            SummarizeOutput(
                summary="根据新增证据，旧结论部分保留并新增信息",
                key_points=["旧结论", "新增事实", "新增事实"],
                confidence=0.7,
                change_log=[],
            ),
            SummarizeInput(
                content=["新增事实"],
                existing_key_points=["旧结论"],
                mode="reflection_summary",
            ),
        )
        assert result.retained_points == ["旧结论"]
        assert result.new_points == ["新增事实"]
        assert result.change_log


# ---------------------------------------------------------------------------
# EvidenceExtractSkill（来源追溯契约）
# ---------------------------------------------------------------------------

class TestEvidenceExtractSkill:
    def test_extract_evidence_confidence_bounds(self):
        with pytest.raises(Exception):
            ExtractedEvidence(claim="声明", confidence=-0.1)

    def test_normalize_backfills_source_fields(self):
        skill = EvidenceExtractSkill()
        output = EvidenceExtractOutput(
            evidences=[ExtractedEvidence(claim="声明", confidence=0.8)]
        )
        normalized = skill._normalize_output(
            output,
            EvidenceExtractInput(
                content="原文",
                source_url="https://example.com/a",
                source_title="来源A",
            ),
        )
        evidence = normalized.evidences[0]
        assert evidence.source_url == "https://example.com/a"
        assert evidence.source_title == "来源A"
        assert evidence.claim_relation == "derived_fact"
        assert normalized.gap_details

    def test_execute_without_llm_returns_heuristic_evidence_and_gap_details(self):
        skill = EvidenceExtractSkill()
        result = skill.execute(
            EvidenceExtractInput(
                content="Veyrafish 在 2026-04-20 发布了新版本，但是官方尚未披露完整数据。",
                claim="Veyrafish 发布了新版本",
            ),
            SkillContext(),
        )
        assert result.evidences
        assert result.evidences[0].source_url == ""
        assert result.evidences[0].claim_relation in {"supports_input_claim", "unclear", "derived_fact"}
        assert result.gap_details
        assert isinstance(result.gap_details[0], EvidenceGap)

    def test_normalize_preserves_llm_gaps_and_normalizes_fields(self):
        skill = EvidenceExtractSkill()
        result = skill._normalize_output(
            EvidenceExtractOutput(
                evidences=[
                    ExtractedEvidence.model_construct(
                        claim="  版本 发布  ",
                        supporting_text="  官方 提到 版本 发布，但 未给出 完整 数据。  ",
                        confidence=1.5,
                        sentiment="POSITIVE",
                        source_url="",
                        source_title="",
                        claim_relation="derived_fact",
                        tags=[],
                    )
                ],
                gaps=["LLM 提示缺少反向证据", "LLM 提示缺少反向证据"],
            ),
            EvidenceExtractInput(
                content="官方提到版本发布，但未给出完整数据。",
                source_title="官方说明",
            ),
        )
        evidence = result.evidences[0]
        assert evidence.confidence == 1.0
        assert evidence.sentiment == "positive"
        assert evidence.source_title == "官方说明"
        assert "LLM 提示缺少反向证据" in result.gaps

    def test_fallback_uses_first_claim_for_claim_relation(self):
        skill = EvidenceExtractSkill()
        result = skill.execute(
            EvidenceExtractInput(
                content="Veyrafish 发布新版本，但官方尚未披露完整数据。",
                claim="Veyrafish 发布新版本",
            ),
            SkillContext(),
        )
        assert result.evidences
        assert result.evidences[0].claim == "Veyrafish 发布新版本"
        assert result.evidences[0].claim_relation == "supports_input_claim"
