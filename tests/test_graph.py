# -*- coding: utf-8 -*-
"""
tests/test_graph.py — Wave 1 验证：StateGraph + GraphRunner + GraphState
"""

import pytest
from veyrafish_core.graph import (
    DictGraphState,
    GraphRunner,
    GraphState,
    StateGraph,
)


# ---------------------------------------------------------------------------
# 辅助：简单的节点函数
# ---------------------------------------------------------------------------

def _inc(state: DictGraphState) -> DictGraphState:
    """将 state.count 加 1。"""
    state.count = (state.count or 0) + 1
    return state


def _append_a(state: DictGraphState) -> DictGraphState:
    state.path = (state.path or "") + "A"
    return state


def _append_b(state: DictGraphState) -> DictGraphState:
    state.path = (state.path or "") + "B"
    return state


def _append_c(state: DictGraphState) -> DictGraphState:
    state.path = (state.path or "") + "C"
    return state


def _raise_error(state: DictGraphState) -> DictGraphState:
    raise RuntimeError("模拟节点失败")


# ---------------------------------------------------------------------------
# DictGraphState
# ---------------------------------------------------------------------------

class TestDictGraphState:
    def test_set_and_get_attr(self):
        s = DictGraphState(count=0)
        s.count = 5
        assert s.count == 5

    def test_get_missing_attr_returns_none(self):
        s = DictGraphState()
        assert s.nonexistent is None

    def test_to_dict_round_trip(self):
        s = DictGraphState(x=1, y="hello", z=[1, 2, 3])
        restored = DictGraphState.from_dict(s.to_dict())
        assert restored.x == 1
        assert restored.y == "hello"
        assert restored.z == [1, 2, 3]

    def test_copy_is_independent(self):
        s = DictGraphState(count=10)
        s2 = s.copy()
        s2.count = 99
        assert s.count == 10

    def test_update(self):
        s = DictGraphState(a=1)
        s.update(b=2, c=3)
        assert s.b == 2
        assert s.c == 3

    def test_get_with_default(self):
        s = DictGraphState()
        assert s.get("missing", "default") == "default"


# ---------------------------------------------------------------------------
# StateGraph — 图构建
# ---------------------------------------------------------------------------

class TestStateGraphBuild:
    def _make_linear_graph(self) -> StateGraph:
        g = StateGraph("linear")
        g.add_node("A", _append_a)
        g.add_node("B", _append_b)
        g.add_node("C", _append_c)
        g.set_entry("A")
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.set_finish("C")
        return g

    def test_add_duplicate_node_raises(self):
        g = StateGraph("test")
        g.add_node("X", _append_a)
        with pytest.raises(ValueError, match="已存在"):
            g.add_node("X", _append_b)

    def test_node_names(self):
        g = self._make_linear_graph()
        assert set(g.node_names()) == {"A", "B", "C"}

    def test_validate_valid_graph(self):
        g = self._make_linear_graph()
        errors = g.validate()
        assert errors == [], f"不应有错误：{errors}"

    def test_validate_missing_entry(self):
        g = StateGraph("test")
        g.add_node("A", _append_a)
        g.set_finish("A")
        errors = g.validate()
        assert any("入口节点" in e for e in errors)

    def test_validate_missing_finish(self):
        g = StateGraph("test")
        g.add_node("A", _append_a)
        g.set_entry("A")
        errors = g.validate()
        assert any("终止节点" in e for e in errors)

    def test_validate_unregistered_entry(self):
        g = StateGraph("test")
        g.add_node("A", _append_a)
        g.set_entry("GHOST")
        g.set_finish("A")
        errors = g.validate()
        assert any("GHOST" in e for e in errors)

    def test_validate_dangling_edge_target(self):
        g = StateGraph("test")
        g.add_node("A", _append_a)
        g.set_entry("A")
        g.set_finish("A")
        g.add_edge("A", "GHOST")
        errors = g.validate()
        assert any("GHOST" in e for e in errors)

    def test_validate_conditional_edge_unknown_target(self):
        g = StateGraph("test")
        g.add_node("A", _append_a)
        g.add_node("B", _append_b)
        g.set_entry("A")
        g.set_finish("B")
        g.add_conditional_edge("A", lambda s: "go", targets={"go": "GHOST"})
        errors = g.validate()
        assert any("GHOST" in e for e in errors)

    def test_to_mermaid_contains_nodes(self):
        g = self._make_linear_graph()
        mermaid = g.to_mermaid()
        assert "graph TD" in mermaid
        assert "A" in mermaid
        assert "B" in mermaid
        assert "C" in mermaid

    def test_to_mermaid_conditional_edge(self):
        g = StateGraph("cond")
        g.add_node("A", _append_a)
        g.add_node("B", _append_b)
        g.add_node("C", _append_c)
        g.set_entry("A")
        g.set_finish("C")
        g.add_conditional_edge("A", lambda s: "left", targets={"left": "B", "right": "C"})
        g.add_edge("B", "C")
        mermaid = g.to_mermaid()
        assert "left" in mermaid
        assert "right" in mermaid


# ---------------------------------------------------------------------------
# GraphRunner — 图执行
# ---------------------------------------------------------------------------

class TestGraphRunnerLinear:
    def _make_runner(self) -> GraphRunner:
        g = StateGraph("linear")
        g.add_node("A", _append_a)
        g.add_node("B", _append_b)
        g.add_node("C", _append_c)
        g.set_entry("A")
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.set_finish("C")
        return GraphRunner(g)

    def test_linear_execution_result(self):
        runner = self._make_runner()
        final = runner.run(DictGraphState(path=""))
        assert final.path == "ABC"

    def test_run_without_task_store(self):
        runner = self._make_runner()
        final = runner.run(DictGraphState(path=""), task_id=None)
        assert final.path == "ABC"

    def test_runner_rejects_invalid_graph(self):
        g = StateGraph("bad")
        g.add_node("A", _append_a)
        # 故意不设 entry/finish
        with pytest.raises(ValueError, match="验证失败"):
            GraphRunner(g)


class TestGraphRunnerConditional:
    def _make_loop_graph(self, limit: int = 3) -> tuple[StateGraph, GraphRunner]:
        """构造一个循环图：process_paragraph × limit 次后结束。"""
        def process(state: DictGraphState) -> DictGraphState:
            state.count = (state.count or 0) + 1
            state.path = (state.path or "") + "P"
            return state

        def has_more(state: DictGraphState) -> str:
            return "more" if (state.count or 0) < limit else "done"

        g = StateGraph("loop")
        g.add_node("process", process)
        g.add_node("finish", _append_c)
        g.set_entry("process")
        g.add_conditional_edge("process", has_more, targets={"more": "process", "done": "finish"})
        g.set_finish("finish")
        return g, GraphRunner(g)

    def test_loop_executes_correct_times(self):
        _, runner = self._make_loop_graph(limit=4)
        final = runner.run(DictGraphState(count=0, path=""))
        assert final.count == 4
        assert final.path == "PPPP" + "C"

    def test_conditional_branch_false_path(self):
        """count 已经 >= limit，直接走 done 分支。"""
        _, runner = self._make_loop_graph(limit=2)
        # 初始 count=2，第一次条件判断就应走 done
        final = runner.run(DictGraphState(count=2, path=""))
        assert final.count == 3    # process 还是要执行一次（先执行节点，再评估条件）
        assert "C" in final.path

    def test_unknown_condition_key_raises(self):
        def bad_condition(state: DictGraphState) -> str:
            return "unknown_key"

        g = StateGraph("bad_cond")
        g.add_node("A", _append_a)
        g.add_node("B", _append_b)
        g.set_entry("A")
        g.set_finish("B")
        g.add_conditional_edge("A", bad_condition, targets={"left": "B"})
        runner = GraphRunner(g)
        with pytest.raises(RuntimeError, match="unknown_key"):
            runner.run(DictGraphState())


class TestGraphRunnerExceptionAndCheckpoint:
    def test_node_failure_raises(self):
        g = StateGraph("err")
        g.add_node("start", _append_a)
        g.add_node("fail", _raise_error)
        g.add_node("end", _append_b)
        g.set_entry("start")
        g.add_edge("start", "fail")
        g.add_edge("fail", "end")
        g.set_finish("end")
        runner = GraphRunner(g)
        with pytest.raises(RuntimeError, match="模拟节点失败"):
            runner.run(DictGraphState(path=""))

    def test_max_steps_protection(self):
        """图中存在真正死循环时，max_steps 应截断执行。"""
        def always_loop(state: DictGraphState) -> str:
            return "loop"

        g = StateGraph("infinite")
        g.add_node("A", _inc)
        g.add_node("B", _append_b)
        g.set_entry("A")
        g.set_finish("B")
        g.add_conditional_edge("A", always_loop, targets={"loop": "A"})
        runner = GraphRunner(g, max_steps=10)
        with pytest.raises(RuntimeError, match="步数超过上限"):
            runner.run(DictGraphState(count=0))


class TestGraphRunnerResume:
    def test_resume_from_middle_node(self):
        g = StateGraph("resume_test")
        g.add_node("A", _append_a)
        g.add_node("B", _append_b)
        g.add_node("C", _append_c)
        g.set_entry("A")
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.set_finish("C")
        runner = GraphRunner(g)

        # 模拟：A 已经执行完（path="A"），从 B 恢复
        state = DictGraphState(path="A")
        final = runner.resume(state, from_node="B")
        assert final.path == "ABC"

    def test_resume_from_unknown_node_raises(self):
        g = StateGraph("r")
        g.add_node("A", _append_a)
        g.set_entry("A")
        g.set_finish("A")
        runner = GraphRunner(g)
        with pytest.raises(ValueError, match="未在图"):
            runner.resume(DictGraphState(), from_node="GHOST")


class TestGraphRunnerTaskStore:
    """验证 task_store 事件写入逻辑（使用 mock store）。"""

    class _MockStore:
        def __init__(self):
            self.events = []

        def add_event(self, task_id, event_type, node_name=None, detail=None, **kwargs):
            self.events.append({"task_id": task_id, "event_type": event_type, "node_name": node_name})

        def update_task(self, task_id, status, result=None):
            self.events.append({"task_id": task_id, "status": status})

    def test_events_emitted_for_each_node(self):
        g = StateGraph("evt")
        g.add_node("A", _append_a)
        g.add_node("B", _append_b)
        g.set_entry("A")
        g.add_edge("A", "B")
        g.set_finish("B")

        mock_store = self._MockStore()
        runner = GraphRunner(g, task_store=mock_store)
        runner.run(DictGraphState(path=""), task_id="tid-001")

        event_types = [e["event_type"] for e in mock_store.events]
        assert "node_start" in event_types
        assert "node_done" in event_types
        # 每个节点应有一对 start/done
        assert event_types.count("node_start") == 2
        assert event_types.count("node_done") == 2

    def test_error_event_emitted_on_failure(self):
        g = StateGraph("err_evt")
        g.add_node("ok", _append_a)
        g.add_node("bad", _raise_error)
        g.set_entry("ok")
        g.add_edge("ok", "bad")
        g.set_finish("bad")

        mock_store = self._MockStore()
        runner = GraphRunner(g, task_store=mock_store)
        with pytest.raises(RuntimeError):
            runner.run(DictGraphState(), task_id="tid-002")

        event_types = [e.get("event_type") for e in mock_store.events]
        assert "error" in event_types

    def test_run_without_task_id_no_events(self):
        g = StateGraph("no_tid")
        g.add_node("A", _append_a)
        g.set_entry("A")
        g.set_finish("A")

        mock_store = self._MockStore()
        runner = GraphRunner(g, task_store=mock_store)
        runner.run(DictGraphState(path=""), task_id=None)

        assert len(mock_store.events) == 0
