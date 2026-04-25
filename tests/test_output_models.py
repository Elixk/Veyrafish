# -*- coding: utf-8 -*-
"""
tests/test_output_models.py — Stage C: Pydantic 结构化输出模型验证测试
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from veyrafish_core.output_models import (
    ReflectionSummaryOutput,
    ReportStructureItem,
    SearchOutput,
    SummaryOutput,
)


class TestSearchOutput:
    def test_required_fields(self):
        out = SearchOutput(
            search_query="舆情分析",
            search_tool="search_topic_globally",
            reasoning="全局搜索更全面",
        )
        assert out.search_query == "舆情分析"
        assert out.search_tool == "search_topic_globally"
        assert out.reasoning == "全局搜索更全面"

    def test_optional_fields_default_none(self):
        out = SearchOutput(
            search_query="q", search_tool="t", reasoning="r"
        )
        assert out.start_date is None
        assert out.end_date is None
        assert out.platform is None
        assert out.time_period is None

    def test_optional_fields_set(self):
        out = SearchOutput(
            search_query="q",
            search_tool="search_topic_by_date",
            reasoning="r",
            start_date="2026-01-01",
            end_date="2026-04-22",
            platform="weibo",
        )
        assert out.start_date == "2026-01-01"
        assert out.end_date == "2026-04-22"
        assert out.platform == "weibo"

    def test_missing_required_field_raises(self):
        with pytest.raises(Exception):
            SearchOutput(search_query="q")  # missing search_tool and reasoning

    def test_serialise_to_dict(self):
        out = SearchOutput(search_query="q", search_tool="t", reasoning="r")
        d = out.model_dump()
        assert set(d.keys()) >= {"search_query", "search_tool", "reasoning"}


class TestSummaryOutput:
    def test_basic(self):
        out = SummaryOutput(paragraph_latest_state="段落总结内容")
        assert out.paragraph_latest_state == "段落总结内容"

    def test_empty_string_allowed(self):
        out = SummaryOutput(paragraph_latest_state="")
        assert out.paragraph_latest_state == ""

    def test_missing_field_raises(self):
        with pytest.raises(Exception):
            SummaryOutput()


class TestReflectionSummaryOutput:
    def test_basic(self):
        out = ReflectionSummaryOutput(updated_paragraph_latest_state="更新后的总结")
        assert out.updated_paragraph_latest_state == "更新后的总结"


class TestReportStructureItem:
    def test_basic(self):
        item = ReportStructureItem(title="舆情背景", content="分析事件起源")
        assert item.title == "舆情背景"
        assert item.content == "分析事件起源"

    def test_list_of_items(self):
        items = [
            ReportStructureItem(title=f"第{i}段", content=f"内容{i}")
            for i in range(3)
        ]
        assert len(items) == 3
        assert items[0].title == "第0段"
