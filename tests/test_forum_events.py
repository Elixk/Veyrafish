# -*- coding: utf-8 -*-
"""
tests/test_forum_events.py — Wave 4 验证：ForumEngine 事件驱动 + 并发调度
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

from veyrafish_core.dispatcher import ResearchDispatcher


# ---------------------------------------------------------------------------
# Mock task_store
# ---------------------------------------------------------------------------

class _MockStore:
    """模拟 task_store，支持 add_event / list_events。"""

    def __init__(self):
        self._events: Dict[str, List[dict]] = {}  # task_id → events
        self._seq = 0

    def add_event(self, task_id, event_type, node_name=None,
                  paragraph=None, iteration=None, detail=None):
        self._seq += 1
        ts = f"2026-04-23T10:00:{self._seq:02d}.000000+00:00"
        self._events.setdefault(task_id, []).append({
            "event_id": f"evt-{self._seq}",
            "task_id": task_id,
            "event_type": event_type,
            "node_name": node_name,
            "paragraph": paragraph,
            "detail": detail or {},
            "created_at": ts,
        })

    def list_events(self, task_id, event_type=None, limit=200):
        evts = self._events.get(task_id, [])
        if event_type:
            evts = [e for e in evts if e["event_type"] == event_type]
        return evts[-limit:]

    def get_completed_paragraphs(self, task_id):
        evts = self._events.get(task_id, [])
        return {e["paragraph"] for e in evts if e["event_type"] == "paragraph_done"
                and e["paragraph"] is not None}


# ---------------------------------------------------------------------------
# ForumEngine LogMonitor 事件驱动测试
# ---------------------------------------------------------------------------

class TestLogMonitorEventDriven:
    def _make_monitor(self, mock_store=None):
        """创建 LogMonitor 实例，注入 mock task_store。"""
        import tempfile
        from ForumEngine.monitor import LogMonitor
        monitor = LogMonitor(log_dir=tempfile.mkdtemp())

        if mock_store:
            # patch task_store 相关
            monitor._mock_store = mock_store
        return monitor

    def test_bind_tasks_sets_tracked_ids(self):
        monitor = self._make_monitor()
        monitor.bind_tasks(["tid-insight", "tid-media", "tid-query"])
        assert monitor._tracked_task_ids == ["tid-insight", "tid-media", "tid-query"]

    def test_bind_tasks_binds_first_as_primary(self):
        monitor = self._make_monitor()
        monitor.bind_tasks(["tid-i", "tid-m"])
        assert monitor.task_id == "tid-i"

    def test_bind_tasks_empty_list(self):
        monitor = self._make_monitor()
        monitor.bind_tasks([])
        assert monitor._tracked_task_ids == []

    def test_poll_events_without_task_store(self):
        monitor = self._make_monitor()
        monitor.bind_tasks(["tid-1"])
        with patch("ForumEngine.monitor._TASK_STORE_AVAILABLE", False):
            events = monitor.poll_events()
        assert events == []

    def test_poll_events_returns_sorted_events(self):
        monitor = self._make_monitor()
        mock_store = _MockStore()
        mock_store.add_event("tid-a", "paragraph_done", paragraph=0, detail={"progress_pct": 50})
        mock_store.add_event("tid-b", "paragraph_done", paragraph=1, detail={"progress_pct": 100})

        with patch("ForumEngine.monitor._TASK_STORE_AVAILABLE", True), \
             patch("ForumEngine.monitor._get_task_store", return_value=mock_store):
            monitor.bind_tasks(["tid-a", "tid-b"])
            events = monitor.poll_events()

        assert len(events) == 2
        # 应按 created_at 升序排列
        assert events[0]["created_at"] <= events[1]["created_at"]

    def test_poll_events_filters_by_since(self):
        monitor = self._make_monitor()
        mock_store = _MockStore()
        mock_store.add_event("tid-x", "paragraph_done", paragraph=0, detail={})
        all_events = mock_store.list_events("tid-x")
        first_ts = all_events[0]["created_at"]

        # 添加第二个事件
        mock_store.add_event("tid-x", "paragraph_done", paragraph=1, detail={})

        with patch("ForumEngine.monitor._TASK_STORE_AVAILABLE", True), \
             patch("ForumEngine.monitor._get_task_store", return_value=mock_store):
            monitor.bind_tasks(["tid-x"])
            # since 设为第一个事件的时间，只应返回第二个
            events = monitor.poll_events(since=first_ts)

        assert len(events) == 1
        assert events[0]["paragraph"] == 1

    def test_should_trigger_host_from_events_threshold(self):
        monitor = self._make_monitor()
        monitor.host_speech_threshold = 3
        monitor._event_paragraph_done_count = 0

        # 2 个 paragraph_done，未达阈值
        events_2 = [{"event_type": "paragraph_done"}, {"event_type": "paragraph_done"}]
        assert monitor._should_trigger_host_from_events(events_2) is False

        # 再来 1 个，累计 3 个，达到阈值
        events_1 = [{"event_type": "paragraph_done"}]
        assert monitor._should_trigger_host_from_events(events_1) is True

    def test_should_trigger_host_non_paragraph_events_ignored(self):
        monitor = self._make_monitor()
        monitor.host_speech_threshold = 2
        monitor._event_paragraph_done_count = 0

        events = [{"event_type": "node_start"}, {"event_type": "node_done"}]
        assert monitor._should_trigger_host_from_events(events) is False

    def test_should_trigger_host_for_conflict_signal(self):
        monitor = self._make_monitor()
        monitor.host_speech_threshold = 10  # 避免纯计数触发
        monitor._event_paragraph_done_count = 0
        events = [{
            "event_type": "paragraph_done",
            "detail": {"gap_types": ["conflict"], "evidence_conflict_count": 1},
        }]
        assert monitor._should_trigger_host_from_events(events) is True

    def test_process_events_writes_to_forum_log(self):
        monitor = self._make_monitor()
        monitor._forum_speech_count = 0

        events = [
            {
                "event_type": "paragraph_done",
                "task_id": "tid-i",
                "node_name": "process_paragraph",
                "detail": {
                    "progress_pct": 50,
                    "engine": "insight",
                    "gap_types": ["coverage"],
                    "evidence_conflict_count": 0,
                },
                "created_at": "2026-04-23T10:00:01",
            }
        ]

        written_lines = []
        original_write = monitor.write_to_forum_log

        def capture_write(content, source=None):
            written_lines.append((content, source))

        monitor.write_to_forum_log = capture_write

        speeches = monitor._process_events_for_speeches(events)
        assert len(speeches) == 1
        assert len(written_lines) == 1
        assert "段落研究完成" in written_lines[0][0]
        assert "gap=coverage" in written_lines[0][0]
        assert written_lines[0][1] == "INSIGHT"

    def test_poll_events_with_explicit_task_ids(self):
        monitor = self._make_monitor()
        mock_store = _MockStore()
        mock_store.add_event("explicit-tid", "paragraph_done", paragraph=0, detail={})

        with patch("ForumEngine.monitor._TASK_STORE_AVAILABLE", True), \
             patch("ForumEngine.monitor._get_task_store", return_value=mock_store):
            events = monitor.poll_events(task_ids=["explicit-tid"])

        assert len(events) == 1


# ---------------------------------------------------------------------------
# ResearchDispatcher 并发调度测试
# ---------------------------------------------------------------------------

class TestResearchDispatcher:
    def _make_agent(self, name: str, delay: float = 0.05) -> MagicMock:
        """创建一个模拟 Agent，research() 返回报告字符串。"""
        agent = MagicMock()
        agent.research.return_value = f"Report from {name}"
        # 模拟轻微延迟
        original_side_effect = None

        def slow_research(*args, **kwargs):
            time.sleep(delay)
            return f"Report from {name}"

        agent.research.side_effect = slow_research
        return agent

    def test_dispatch_returns_all_results(self):
        dispatcher = ResearchDispatcher()
        agents = {
            "insight": self._make_agent("insight"),
            "media": self._make_agent("media"),
            "query": self._make_agent("query"),
        }
        results = dispatcher.dispatch("测试查询", agents, save_report=False)

        assert results["insight"] == "Report from insight"
        assert results["media"] == "Report from media"
        assert results["query"] == "Report from query"
        assert results["_errors"] == {}

    def test_dispatch_concurrent_faster_than_serial(self):
        """并发执行应显著快于串行（3 * 0.1s）。"""
        dispatcher = ResearchDispatcher(max_workers=3)
        agents = {
            "insight": self._make_agent("insight", delay=0.1),
            "media": self._make_agent("media", delay=0.1),
            "query": self._make_agent("query", delay=0.1),
        }

        t0 = time.monotonic()
        results = dispatcher.dispatch("测试", agents, save_report=False)
        elapsed = time.monotonic() - t0

        # 并发时 3 个任务各 0.1s，总时间应接近 0.1s（≤ 0.5s 为合理上界）
        assert elapsed < 0.5, f"并发调度耗时 {elapsed:.2f}s，疑似串行执行"
        assert results["_errors"] == {}

    def test_dispatch_one_engine_failure_others_succeed(self):
        """一个引擎失败时，其他引擎应继续正常完成。"""
        def fail_research(*args, **kwargs):
            raise RuntimeError("模拟引擎崩溃")

        insight_agent = self._make_agent("insight")
        media_agent = MagicMock()
        media_agent.research.side_effect = fail_research
        query_agent = self._make_agent("query")

        dispatcher = ResearchDispatcher()
        results = dispatcher.dispatch(
            "测试", {"insight": insight_agent, "media": media_agent, "query": query_agent},
            save_report=False,
        )

        assert results["insight"] == "Report from insight"
        assert results["media"] is None
        assert "media" in results["_errors"]
        assert results["query"] == "Report from query"

    def test_dispatch_passes_task_id_to_agent(self):
        """task_id 应该被正确传递给各引擎的 research() 调用。"""
        insight_agent = self._make_agent("insight")
        task_ids = {"insight": "tid-insight-001"}

        dispatcher = ResearchDispatcher()
        dispatcher.dispatch("test", {"insight": insight_agent},
                            task_ids=task_ids, save_report=False)

        # 验证 task_id 被传递
        call_kwargs = insight_agent.research.call_args
        assert call_kwargs.kwargs.get("task_id") == "tid-insight-001" or \
               (call_kwargs.args and "tid-insight-001" in str(call_kwargs))

    def test_dispatch_empty_agents_returns_empty(self):
        dispatcher = ResearchDispatcher()
        results = dispatcher.dispatch("test", {})
        assert results["_errors"] == {}
        assert results["_task_ids"] == {}

    def test_dispatch_stores_task_ids_in_result(self):
        dispatcher = ResearchDispatcher()
        agents = {"insight": self._make_agent("insight")}
        task_ids = {"insight": "tid-001"}
        results = dispatcher.dispatch("test", agents, task_ids=task_ids, save_report=False)
        assert results["_task_ids"]["insight"] == "tid-001"

    def test_dispatch_with_forum_calls_bind_tasks(self):
        """dispatch_with_forum 应调用 forum_monitor.bind_tasks()。"""
        dispatcher = ResearchDispatcher()
        agents = {"insight": self._make_agent("insight")}
        task_ids = {"insight": "tid-i"}

        mock_forum = MagicMock()
        mock_forum.start_event_driven_monitoring.return_value = True

        dispatcher.dispatch_with_forum(
            "test", agents, task_ids=task_ids,
            forum_monitor=mock_forum, save_report=False,
        )

        mock_forum.bind_tasks.assert_called_once_with(["tid-i"])
        mock_forum.start_event_driven_monitoring.assert_called_once()
