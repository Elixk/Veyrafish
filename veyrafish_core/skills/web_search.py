# -*- coding: utf-8 -*-
"""WebSearchSkill — 统一网络搜索适配层（Anspire / Bocha / Tavily）。"""

from __future__ import annotations

from typing import Any, List
from urllib.parse import urlparse

from loguru import logger
from pydantic import BaseModel

from veyrafish_core.skill import Skill, SkillContext
from veyrafish_core.skills._models import (
    SearchResult,
    WebSearchInput,
    WebSearchOutput,
)


class WebSearchSkill(Skill):
    """
    统一网络搜索 Skill。

    根据 ctx.config.SEARCH_TOOL_TYPE（或 input.provider）自动选择
    Anspire / Bocha / Tavily 适配器。
    """

    name = "web_search"
    description = "使用配置的搜索 Provider（Anspire/Bocha/Tavily）执行网络搜索，返回结构化结果列表"
    version = "0.1.0"
    tags = ["search", "web", "information_retrieval"]
    input_schema = WebSearchInput
    output_schema = WebSearchOutput
    _PROVIDER_ALIASES = {
        "anspire": "anspire",
        "anspireapi": "anspire",
        "anspire_api": "anspire",
        "bocha": "bocha",
        "bochaai": "bocha",
        "bocha_api": "bocha",
        "tavily": "tavily",
        "tavilysearch": "tavily",
        "tavily_api": "tavily",
    }

    def execute(self, input: WebSearchInput, ctx: SkillContext) -> WebSearchOutput:
        provider = self._resolve_provider(input, ctx)
        try:
            results = self._normalize_results(self._search(provider, input, ctx), input.max_results)
            return WebSearchOutput(
                results=results,
                provider_used=provider,
                total_found=len(results),
            )
        except Exception as exc:
            logger.warning(f"[WebSearchSkill] 搜索失败（provider={provider}）：{exc}")
            return WebSearchOutput(
                results=[],
                provider_used=provider,
                total_found=0,
                error=str(exc),
            )

    def on_error(self, error: Exception, input: BaseModel, ctx: SkillContext) -> WebSearchOutput:
        return WebSearchOutput(results=[], provider_used="none", total_found=0, error=str(error))

    # ------------------------------------------------------------------
    # 内部实现
    # ------------------------------------------------------------------

    def _resolve_provider(self, input: WebSearchInput, ctx: SkillContext) -> str:
        """确定实际使用的 Provider。"""
        if input.provider:
            return self._normalize_provider(input.provider)
        if ctx.config and hasattr(ctx.config, "SEARCH_TOOL_TYPE"):
            tool_type = getattr(ctx.config, "SEARCH_TOOL_TYPE", "") or "AnspireAPI"
            normalized = self._normalize_provider(tool_type)
            if normalized:
                return normalized
        return "anspire"

    def _search(self, provider: str, input: WebSearchInput, ctx: SkillContext) -> List[SearchResult]:
        """分发到具体 Provider。"""
        if provider == "anspire":
            return self._search_anspire(input, ctx)
        elif provider == "bocha":
            return self._search_bocha(input, ctx)
        elif provider == "tavily":
            return self._search_tavily(input, ctx)
        else:
            raise ValueError(f"未知 Provider: {provider}")

    def _search_anspire(self, input: WebSearchInput, ctx: SkillContext) -> List[SearchResult]:
        """Anspire 搜索适配。"""
        import requests
        cfg = ctx.config
        base_url = getattr(cfg, "ANSPIRE_BASE_URL", "https://plugin.anspire.cn/api/ntsearch/search")
        api_key = self._require_api_key(cfg, "ANSPIRE_API_KEY", "anspire")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "query": input.query,
            "size": input.max_results,
        }
        resp = requests.post(base_url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = self._extract_items(data)
        return [
            self._make_result(
                title=item.get("name", ""),
                url=item.get("url", ""),
                content=item.get("snippet", ""),
                score=item.get("score", 0.7),
            )
            for item in items
        ]

    def _search_bocha(self, input: WebSearchInput, ctx: SkillContext) -> List[SearchResult]:
        """Bocha 搜索适配。"""
        import requests
        cfg = ctx.config
        base_url = getattr(cfg, "BOCHA_BASE_URL", "https://api.bocha.cn/v1/ai-search")
        api_key = self._require_api_key(cfg, "BOCHA_WEB_SEARCH_API_KEY", "bocha")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"query": input.query, "count": input.max_results}
        resp = requests.post(base_url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = self._extract_items(data)
        return [
            self._make_result(
                title=item.get("name", ""),
                url=item.get("url", ""),
                content=item.get("snippet", ""),
                score=item.get("score", 0.7),
            )
            for item in items
        ]

    def _search_tavily(self, input: WebSearchInput, ctx: SkillContext) -> List[SearchResult]:
        """Tavily 搜索适配。"""
        from tavily import TavilyClient  # type: ignore
        cfg = ctx.config
        api_key = self._require_api_key(cfg, "TAVILY_API_KEY", "tavily")
        client = TavilyClient(api_key=api_key)
        response = client.search(input.query, max_results=input.max_results)
        return [
            self._make_result(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("content", ""),
                score=item.get("score", 0.5),
            )
            for item in response.get("results", [])
        ]

    @classmethod
    def _normalize_provider(cls, provider: str) -> str:
        normalized = "".join(ch for ch in str(provider or "").strip().lower() if ch.isalnum())
        if not normalized:
            return "anspire"
        return cls._PROVIDER_ALIASES.get(normalized, normalized)

    @staticmethod
    def _require_api_key(cfg: Any, field_name: str, provider: str) -> str:
        api_key = str(getattr(cfg, field_name, "") or "").strip() if cfg else ""
        if not api_key:
            raise RuntimeError(f"{provider} provider 缺少配置：{field_name}")
        return api_key

    @staticmethod
    def _extract_items(payload: Any) -> list[dict]:
        candidate_paths = (
            ("data", "webPages", "value"),
            ("webPages", "value"),
            ("data", "value"),
            ("data", "results"),
            ("results",),
        )
        for path in candidate_paths:
            current = payload
            for key in path:
                if not isinstance(current, dict):
                    current = None
                    break
                current = current.get(key)
            if isinstance(current, list):
                return [item for item in current if isinstance(item, dict)]
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return []

    @classmethod
    def _make_result(cls, title: Any, url: Any, content: Any, score: Any) -> SearchResult:
        clean_url = str(url or "").strip()
        clean_title = str(title or "").strip()
        clean_content = str(content or "").strip()
        if not clean_title and clean_url:
            clean_title = cls._infer_title_from_url(clean_url)
        return SearchResult(
            title=clean_title,
            url=clean_url,
            content=clean_content,
            score=cls._normalize_score(score),
        )

    @classmethod
    def _normalize_results(cls, results: List[SearchResult], max_results: int) -> List[SearchResult]:
        normalized: List[SearchResult] = []
        seen_keys: set[str] = set()
        for result in results:
            item = cls._make_result(result.title, result.url, result.content, result.score)
            unique_key = item.url or f"{item.title}|{item.content}"
            if unique_key in seen_keys:
                continue
            if not (item.url or item.title or item.content):
                continue
            seen_keys.add(unique_key)
            normalized.append(item)
            if len(normalized) >= max_results:
                break
        return normalized

    @staticmethod
    def _normalize_score(score: Any) -> float:
        try:
            value = float(score)
        except Exception:
            value = 0.0
        return max(0.0, min(1.0, value))

    @staticmethod
    def _infer_title_from_url(url: str) -> str:
        try:
            parsed = urlparse(url)
            return parsed.netloc or url
        except Exception:
            return url
