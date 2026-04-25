# -*- coding: utf-8 -*-
"""
veyrafish_core.output_models — Pydantic 结构化输出模型

供 invoke_structured() 使用，替代各节点中的手工 JSON Schema 字典。
当前已定义：
- 搜索、总结、反思、报告节点输出模型（三引擎共用）
- Evidence / EvidenceAggregate（Wave 5 共享证据层）
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# 搜索节点输出（FirstSearchNode / ReflectionNode 共用）
# ------------------------------------------------------------------

class SearchOutput(BaseModel):
    """节点 FirstSearchNode / ReflectionNode 的结构化输出。"""

    search_query: str = Field(..., description="优化后的搜索查询词")
    search_tool: str = Field(
        ...,
        description=(
            "选用的搜索工具名称，如 search_topic_globally / comprehensive_search / basic_search_news"
        ),
    )
    reasoning: str = Field(..., description="工具选择推理说明")
    start_date: Optional[str] = Field(None, description="可选起始日期，格式 YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="可选结束日期，格式 YYYY-MM-DD")
    platform: Optional[str] = Field(None, description="可选平台名称")
    time_period: Optional[str] = Field(None, description="热点时间范围，如 week / month")


# ------------------------------------------------------------------
# 总结节点输出
# ------------------------------------------------------------------

class SummaryOutput(BaseModel):
    """节点 FirstSummaryNode 的结构化输出。"""

    paragraph_latest_state: str = Field(..., description="当前段落的最新总结内容")


class ReflectionSummaryOutput(BaseModel):
    """节点 ReflectionSummaryNode 的结构化输出。"""

    updated_paragraph_latest_state: str = Field(..., description="反思后更新的段落总结")


# ------------------------------------------------------------------
# 报告结构节点输出
# ------------------------------------------------------------------

class ReportStructureItem(BaseModel):
    """报告中单个段落的结构定义。"""

    title: str = Field(..., description="段落标题")
    content: str = Field(..., description="段落预期研究内容的简要描述")


# ------------------------------------------------------------------
# Wave 5：共享证据层模型
# ------------------------------------------------------------------

class Evidence(BaseModel):
    """
    单条结构化证据。

    由三引擎在研究过程中持续沉淀，存入 evidence 表，
    供 ReportEngine 和 ForumEngine 读取。
    """

    evidence_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="证据唯一 ID"
    )
    task_id: str = Field(..., description="关联的研究任务 ID")
    engine: str = Field(..., description="来源引擎：insight / media / query")
    paragraph_index: Optional[int] = Field(None, description="段落索引（从 0 开始）")
    claim: str = Field(..., description="证据声明（一句话，客观陈述）")
    supporting_text: str = Field("", description="原文摘录，支撑 claim 的具体文本")
    source_url: str = Field("", description="来源 URL")
    source_title: str = Field("", description="来源标题")
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="置信度 0~1")
    sentiment: Optional[str] = Field(
        None, description="情感倾向：positive / negative / neutral"
    )
    tags: List[str] = Field(default_factory=list, description="自定义标签")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        description="创建时间（ISO8601 UTC）"
    )


class EvidenceAggregate(BaseModel):
    """跨引擎证据聚合摘要，供 ReportEngine / ForumEngine 使用。"""

    total_count: int = Field(0, description="证据总条数")
    by_engine: Dict[str, int] = Field(
        default_factory=dict, description="按引擎分组的证据数量"
    )
    by_sentiment: Dict[str, int] = Field(
        default_factory=dict, description="按情感倾向分组的证据数量"
    )
    avg_confidence: float = Field(0.0, description="平均置信度")
    top_claims: List[str] = Field(
        default_factory=list, description="置信度最高的 N 条 claim"
    )
    conflicts: List[Dict] = Field(
        default_factory=list,
        description="相互矛盾的证据对（sentiment 相反的高置信度证据）"
    )
