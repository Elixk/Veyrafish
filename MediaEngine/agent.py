# -*- coding: utf-8 -*-
"""
MediaEngine/agent.py — 媒析引擎 Agent（基于 BaseResearchAgent）

MediaEngine 独有能力
---------------------
- Bocha 多模态网络搜索（BochaMultimodalSearch）
- Anspire AI 搜索（AnspireSearchAgent 子类）
- 搜索结果字段映射（webpages → 标准 dict）
"""

import os
from typing import Any, List, Optional

from loguru import logger

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
from .tools import AnspireAISearch, AnspireResponse, BochaMultimodalSearch, BochaResponse
from .utils import Settings, settings


class DeepSearchAgent(BaseResearchAgent):
    """MediaEngine Deep Search Agent（继承自 BaseResearchAgent）。"""

    ENABLE_EVIDENCE_SINK = True

    def __init__(self, config: Optional[Settings] = None) -> None:
        super().__init__(config=config or settings)
        logger.info("Media Agent已初始化")
        logger.info(f"使用LLM: {self.llm_client.get_model_info()}")
        logger.info("搜索工具集: BochaMultimodalSearch (支持5种多模态搜索工具)")

    # ------------------------------------------------------------------
    # 抽象方法实现
    # ------------------------------------------------------------------

    def _initialize_llm(self) -> LLMClient:
        return LLMClient(
            api_key=(self.config.MEDIA_ENGINE_API_KEY or self.config.MINDSPIDER_API_KEY),
            model_name=(self.config.MEDIA_ENGINE_MODEL_NAME or self.config.MINDSPIDER_MODEL_NAME),
            base_url=(self.config.MEDIA_ENGINE_BASE_URL or self.config.MINDSPIDER_BASE_URL),
            engine_name="MediaEngine",
        )

    def _initialize_search_agency(self) -> BochaMultimodalSearch:
        return BochaMultimodalSearch(
            api_key=(self.config.BOCHA_API_KEY or self.config.BOCHA_WEB_SEARCH_API_KEY)
        )

    def _initialize_nodes(self) -> None:
        self.first_search_node = FirstSearchNode(self.llm_client)
        self.reflection_node = ReflectionNode(self.llm_client)
        self.first_summary_node = FirstSummaryNode(self.llm_client)
        self.reflection_summary_node = ReflectionSummaryNode(self.llm_client)
        self.report_formatting_node = ReportFormattingNode(self.llm_client)
        self._report_structure_node_class = ReportStructureNode

    def _create_initial_state(self) -> State:
        return State()

    def execute_search_tool(self, tool_name: str, query: str, **kwargs) -> BochaResponse:
        """调用 Bocha 多模态搜索工具。"""
        logger.info(f"  → 执行搜索工具: {tool_name}")
        if tool_name == "comprehensive_search":
            return self.search_agency.comprehensive_search(query, kwargs.get("max_results", 10))
        elif tool_name == "web_search_only":
            return self.search_agency.web_search_only(query, kwargs.get("max_results", 15))
        elif tool_name == "search_for_structured_data":
            return self.search_agency.search_for_structured_data(query)
        elif tool_name == "search_last_24_hours":
            return self.search_agency.search_last_24_hours(query)
        elif tool_name == "search_last_week":
            return self.search_agency.search_last_week(query)
        else:
            logger.info(f"  ⚠️  未知的搜索工具: {tool_name}，使用默认综合搜索")
            return self.search_agency.comprehensive_search(query)

    def _normalize_search_response(self, response: BochaResponse) -> List[dict]:
        """将 BochaResponse.webpages 标准化为统一 dict 列表。"""
        results: List[dict] = []
        if not (response and response.webpages):
            return results
        cap = min(len(response.webpages), 10)
        for r in response.webpages[:cap]:
            results.append({
                "title": r.name,
                "url": r.url,
                "content": r.snippet,
                "score": None,
                "raw_content": r.snippet,
                "published_date": r.date_last_crawled,
            })
        return results

    def _get_content_max_length(self) -> int:
        return self.config.SEARCH_CONTENT_MAX_LENGTH

    def _get_default_search_tool(self) -> str:
        return "comprehensive_search"

    def _prepare_search_call(self, search_tool: str, search_output: dict) -> tuple:
        """Media 特有：为 comprehensive_search / web_search_only 添加 max_results。"""
        kwargs: dict = {}
        if search_tool in ("comprehensive_search", "web_search_only"):
            kwargs["max_results"] = 10
        return search_tool, kwargs

    def _record_search_results(
        self,
        paragraph: Any,
        query: str,
        results: List[dict],
        search_tool: str = "",
    ) -> None:
        """Media 覆写：传递额外的 search_tool 和 paragraph_title 参数。"""
        paragraph.research.add_search_results(
            query,
            results,
            search_tool=search_tool,
            paragraph_title=paragraph.title,
        )


class AnspireSearchAgent(DeepSearchAgent):
    """使用 Anspire AI Search 的 MediaEngine 变体。"""

    def __init__(self, config: Optional[Settings] = None) -> None:
        cfg = config or settings
        self.config = cfg
        self.llm_client = self._initialize_llm()
        self.search_agency = AnspireAISearch(api_key=cfg.ANSPIRE_API_KEY)
        self._initialize_nodes()
        self.state = self._create_initial_state()
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
        self._evidence_store = None
        try:
            from veyrafish_core.skills import default_registry
            self._skill_registry = default_registry
        except Exception:
            self._skill_registry = None
        logger.info("Media Agent已初始化")
        logger.info(f"使用LLM: {self.llm_client.get_model_info()}")
        logger.info("搜索工具集: AnspireSearch")

    def execute_search_tool(self, tool_name: str, query: str, **kwargs) -> AnspireResponse:
        logger.info(f"  → 执行搜索工具: {tool_name}")
        if tool_name == "comprehensive_search":
            return self.search_agency.comprehensive_search(query, kwargs.get("max_results", 10))
        elif tool_name == "search_last_24_hours":
            return self.search_agency.search_last_24_hours(query)
        elif tool_name == "search_last_week":
            return self.search_agency.search_last_week(query)
        else:
            logger.info(f"  ⚠️  未知的搜索工具: {tool_name}，使用默认综合搜索")
            return self.search_agency.comprehensive_search(query)

    def _normalize_search_response(self, response: AnspireResponse) -> List[dict]:
        """将 AnspireResponse 标准化。"""
        results: List[dict] = []
        if not (response and hasattr(response, "webpages") and response.webpages):
            return results
        cap = min(len(response.webpages), 10)
        for r in response.webpages[:cap]:
            results.append({
                "title": r.name,
                "url": r.url,
                "content": r.snippet,
                "score": None,
                "raw_content": r.snippet,
                "published_date": getattr(r, "date_last_crawled", None),
            })
        return results


def create_agent(config_file: Optional[str] = None) -> DeepSearchAgent:
    """创建 MediaEngine Agent 实例的便捷工厂函数。"""
    cfg = Settings()
    if cfg.SEARCH_TOOL_TYPE == "AnspireAPI":
        return AnspireSearchAgent(cfg)
    return DeepSearchAgent(cfg)
