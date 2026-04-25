# -*- coding: utf-8 -*-
"""
veyrafish_core.skills._models — 所有 Skill 共用的 Pydantic I/O 模型

每个 Skill 的 input_schema / output_schema 都定义在此处，
统一管理，避免散落在各 Skill 文件中。
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# WebSearchSkill
# ---------------------------------------------------------------------------

class WebSearchInput(BaseModel):
    query: str = Field(..., description="搜索关键词")
    provider: Optional[str] = Field(None, description="指定搜索 Provider：anspire / bocha / tavily；为 None 时自动选择")
    max_results: int = Field(10, description="最大返回结果数")
    start_date: Optional[str] = Field(None, description="起始日期，格式 YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="截止日期，格式 YYYY-MM-DD")


class SearchResult(BaseModel):
    title: str = Field("", description="结果标题")
    url: str = Field("", description="来源 URL")
    content: str = Field("", description="正文摘要")
    score: float = Field(0.0, description="相关性得分 0~1")


class WebSearchOutput(BaseModel):
    results: List[SearchResult] = Field(default_factory=list)
    provider_used: str = Field("", description="实际使用的 Provider")
    total_found: int = Field(0, description="命中总数")
    error: Optional[str] = Field(None, description="如有异常，记录错误信息")


# ---------------------------------------------------------------------------
# QueryRewriteSkill
# ---------------------------------------------------------------------------

class QueryRewriteInput(BaseModel):
    original_query: str = Field(..., description="原始搜索查询")
    context: str = Field("", description="段落标题/研究背景，帮助 LLM 理解意图")
    search_tools_available: List[str] = Field(
        default_factory=list,
        description="可用搜索工具名称列表"
    )


class QueryRewriteOutput(BaseModel):
    rewritten_query: str = Field(..., description="优化后的搜索查询词")
    search_tool: str = Field(..., description="推荐使用的搜索工具名称")
    reasoning: str = Field("", description="工具选择和查询改写的推理说明")
    selection_rule: str = Field("", description="触发的工具选择规则或回退规则")
    constraints: List[str] = Field(default_factory=list, description="实际应用的日期、平台、时效约束说明")
    start_date: Optional[str] = Field(None)
    end_date: Optional[str] = Field(None)
    platform: Optional[str] = Field(None)
    time_period: Optional[str] = Field(None)


# ---------------------------------------------------------------------------
# LLMSummarizeSkill
# ---------------------------------------------------------------------------

class SummarizeInput(BaseModel):
    content: List[str] = Field(..., min_length=1, description="待总结的文本片段列表")
    paragraph_title: str = Field("", description="当前段落标题，引导总结方向")
    existing_summary: str = Field("", description="已有总结，用于反思更新；首次总结时为空")
    existing_key_points: List[str] = Field(
        default_factory=list,
        description="已有关键点，用于 reflection_summary 判断保留/新增/修订",
    )
    mode: Literal["first_summary", "reflection_summary"] = Field(
        "first_summary",
        description="first_summary / reflection_summary",
    )


class SummarizeOutput(BaseModel):
    summary: str = Field(..., description="总结内容")
    key_points: List[str] = Field(default_factory=list, description="关键要点列表")
    confidence: float = Field(0.7, ge=0.0, le=1.0, description="总结置信度 0~1")
    conflicts: List[str] = Field(default_factory=list, description="证据之间或新旧结论之间的冲突点")
    uncertainties: List[str] = Field(default_factory=list, description="证据不足、来源缺失或仍待确认的信息")
    entities: List[str] = Field(default_factory=list, description="摘要中涉及的关键主体")
    retained_points: List[str] = Field(default_factory=list, description="反思更新后仍成立的旧关键点")
    new_points: List[str] = Field(default_factory=list, description="反思更新中新加入的事实或观点")
    revised_points: List[str] = Field(default_factory=list, description="被新证据修订的旧结论")
    change_log: List[str] = Field(default_factory=list, description="反思更新的变更原因记录")


# ---------------------------------------------------------------------------
# EvidenceExtractSkill
# ---------------------------------------------------------------------------

class EvidenceExtractInput(BaseModel):
    content: str = Field(..., description="待提取证据的原文内容")
    claim: str = Field("", description="需要支撑的论点（为空时自动提取）")
    source_url: str = Field("", description="来源 URL")
    source_title: str = Field("", description="来源标题")


class ExtractedEvidence(BaseModel):
    claim: str = Field(..., description="证据声明（一句话）")
    supporting_text: str = Field("", description="支撑文本摘录")
    source_url: str = Field("", description="来源 URL")
    source_title: str = Field("", description="来源标题")
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="置信度 0~1")
    sentiment: Optional[str] = Field(None, description="情感倾向：positive / negative / neutral")
    claim_relation: Literal["supports_input_claim", "derived_fact", "unclear"] = Field(
        "derived_fact",
        description="该证据与输入 claim 的关系",
    )
    tags: List[str] = Field(default_factory=list, description="证据标签")


class EvidenceGap(BaseModel):
    gap_type: Literal[
        "missing_source",
        "missing_time",
        "missing_counter_evidence",
        "missing_scope",
        "claim_alignment",
    ] = Field(..., description="证据缺口类型")
    description: str = Field(..., description="缺口说明")


class EvidenceExtractOutput(BaseModel):
    evidences: List[ExtractedEvidence] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list, description="发现的证据缺口列表")
    gap_details: List[EvidenceGap] = Field(default_factory=list, description="带分类的证据缺口")


# ---------------------------------------------------------------------------
# SentimentAnalysisSkill
# ---------------------------------------------------------------------------

class SentimentInput(BaseModel):
    texts: List[str] = Field(..., description="待分析的文本列表")
    language: str = Field("zh", description="文本语言代码，如 zh / en")


class SentimentResult(BaseModel):
    text: str = Field(..., description="原文本")
    sentiment: str = Field(..., description="positive / negative / neutral")
    score: float = Field(0.0, description="情感得分（正数=正面，负数=负面）")
    confidence: float = Field(0.5, description="置信度 0~1")


class SentimentOutput(BaseModel):
    results: List[SentimentResult] = Field(default_factory=list)
    overall_sentiment: str = Field("neutral", description="整体情感倾向")
    error: Optional[str] = Field(None)


# ---------------------------------------------------------------------------
# GapFinderSkill
# ---------------------------------------------------------------------------

class GapInput(BaseModel):
    summaries: List[str] = Field(..., description="各段落/引擎的当前总结列表")
    research_question: str = Field(..., description="研究主题或核心问题")
    engine_names: List[str] = Field(default_factory=list, description="各总结对应的引擎名称")


class ResearchGap(BaseModel):
    description: str = Field(..., description="缺口描述")
    suggested_query: str = Field("", description="建议补充检索的查询词")
    gap_type: Literal["coverage", "conflict", "recency"] = Field(
        "coverage",
        description="缺口类型：coverage / conflict / recency",
    )
    priority: str = Field("medium", description="优先级：high / medium / low")


class GapFinderOutput(BaseModel):
    gaps: List[ResearchGap] = Field(default_factory=list)
    conflict_notes: List[str] = Field(default_factory=list, description="引擎间的矛盾/不一致点")
    overall_coverage: str = Field("", description="当前证据覆盖度评估")


# ---------------------------------------------------------------------------
# QualityGateSkill
# ---------------------------------------------------------------------------

class QualityGateInput(BaseModel):
    content: str = Field(..., description="待检查的内容")
    content_type: str = Field("summary", description="内容类型：summary / report_section / evidence")
    criteria: List[str] = Field(
        default_factory=list,
        description="检查标准列表（为空时使用默认标准）"
    )
    min_length: int = Field(50, description="最小字符长度")


class QualityIssue(BaseModel):
    issue_type: str = Field(
        ...,
        description=(
            "问题类型，如 too_short / empty / repetition / weak_support / "
            "missing_summary_focus / check_failed"
        ),
    )
    description: str = Field(..., description="问题描述")
    severity: str = Field("warning", description="严重程度：error / warning / info")


class QualityGateOutput(BaseModel):
    passed: bool = Field(..., description="是否通过质量检查")
    score: float = Field(0.0, description="质量评分 0~1")
    content_type_used: str = Field("summary", description="实际应用的内容类型标准")
    criteria_used: List[str] = Field(default_factory=list, description="本次检查实际使用的标准")
    issues: List[QualityIssue] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
