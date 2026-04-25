# -*- coding: utf-8 -*-
"""QueryRewriteSkill — LLM 驱动的查询改写 + 搜索工具选择。"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from loguru import logger
from pydantic import BaseModel

from veyrafish_core.skill import Skill, SkillContext
from veyrafish_core.skills._models import QueryRewriteInput, QueryRewriteOutput


_DEFAULT_TOOLS = ["basic_search", "comprehensive_search", "search_topic_globally"]

_SYSTEM_PROMPT = """你是一位专业的信息检索优化专家。
给定用户的原始搜索需求，你需要：
1. 将查询改写为更精准、更具区分度的搜索词
2. 从可用工具列表中选择最合适的搜索工具
3. 如有必要，推断合适的日期范围或平台限制

请以 JSON 格式输出，包含字段：
- rewritten_query: 改写后的搜索词（字符串）
- search_tool: 选用的工具名称（字符串）
- reasoning: 改写和选择的简短推理（字符串）
- selection_rule: 触发的工具选择规则（字符串）
- constraints: 应用的约束列表（字符串数组）
- start_date: 起始日期 YYYY-MM-DD（可选，不确定则省略）
- end_date: 截止日期 YYYY-MM-DD（可选）
- platform: 平台名称（可选，如 weibo/wechat/news）
- time_period: 时间范围（可选，如 week/month）"""


class QueryRewriteSkill(Skill):
    """LLM 驱动的查询改写 Skill，借鉴 research-ideation 的规划思路。"""

    name = "query_rewrite"
    description = "使用 LLM 将原始搜索查询改写为更精准的检索词，并推荐合适的搜索工具"
    version = "0.1.0"
    tags = ["search", "llm", "query_optimization"]
    input_schema = QueryRewriteInput
    output_schema = QueryRewriteOutput

    def execute(self, input: QueryRewriteInput, ctx: SkillContext) -> QueryRewriteOutput:
        if ctx.llm_client is None:
            logger.warning("[QueryRewriteSkill] llm_client 未提供，返回启发式改写结果")
            return self._fallback(input, reason="LLM 不可用，使用启发式查询改写与工具选择")

        tools = input.search_tools_available or _DEFAULT_TOOLS
        user_msg = (
            f"原始查询：{input.original_query}\n"
            f"研究背景：{input.context or '无'}\n"
            f"可用搜索工具：{', '.join(tools)}"
        )

        try:
            from veyrafish_core.output_models import SearchOutput  # noqa: F401 (type hint only)
            result = ctx.llm_client.invoke_structured(
                prompt=user_msg,
                system_prompt=_SYSTEM_PROMPT,
                output_model=QueryRewriteOutput,
            )
            if isinstance(result, QueryRewriteOutput):
                return self._normalize_output(result, input)
            return self._fallback(input, reason="LLM 未返回结构化结果，使用启发式回退")
        except Exception as exc:
            logger.warning(f"[QueryRewriteSkill] LLM 调用失败：{exc}，使用启发式回退")
            return self._fallback(input, reason=f"LLM 调用失败：{exc}")

    def _normalize_output(self, output: QueryRewriteOutput, input: QueryRewriteInput) -> QueryRewriteOutput:
        tools = input.search_tools_available or _DEFAULT_TOOLS
        heuristic = self._fallback(input, reason="启发式规则已补齐约束")
        if not output.rewritten_query:
            output.rewritten_query = heuristic.rewritten_query
        if output.search_tool not in tools:
            output.search_tool = heuristic.search_tool
        if not output.selection_rule:
            output.selection_rule = heuristic.selection_rule
        if not output.reasoning:
            output.reasoning = heuristic.reasoning
        if not output.platform:
            output.platform = heuristic.platform
        if not output.time_period:
            output.time_period = heuristic.time_period
        if not output.start_date:
            output.start_date = heuristic.start_date
        if not output.end_date:
            output.end_date = heuristic.end_date
        derived_constraints = self._build_constraints(
            output.platform,
            output.start_date,
            output.end_date,
            output.time_period,
        )
        merged_constraints = list(
            dict.fromkeys([*derived_constraints, *heuristic.constraints, *output.constraints])
        )
        output.constraints = merged_constraints
        return output

    def _fallback(self, input: QueryRewriteInput, reason: str) -> QueryRewriteOutput:
        tools = input.search_tools_available or _DEFAULT_TOOLS
        platform = self._infer_platform(input)
        start_date, end_date, time_period = self._infer_time_constraints(input)
        selection_rule, search_tool = self._select_tool(input, tools, platform, time_period)
        return QueryRewriteOutput(
            rewritten_query=self._rewrite_query(input, platform, time_period),
            search_tool=search_tool,
            reasoning=reason,
            selection_rule=selection_rule,
            constraints=self._build_constraints(platform, start_date, end_date, time_period),
            start_date=start_date,
            end_date=end_date,
            platform=platform,
            time_period=time_period,
        )

    def _rewrite_query(self, input: QueryRewriteInput, platform: str | None, time_period: str | None) -> str:
        parts = [input.original_query.strip()]
        context = input.context.strip()
        if context:
            parts.append(context[:80])
        if platform and platform.lower() not in input.original_query.lower():
            parts.append(platform)
        if time_period in {"week", "month", "recent"}:
            parts.append("最新动态")
        return " ".join(part for part in parts if part)

    def _infer_platform(self, input: QueryRewriteInput) -> str | None:
        text = f"{input.original_query} {input.context}".lower()
        platform_map = {
            "weibo": ["微博", "weibo"],
            "wechat": ["微信", "wechat", "公众号"],
            "news": ["新闻", "news", "媒体报道"],
            "forum": ["论坛", "贴吧", "reddit", "社区"],
            "video": ["视频", "b站", "bilibili", "youtube"],
        }
        for platform, keywords in platform_map.items():
            if any(keyword in text for keyword in keywords):
                return platform
        return None

    def _infer_time_constraints(self, input: QueryRewriteInput) -> tuple[str | None, str | None, str | None]:
        text = f"{input.original_query} {input.context}"
        match = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
        if match:
            date_value = match.group(1)
            return date_value, date_value, None

        today = datetime.now().date()
        if any(token in text for token in ("今日", "今天", "当天")):
            date_value = today.isoformat()
            return date_value, date_value, "day"
        if any(token in text for token in ("近7天", "最近一周", "本周")):
            return (today - timedelta(days=7)).isoformat(), today.isoformat(), "week"
        if any(token in text for token in ("近30天", "最近一个月", "本月")):
            return (today - timedelta(days=30)).isoformat(), today.isoformat(), "month"
        if any(token in text for token in ("最新", "近期", "最近")):
            return None, None, "recent"
        return None, None, None

    def _select_tool(
        self,
        input: QueryRewriteInput,
        tools: list[str],
        platform: str | None,
        time_period: str | None,
    ) -> tuple[str, str]:
        text = f"{input.original_query} {input.context}".lower()
        if platform and (tool := self._pick_tool(tools, ["comprehensive", "global", "topic"])):
            return "platform_specific_or_cross_source", tool
        if time_period and (tool := self._pick_tool(tools, ["comprehensive", "news", "global"])):
            return "recency_sensitive_query", tool
        if any(token in text for token in ("对比", "趋势", "热点", "全球", "全网", "舆情")):
            if tool := self._pick_tool(tools, ["global", "comprehensive", "topic"]):
                return "trend_or_broad_topic_query", tool
        if any(token in text for token in ("新闻", "news", "快讯", "媒体")):
            if tool := self._pick_tool(tools, ["news", "comprehensive", "basic"]):
                return "news_focused_query", tool
        return "default_first_available_tool", tools[0] if tools else "basic_search"

    @staticmethod
    def _pick_tool(tools: list[str], preferred_keywords: list[str]) -> str | None:
        lowered = [(tool, tool.lower()) for tool in tools]
        for keyword in preferred_keywords:
            for original, lower_name in lowered:
                if keyword in lower_name:
                    return original
        return None

    @staticmethod
    def _build_constraints(
        platform: str | None,
        start_date: str | None,
        end_date: str | None,
        time_period: str | None,
    ) -> list[str]:
        constraints = []
        if platform:
            constraints.append(f"platform={platform}")
        if start_date and end_date:
            constraints.append(f"date_range={start_date}..{end_date}")
        elif start_date:
            constraints.append(f"start_date={start_date}")
        elif end_date:
            constraints.append(f"end_date={end_date}")
        if time_period:
            constraints.append(f"time_period={time_period}")
        return constraints
