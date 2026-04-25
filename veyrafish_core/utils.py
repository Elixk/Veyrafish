# -*- coding: utf-8 -*-
"""
veyrafish_core.utils — 三引擎共用工具函数

此模块抽取了三引擎 utils/text_processing.py 中完全相同的 format_search_results_for_prompt。
"""

from typing import Any, Dict, List


def truncate_content(content: str, max_length: int) -> str:
    """将文本截断到 max_length 个字符。"""
    if not content:
        return ""
    return content[:max_length] if len(content) > max_length else content


def format_search_results_for_prompt(
    search_results: List[Dict[str, Any]],
    max_length: int = 20000,
) -> List[str]:
    """
    格式化搜索结果列表，用于传入 LLM 提示词。

    每条结果取 content 字段并截断到 max_length 字符，
    返回字符串列表供提示词拼接。
    """
    formatted: List[str] = []
    for result in search_results:
        content = result.get("content", "")
        if content:
            formatted.append(truncate_content(content, max_length))
    return formatted
