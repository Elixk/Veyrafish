# -*- coding: utf-8 -*-
"""
QueryEngine/agent.py — 检索引擎 Agent（基于 BaseResearchAgent）

QueryEngine 独有能力
---------------------
- Tavily 新闻搜索（TavilyNewsAgency）
- 日期范围搜索（search_news_by_date）
- 六种新闻搜索工具
"""

from typing import List, Optional

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
from .tools import TavilyNewsAgency, TavilyResponse
from .utils import Settings, format_search_results_for_prompt


class DeepSearchAgent(BaseResearchAgent):
    """QueryEngine Deep Search Agent（继承自 BaseResearchAgent）。"""

    ENABLE_EVIDENCE_SINK = True

    def __init__(self, config: Optional[Settings] = None) -> None:
        from .utils.config import settings as _settings
        super().__init__(config=config or _settings)
        logger.info("Query Agent已初始化")
        logger.info(f"使用LLM: {self.llm_client.get_model_info()}")
        logger.info("搜索工具集: TavilyNewsAgency (支持6种搜索工具)")

    # ------------------------------------------------------------------
    # 抽象方法实现
    # ------------------------------------------------------------------

    def _initialize_llm(self) -> LLMClient:
        return LLMClient(
            api_key=self.config.QUERY_ENGINE_API_KEY,
            model_name=self.config.QUERY_ENGINE_MODEL_NAME,
            base_url=self.config.QUERY_ENGINE_BASE_URL,
            engine_name="QueryEngine",
        )

    def _initialize_search_agency(self) -> TavilyNewsAgency:
        return TavilyNewsAgency(api_key=self.config.TAVILY_API_KEY)

    def _initialize_nodes(self) -> None:
        self.first_search_node = FirstSearchNode(self.llm_client)
        self.reflection_node = ReflectionNode(self.llm_client)
        self.first_summary_node = FirstSummaryNode(self.llm_client)
        self.reflection_summary_node = ReflectionSummaryNode(self.llm_client)
        self.report_formatting_node = ReportFormattingNode(self.llm_client)
        self._report_structure_node_class = ReportStructureNode

    def _create_initial_state(self) -> State:
        return State()

    def execute_search_tool(self, tool_name: str, query: str, **kwargs) -> TavilyResponse:
        """调用 Tavily 新闻搜索工具。"""
        logger.info(f"  → 执行搜索工具: {tool_name}")
        if tool_name == "basic_search_news":
            return self.search_agency.basic_search_news(query, kwargs.get("max_results", 7))
        elif tool_name == "deep_search_news":
            return self.search_agency.deep_search_news(query)
        elif tool_name == "search_news_last_24_hours":
            return self.search_agency.search_news_last_24_hours(query)
        elif tool_name == "search_news_last_week":
            return self.search_agency.search_news_last_week(query)
        elif tool_name == "search_images_for_news":
            return self.search_agency.search_images_for_news(query)
        elif tool_name == "search_news_by_date":
            start_date = kwargs.get("start_date")
            end_date = kwargs.get("end_date")
            if not start_date or not end_date:
                raise ValueError("search_news_by_date 工具需要 start_date 和 end_date 参数")
            return self.search_agency.search_news_by_date(query, start_date, end_date)
        else:
            logger.warning(f"  ⚠️  未知的搜索工具: {tool_name}，使用默认基础搜索")
            return self.search_agency.basic_search_news(query)

    def _normalize_search_response(self, response: TavilyResponse) -> List[dict]:
        """将 TavilyResponse.results 标准化为统一 dict 列表。"""
        results: List[dict] = []
        if not (response and response.results):
            return results
        cap = min(len(response.results), 10)
        for r in response.results[:cap]:
            results.append({
                "title": r.title,
                "url": r.url,
                "content": r.content,
                "score": r.score,
                "raw_content": r.raw_content,
                "published_date": r.published_date,
            })
        return results

    def _get_content_max_length(self) -> int:
        return self.config.SEARCH_CONTENT_MAX_LENGTH

    def _get_default_search_tool(self) -> str:
        return "basic_search_news"

    def _prepare_search_call(self, search_tool: str, search_output: dict) -> tuple:
        """Query 特有：处理 search_news_by_date 的日期参数，无效时回退基础搜索。"""
        kwargs: dict = {}
        if search_tool == "search_news_by_date":
            start_date = search_output.get("start_date")
            end_date = search_output.get("end_date")
            if start_date and end_date:
                if self._validate_date_format(start_date) and self._validate_date_format(end_date):
                    kwargs["start_date"] = start_date
                    kwargs["end_date"] = end_date
                    logger.info(f"  - 时间范围: {start_date} 到 {end_date}")
                else:
                    logger.info("  ⚠️  日期格式错误，改用基础搜索")
                    search_tool = "basic_search_news"
            else:
                logger.info("  ⚠️  search_news_by_date缺少时间参数，改用基础搜索")
                search_tool = "basic_search_news"
        return search_tool, kwargs


def create_agent(config_file: Optional[str] = None) -> DeepSearchAgent:
    """创建 QueryEngine Agent 实例的便捷工厂函数。"""
    from .utils.config import Settings as _Settings
    return DeepSearchAgent(_Settings())
