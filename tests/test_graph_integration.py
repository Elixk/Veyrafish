# -*- coding: utf-8 -*-
"""
tests/test_graph_integration.py — Wave 3 验证：BaseResearchAgent 图谱化迁移

使用 stub 子类模拟研究流程，验证：
1. 图执行路径（USE_GRAPH_ENGINE=True）的正确性
2. 旧路径（USE_GRAPH_ENGINE=False）的向后兼容性
3. 段落循环执行正确次数
4. 断点恢复（skip_indices）有效
5. task_events 通过 _emit 写入（不通过 GraphRunner）
6. 子类可以 override _build_graph
"""

from __future__ import annotations

import os
import tempfile
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

from veyrafish_core.base_research_agent import BaseResearchAgent
from veyrafish_core.graph import DictGraphState, GraphRunner, StateGraph
from veyrafish_core.skills._models import (
    EvidenceExtractOutput,
    ExtractedEvidence,
    GapFinderOutput,
    QualityGateOutput,
    QueryRewriteOutput,
    ResearchGap,
    SummarizeOutput,
)


# ---------------------------------------------------------------------------
# Stub：最小化 Config
# ---------------------------------------------------------------------------

class _StubConfig:
    OUTPUT_DIR = tempfile.mkdtemp()
    MAX_REFLECTIONS = 1
    SAVE_INTERMEDIATE_STATES = False


# ---------------------------------------------------------------------------
# Stub：段落 / 研究状态
# ---------------------------------------------------------------------------

class _StubResearch:
    def __init__(self):
        self.latest_summary = ""
        self._completed = False
        self.reflection_iteration = 0

    def add_search_results(self, query, results):
        self.latest_summary = f"summary_for_{query}"

    def increment_reflection(self):
        self.reflection_iteration += 1

    def mark_completed(self):
        self._completed = True

    @property
    def is_completed(self):
        return self._completed


class _StubParagraph:
    def __init__(self, title: str):
        self.title = title
        self.content = f"content of {title}"
        self.research = _StubResearch()


class _StubState:
    def __init__(self, paragraphs=None):
        self.paragraphs: List[_StubParagraph] = paragraphs or []
        self.query = ""
        self.report_title = "Test Report"
        self.final_report = ""

    def get_progress_summary(self):
        return {}

    def mark_completed(self):
        pass

    def save_to_file(self, path):
        pass


# ---------------------------------------------------------------------------
# Stub：ReportStructureNode
# ---------------------------------------------------------------------------

class _StubReportStructureNode:
    def __init__(self, llm_client, query, num_paragraphs=2):
        self._query = query
        self._n = num_paragraphs

    def mutate_state(self, state):
        state.query = self._query
        state.paragraphs = [_StubParagraph(f"Para {i+1}") for i in range(self._n)]
        return state


# ---------------------------------------------------------------------------
# Stub：各类 Node
# ---------------------------------------------------------------------------

class _StubFirstSearchNode:
    def run(self, input_data):
        return {"search_query": f"query_{input_data['title']}", "search_tool": "basic_search"}


class _StubFirstSummaryNode:
    def mutate_state(self, input_data, state, paragraph_index):
        state.paragraphs[paragraph_index].research.latest_summary = (
            f"first_summary_{input_data['search_query']}"
        )
        return state


class _StubReflectionNode:
    def run(self, input_data):
        return {"search_query": f"reflect_{input_data['title']}", "search_tool": "basic_search"}


class _StubReflectionSummaryNode:
    def mutate_state(self, input_data, state, paragraph_index):
        state.paragraphs[paragraph_index].research.latest_summary = (
            f"reflected_{input_data['search_query']}"
        )
        return state


class _StubReportFormattingNode:
    def run(self, report_data):
        return "# Final Report\n" + "\n".join(
            f"## {item['title']}\n{item['paragraph_latest_state']}"
            for item in report_data
        )

    def format_report_manually(self, report_data, title):
        return f"# {title}\nManual"


# ---------------------------------------------------------------------------
# StubAgent：继承 BaseResearchAgent 的最小实现
# ---------------------------------------------------------------------------

class _StubAgent(BaseResearchAgent):
    """最小化 stub，完全不依赖 LLM / 搜索 API。"""

    def __init__(self, num_paragraphs: int = 2, use_graph: bool = True):
        self._num_paragraphs = num_paragraphs
        self.USE_GRAPH_ENGINE = use_graph
        super().__init__(config=_StubConfig())

    # ------------------------------------------------------------------
    # 抽象方法实现
    # ------------------------------------------------------------------

    def _initialize_llm(self) -> Any:
        return None

    def _initialize_search_agency(self) -> Any:
        return MagicMock()

    def _initialize_nodes(self) -> None:
        self.first_search_node = _StubFirstSearchNode()
        self.first_summary_node = _StubFirstSummaryNode()
        self.reflection_node = _StubReflectionNode()
        self.reflection_summary_node = _StubReflectionSummaryNode()
        self.report_formatting_node = _StubReportFormattingNode()
        self._report_structure_node_class = _make_struct_node_class(self._num_paragraphs)

    def _create_initial_state(self) -> _StubState:
        return _StubState()

    def execute_search_tool(self, tool_name: str, query: str, **kwargs) -> Any:
        return {"results": [{"title": "result", "content": f"content_{query}"}]}

    def _normalize_search_response(self, response: Any) -> List[dict]:
        return [
            {
                "title": r["title"],
                "url": "",
                "content": r["content"],
                "score": 0.9,
                "raw_content": r["content"],
                "published_date": "",
            }
            for r in response.get("results", [])
        ]

    def _get_content_max_length(self) -> int:
        return 1000


def _make_struct_node_class(num_paragraphs: int):
    """工厂：创建一个返回指定段落数的 ReportStructureNode 类。"""
    class _NodeClass(_StubReportStructureNode):
        def __init__(self, llm_client, query):
            super().__init__(llm_client, query, num_paragraphs=num_paragraphs)
    return _NodeClass


# ---------------------------------------------------------------------------
# 测试：图执行路径
# ---------------------------------------------------------------------------

class TestResearchViaGraph:
    def test_graph_execution_returns_string(self):
        agent = _StubAgent(num_paragraphs=2, use_graph=True)
        result = agent.research("测试查询", save_report=False)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_graph_processes_all_paragraphs(self):
        agent = _StubAgent(num_paragraphs=3, use_graph=True)
        agent.research("测试", save_report=False)
        # 所有段落应标记为已完成
        for p in agent.state.paragraphs:
            assert p.research.is_completed, f"段落 '{p.title}' 未标记为完成"

    def test_graph_report_contains_paragraph_titles(self):
        agent = _StubAgent(num_paragraphs=2, use_graph=True)
        report = agent.research("Veyrafish测试", save_report=False)
        assert "Para 1" in report
        assert "Para 2" in report

    def test_graph_skips_completed_paragraphs(self):
        """断点恢复：skip_indices={0} 时段落 0 不应被处理。"""
        agent = _StubAgent(num_paragraphs=2, use_graph=True)
        # 先触发 _generate_report_structure，让 state.paragraphs 初始化
        agent._generate_report_structure("test")
        # 重置以模拟中断后恢复
        agent._create_initial_state()
        agent.state = _StubState()

        result = agent.research("test", save_report=False, skip_paragraph_indices={0})
        assert isinstance(result, str)
        # 段落 0 被跳过，应通过 mark_completed（在 skip 路径调用）
        assert agent.state.paragraphs[0].research.is_completed

    def test_graph_execution_without_task_id(self):
        agent = _StubAgent(use_graph=True)
        result = agent.research("no_task_id", save_report=False, task_id=None)
        assert isinstance(result, str)

    def test_graph_with_task_id_emits_events(self):
        """验证 _emit 调用了 task_store（而不是 GraphRunner）。"""
        agent = _StubAgent(use_graph=True)

        emitted = []
        original_emit = agent._emit.__func__

        def mock_emit(self, task_id, event_type, **kwargs):
            emitted.append(event_type)

        with patch.object(type(agent), '_emit', mock_emit):
            agent.research("test_emit", save_report=False, task_id="tid-test")

        assert "research_start" in emitted
        assert "research_done" in emitted
        assert "paragraph_start" in emitted
        assert "paragraph_done" in emitted


# ---------------------------------------------------------------------------
# 测试：旧路径向后兼容
# ---------------------------------------------------------------------------

class TestResearchLegacy:
    def test_legacy_returns_string(self):
        agent = _StubAgent(num_paragraphs=2, use_graph=False)
        result = agent.research("legacy test", save_report=False)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_legacy_processes_all_paragraphs(self):
        agent = _StubAgent(num_paragraphs=2, use_graph=False)
        agent.research("legacy test", save_report=False)
        for p in agent.state.paragraphs:
            assert p.research.is_completed

    def test_legacy_and_graph_produce_equivalent_output(self):
        """图执行路径和旧路径的输出格式应等价（都包含段落标题）。"""
        agent_graph = _StubAgent(num_paragraphs=2, use_graph=True)
        agent_legacy = _StubAgent(num_paragraphs=2, use_graph=False)

        report_graph = agent_graph.research("同一查询", save_report=False)
        report_legacy = agent_legacy.research("同一查询", save_report=False)

        # 两者都应包含段落标题
        for title in ["Para 1", "Para 2"]:
            assert title in report_graph, f"图路径报告缺少 {title}"
            assert title in report_legacy, f"旧路径报告缺少 {title}"


# ---------------------------------------------------------------------------
# 测试：research_with_resume
# ---------------------------------------------------------------------------

class TestResearchWithResume:
    def test_resume_without_task_store(self):
        """没有 task_store 时应该从头开始（skip_indices 为空）。"""
        agent = _StubAgent(num_paragraphs=2, use_graph=True)
        # 直接调用 research_with_resume，应该正常执行（不崩溃）
        with patch("veyrafish_core.base_research_agent._TASK_STORE_AVAILABLE", False):
            result = agent.research_with_resume("test", task_id="tid-resume", save_report=False)
        assert isinstance(result, str)

    def test_resume_skips_completed_paragraphs_via_task_store(self):
        """task_store.get_completed_paragraphs 返回 {0} 时段落 0 被跳过。"""
        agent = _StubAgent(num_paragraphs=2, use_graph=True)

        mock_store = MagicMock()
        mock_store.get_completed_paragraphs.return_value = {0}

        with patch("veyrafish_core.base_research_agent._TASK_STORE_AVAILABLE", True), \
             patch("veyrafish_core.base_research_agent._get_task_store", return_value=mock_store):
            result = agent.research_with_resume("test resume", task_id="tid-resume-2", save_report=False)

        assert isinstance(result, str)
        mock_store.get_completed_paragraphs.assert_called_once_with("tid-resume-2")

    def test_resume_uses_graph_runner_resume(self):
        """图模式断点恢复应进入 GraphRunner.resume，而不是普通 run。"""
        agent = _StubAgent(num_paragraphs=2, use_graph=True)

        with patch(
            "veyrafish_core.base_research_agent.GraphRunner.resume",
            autospec=True,
            wraps=GraphRunner.resume,
        ) as resume_mock:
            result = agent.research_with_resume(
                "test graph resume",
                task_id="tid-resume-graph",
                save_report=False,
            )

        assert isinstance(result, str)
        assert resume_mock.called


# ---------------------------------------------------------------------------
# 测试：_build_graph 可 override
# ---------------------------------------------------------------------------

class TestCustomGraph:
    def test_subclass_can_override_build_graph(self):
        """子类可以 override _build_graph() 并添加额外节点。"""
        extra_executed = []

        class _CustomAgent(_StubAgent):
            def _build_graph(self) -> StateGraph:
                g = super()._build_graph()
                return g  # 这里可以再 add_node / add_edge

            def _extra_hook(self):
                extra_executed.append("called")

        agent = _CustomAgent(num_paragraphs=1, use_graph=True)
        result = agent.research("custom graph test", save_report=False)
        assert isinstance(result, str)

    def test_use_graph_engine_false_uses_legacy(self):
        """USE_GRAPH_ENGINE=False 时明确走旧路径。"""
        agent = _StubAgent(num_paragraphs=2, use_graph=False)
        assert agent.USE_GRAPH_ENGINE is False
        result = agent.research("legacy check", save_report=False)
        assert isinstance(result, str)
        assert "Para 1" in result


class _FakeSkillRegistry:
    def __init__(self):
        self.calls: List[str] = []

    def has(self, name: str) -> bool:
        return name in {"query_rewrite", "llm_summarize", "quality_gate", "evidence_extract", "gap_finder"}

    def execute(self, name: str, input_data: Any, ctx: Any) -> Any:
        self.calls.append(name)
        if name == "query_rewrite":
            return QueryRewriteOutput(
                rewritten_query=f"skill_{input_data.original_query}",
                search_tool=input_data.search_tools_available[0],
                reasoning="skill_rewrite",
                selection_rule="test_rule",
            )
        if name == "llm_summarize":
            if input_data.mode == "reflection_summary":
                return SummarizeOutput(summary="skill_reflection_summary", confidence=0.8)
            return SummarizeOutput(summary="skill_first_summary", confidence=0.8)
        if name == "quality_gate":
            return QualityGateOutput(
                passed=True,
                score=0.9,
                content_type_used="summary",
                criteria_used=["内容不为空"],
            )
        if name == "evidence_extract":
            return EvidenceExtractOutput(
                evidences=[
                    ExtractedEvidence(
                        claim="skill_evidence_claim",
                        supporting_text="skill_evidence_support",
                        confidence=0.7,
                    )
                ]
            )
        if name == "gap_finder":
            return GapFinderOutput(
                gaps=[
                    ResearchGap(
                        description="覆盖度较好，仅建议补充边缘信息",
                        suggested_query="补充检索",
                        gap_type="coverage",
                        priority="low",
                    )
                ],
                conflict_notes=[],
                overall_coverage="覆盖度较好",
            )
        raise KeyError(name)


class TestWave25SkillIntegration:
    def test_initial_and_reflection_summary_prefer_skill_registry(self):
        fake_registry = _FakeSkillRegistry()
        with patch("veyrafish_core.base_research_agent._DEFAULT_SKILL_REGISTRY", fake_registry):
            agent = _StubAgent(num_paragraphs=1, use_graph=True)
            agent._generate_report_structure("skill integration")
            agent._initial_search_and_summary(0, task_id="tid-skill")
            assert agent.state.paragraphs[0].research.latest_summary == "skill_first_summary"

            agent._reflection_loop(0, task_id="tid-skill")
            assert agent.state.paragraphs[0].research.latest_summary == "skill_reflection_summary"
            assert agent.state.paragraphs[0].research.reflection_iteration == 1
            assert "query_rewrite" in fake_registry.calls
            assert "llm_summarize" in fake_registry.calls
            assert "quality_gate" in fake_registry.calls
            assert "gap_finder" in fake_registry.calls

    def test_evidence_sink_prefers_evidence_extract_skill(self):
        fake_registry = _FakeSkillRegistry()
        with patch("veyrafish_core.base_research_agent._DEFAULT_SKILL_REGISTRY", fake_registry):
            agent = _StubAgent(num_paragraphs=1, use_graph=True)
            evidences = agent._extract_evidences_from_summary(
                summary="这是一个用于测试的总结内容，长度足够触发证据提取。",
                paragraph_index=0,
                task_id="tid-evidence",
            )
        assert evidences
        assert evidences[0].claim == "skill_evidence_claim"
        assert "evidence_extract" in fake_registry.calls

    def test_reflection_gap_conflict_adds_conservative_note(self):
        class _ConflictGapRegistry(_FakeSkillRegistry):
            def execute(self, name: str, input_data: Any, ctx: Any) -> Any:
                if name == "gap_finder":
                    self.calls.append(name)
                    return GapFinderOutput(
                        gaps=[
                            ResearchGap(
                                description="不同来源存在冲突",
                                suggested_query="权威来源 交叉验证",
                                gap_type="conflict",
                                priority="high",
                            )
                        ],
                        conflict_notes=["检测到冲突"],
                        overall_coverage="覆盖度一般",
                    )
                return super().execute(name, input_data, ctx)

        fake_registry = _ConflictGapRegistry()
        with patch("veyrafish_core.base_research_agent._DEFAULT_SKILL_REGISTRY", fake_registry):
            agent = _StubAgent(num_paragraphs=1, use_graph=True)
            agent._generate_report_structure("skill integration")
            agent._initial_search_and_summary(0, task_id="tid-skill")
            agent._reflection_loop(0, task_id="tid-skill")

        final_summary = agent.state.paragraphs[0].research.latest_summary
        assert "审慎说明" in final_summary
        assert "gap_finder" in fake_registry.calls
