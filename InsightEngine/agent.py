# -*- coding: utf-8 -*-
"""
InsightEngine/agent.py — 洞察引擎 Agent（基于 BaseResearchAgent）

本文件通过继承 veyrafish_core.BaseResearchAgent 消除了与
MediaEngine / QueryEngine 之间约 70% 的重复代码。

InsightEngine 独有能力
---------------------
- 私有数据库搜索（MediaCrawlerDB + keyword_optimizer）
- 情感分析（WeiboMultilingualSentiment）
- 聚类采样（KMeans + SentenceTransformer）
- 复杂搜索参数（日期 / 平台 / 热点限制）
"""

import os
from typing import Any, Dict, List, Optional, Union

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans

from veyrafish_core import BaseResearchAgent
from veyrafish_core.llm_client import LLMClient

from .nodes import (
    FirstSearchNode,
    FirstSummaryNode,
    ReflectionNode,
    ReflectionSummaryNode,
    ReportFormattingNode,
    ReportStructureNode,
)
from .state import State
from .tools import (
    DBResponse,
    MediaCrawlerDB,
    keyword_optimizer,
    multilingual_sentiment_analyzer,
)
from .utils.config import Settings, settings

ENABLE_CLUSTERING: bool = True
MAX_CLUSTERED_RESULTS: int = 50
RESULTS_PER_CLUSTER: int = 5


class DeepSearchAgent(BaseResearchAgent):
    """InsightEngine Deep Search Agent（继承自 BaseResearchAgent）。"""

    ENABLE_EVIDENCE_SINK = True

    def __init__(self, config: Optional[Settings] = None) -> None:
        # InsightEngine 独有的懒加载 / 情感分析器放在 super() 之前初始化
        self._clustering_model = None
        self.sentiment_analyzer = multilingual_sentiment_analyzer
        super().__init__(config=config or settings)
        logger.info("Insight Agent已初始化")
        logger.info(f"使用LLM: {self.llm_client.get_model_info()}")
        logger.info("搜索工具集: MediaCrawlerDB (支持5种本地数据库查询工具)")
        logger.info("情感分析: WeiboMultilingualSentiment (支持22种语言的情感分析)")

    # ------------------------------------------------------------------
    # 抽象方法实现
    # ------------------------------------------------------------------

    def _initialize_llm(self) -> LLMClient:
        return LLMClient(
            api_key=self.config.INSIGHT_ENGINE_API_KEY,
            model_name=self.config.INSIGHT_ENGINE_MODEL_NAME,
            base_url=self.config.INSIGHT_ENGINE_BASE_URL,
            engine_name="InsightEngine",
        )

    def _initialize_search_agency(self) -> MediaCrawlerDB:
        return MediaCrawlerDB()

    def _initialize_nodes(self) -> None:
        self.first_search_node = FirstSearchNode(self.llm_client)
        self.reflection_node = ReflectionNode(self.llm_client)
        self.first_summary_node = FirstSummaryNode(self.llm_client)
        self.reflection_summary_node = ReflectionSummaryNode(self.llm_client)
        self.report_formatting_node = ReportFormattingNode(self.llm_client)
        self._report_structure_node_class = ReportStructureNode

    def _create_initial_state(self) -> State:
        return State()

    def execute_search_tool(self, tool_name: str, query: str, **kwargs) -> DBResponse:
        """调用私有数据库搜索工具（含关键词优化 + 可选情感分析）。"""
        logger.info(f"  → 执行数据库查询工具: {tool_name}")

        if tool_name == "search_hot_content":
            time_period = kwargs.get("time_period", "week")
            limit = kwargs.get("limit", 100)
            response = self.search_agency.search_hot_content(time_period=time_period, limit=limit)
            if kwargs.get("enable_sentiment", True) and response.results:
                sa = self._perform_sentiment_analysis(response.results)
                if sa:
                    response.parameters["sentiment_analysis"] = sa
            return response

        if tool_name == "analyze_sentiment":
            texts = kwargs.get("texts", query)
            result = self.analyze_sentiment_only(texts)
            return DBResponse(
                tool_name="analyze_sentiment",
                parameters={"texts": texts if isinstance(texts, list) else [texts], **kwargs},
                results=[],
                results_count=0,
                metadata=result,
            )

        optimized = keyword_optimizer.optimize_keywords(
            original_query=query, context=f"使用{tool_name}工具进行查询"
        )
        logger.info(f"  🔍 原始查询: '{query}'")
        logger.info(f"  ✨ 优化后关键词: {optimized.optimized_keywords}")

        all_results: list = []
        for keyword in optimized.optimized_keywords:
            logger.info(f"    查询关键词: '{keyword}'")
            try:
                if tool_name == "search_topic_globally":
                    resp = self.search_agency.search_topic_globally(
                        topic=keyword,
                        limit_per_table=self.config.DEFAULT_SEARCH_TOPIC_GLOBALLY_LIMIT_PER_TABLE,
                    )
                elif tool_name == "search_topic_by_date":
                    resp = self.search_agency.search_topic_by_date(
                        topic=keyword,
                        start_date=kwargs["start_date"],
                        end_date=kwargs["end_date"],
                        limit_per_table=self.config.DEFAULT_SEARCH_TOPIC_BY_DATE_LIMIT_PER_TABLE,
                    )
                elif tool_name == "get_comments_for_topic":
                    per_kw = max(
                        self.config.DEFAULT_GET_COMMENTS_FOR_TOPIC_LIMIT
                        // len(optimized.optimized_keywords),
                        50,
                    )
                    resp = self.search_agency.get_comments_for_topic(
                        topic=keyword, limit=per_kw
                    )
                elif tool_name == "search_topic_on_platform":
                    per_kw = max(
                        self.config.DEFAULT_SEARCH_TOPIC_ON_PLATFORM_LIMIT
                        // len(optimized.optimized_keywords),
                        30,
                    )
                    resp = self.search_agency.search_topic_on_platform(
                        platform=kwargs["platform"],
                        topic=keyword,
                        start_date=kwargs.get("start_date"),
                        end_date=kwargs.get("end_date"),
                        limit=per_kw,
                    )
                else:
                    resp = self.search_agency.search_topic_globally(
                        topic=keyword,
                        limit_per_table=self.config.DEFAULT_SEARCH_TOPIC_GLOBALLY_LIMIT_PER_TABLE,
                    )
                if resp.results:
                    all_results.extend(resp.results)
            except Exception as exc:
                logger.error(f"      查询'{keyword}'时出错: {exc}")

        unique = self._deduplicate_results(all_results)
        if ENABLE_CLUSTERING:
            unique = self._cluster_and_sample_results(unique)

        if kwargs.get("enable_sentiment", True) and unique:
            sa = self._perform_sentiment_analysis(unique)
            if sa:
                return DBResponse(
                    tool_name=f"{tool_name}_optimized",
                    parameters={
                        "original_query": query,
                        "optimized_keywords": optimized.optimized_keywords,
                        "sentiment_analysis": sa,
                        **kwargs,
                    },
                    results=unique,
                    results_count=len(unique),
                )
        return DBResponse(
            tool_name=f"{tool_name}_optimized",
            parameters={
                "original_query": query,
                "optimized_keywords": optimized.optimized_keywords,
                **kwargs,
            },
            results=unique,
            results_count=len(unique),
        )

    def _normalize_search_response(self, response: DBResponse) -> List[dict]:
        """将 DBResponse.results 标准化为统一 dict 列表。"""
        results: List[dict] = []
        if not (response and response.results):
            return results

        cap = len(response.results)
        if self.config.MAX_SEARCH_RESULTS_FOR_LLM > 0:
            cap = min(cap, self.config.MAX_SEARCH_RESULTS_FOR_LLM)

        for r in response.results[:cap]:
            results.append({
                "title": r.title_or_content,
                "url": r.url or "",
                "content": r.title_or_content,
                "score": r.hotness_score,
                "raw_content": r.title_or_content,
                "published_date": r.publish_time.isoformat() if r.publish_time else None,
                "platform": r.platform,
                "content_type": r.content_type,
                "author": r.author_nickname,
                "engagement": r.engagement,
            })
        return results

    def _get_content_max_length(self) -> int:
        return self.config.MAX_CONTENT_LENGTH

    def _get_default_search_tool(self) -> str:
        return "search_topic_globally"

    # ------------------------------------------------------------------
    # InsightEngine 独有钩子：复杂搜索参数构造
    # ------------------------------------------------------------------

    def _prepare_search_call(self, search_tool: str, search_output: dict) -> tuple:
        """Insight 特有：处理日期、平台、限制参数，必要时回退默认工具。"""
        kwargs: dict = {}

        if search_tool in ("search_topic_by_date", "search_topic_on_platform"):
            start_date = search_output.get("start_date")
            end_date = search_output.get("end_date")
            if start_date and end_date:
                if self._validate_date_format(start_date) and self._validate_date_format(end_date):
                    kwargs["start_date"] = start_date
                    kwargs["end_date"] = end_date
                else:
                    logger.info("    日期格式错误，改用全局搜索")
                    search_tool = "search_topic_globally"
            elif search_tool == "search_topic_by_date":
                logger.info("    search_topic_by_date缺少时间参数，改用全局搜索")
                search_tool = "search_topic_globally"

        if search_tool == "search_topic_on_platform":
            platform = search_output.get("platform")
            if platform:
                kwargs["platform"] = platform
            else:
                logger.warning("    search_topic_on_platform缺少平台参数，改用全局搜索")
                search_tool = "search_topic_globally"

        if search_tool == "search_hot_content":
            kwargs["time_period"] = search_output.get("time_period", "week")
            kwargs["limit"] = self.config.DEFAULT_SEARCH_HOT_CONTENT_LIMIT
        elif search_tool == "search_topic_globally":
            kwargs["limit_per_table"] = self.config.DEFAULT_SEARCH_TOPIC_GLOBALLY_LIMIT_PER_TABLE
        elif search_tool == "search_topic_by_date":
            kwargs["limit_per_table"] = self.config.DEFAULT_SEARCH_TOPIC_BY_DATE_LIMIT_PER_TABLE
        elif search_tool == "get_comments_for_topic":
            kwargs["limit"] = self.config.DEFAULT_GET_COMMENTS_FOR_TOPIC_LIMIT
        elif search_tool == "search_topic_on_platform":
            kwargs["limit"] = self.config.DEFAULT_SEARCH_TOPIC_ON_PLATFORM_LIMIT

        return search_tool, kwargs

    # ------------------------------------------------------------------
    # InsightEngine 独有方法（聚类 / 去重 / 情感分析）
    # ------------------------------------------------------------------

    def _get_clustering_model(self) -> SentenceTransformer:
        if self._clustering_model is None:
            logger.info("  加载聚类模型 (paraphrase-multilingual-MiniLM-L12-v2)...")
            self._clustering_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        return self._clustering_model

    def _cluster_and_sample_results(
        self,
        results: list,
        max_results: int = MAX_CLUSTERED_RESULTS,
        results_per_cluster: int = RESULTS_PER_CLUSTER,
    ) -> list:
        if len(results) <= max_results:
            return results
        try:
            texts = [r.title_or_content[:500] for r in results]
            model = self._get_clustering_model()
            embeddings = model.encode(texts, show_progress_bar=False)
            n_clusters = min(max(2, max_results // results_per_cluster), len(results))
            labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(embeddings)
            sampled: list = []
            for cid in range(n_clusters):
                cluster_items = sorted(
                    [(results[i], i) for i in np.flatnonzero(labels == cid)],
                    key=lambda x: x[0].hotness_score or 0,
                    reverse=True,
                )
                for item, _ in cluster_items[:results_per_cluster]:
                    sampled.append(item)
                    if len(sampled) >= max_results:
                        break
                if len(sampled) >= max_results:
                    break
            logger.info(f"  聚类完成: {len(results)} → {n_clusters} 主题 → {len(sampled)} 代表")
            return sampled
        except Exception as exc:
            logger.warning(f"  聚类失败，返回前{max_results}条: {exc}")
            return results[:max_results]

    def _deduplicate_results(self, results: list) -> list:
        seen: set = set()
        unique: list = []
        for r in results:
            key = r.url if r.url else r.title_or_content[:100]
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique

    def _perform_sentiment_analysis(self, results: list) -> Optional[Dict[str, Any]]:
        try:
            if not self.sentiment_analyzer.is_initialized and not self.sentiment_analyzer.is_disabled:
                self.sentiment_analyzer.initialize()
            results_dict = [
                {
                    "content": r.title_or_content,
                    "platform": r.platform,
                    "author": r.author_nickname,
                    "url": r.url,
                    "publish_time": str(r.publish_time) if r.publish_time else None,
                }
                for r in results
            ]
            result = self.sentiment_analyzer.analyze_query_results(
                query_results=results_dict, text_field="content", min_confidence=0.5
            )
            return result.get("sentiment_analysis")
        except Exception as exc:
            logger.exception(f"    ❌ 情感分析错误: {exc}")
            return None

    def analyze_sentiment_only(self, texts: Union[str, List[str]]) -> Dict[str, Any]:
        """独立情感分析工具。"""
        logger.info("  → 执行独立情感分析")
        try:
            if not self.sentiment_analyzer.is_initialized and not self.sentiment_analyzer.is_disabled:
                self.sentiment_analyzer.initialize()
            if isinstance(texts, str):
                result = self.sentiment_analyzer.analyze_single_text(texts)
                return {
                    "success": result.success and result.analysis_performed,
                    "total_analyzed": 1 if result.analysis_performed else 0,
                    "results": [result.__dict__],
                }
            batch = self.sentiment_analyzer.analyze_batch(list(texts), show_progress=True)
            return {
                "success": batch.analysis_performed and batch.success_count > 0,
                "total_analyzed": batch.total_processed if batch.analysis_performed else 0,
                "success_count": batch.success_count,
                "failed_count": batch.failed_count,
                "average_confidence": batch.average_confidence if batch.analysis_performed else 0.0,
                "results": [r.__dict__ for r in batch.results],
            }
        except Exception as exc:
            logger.exception(f"    ❌ 情感分析错误: {exc}")
            return {"success": False, "error": str(exc), "results": []}


def create_agent(config_file: Optional[str] = None) -> DeepSearchAgent:
    """创建 InsightEngine Agent 实例的便捷工厂函数。"""
    return DeepSearchAgent(Settings())
