# -*- coding: utf-8 -*-
"""
tests/test_task_store.py

TaskStore 单元测试。
覆盖：create / update / get / list / cleanup_stale_tasks 五个核心操作，
以及 JSON 字段序列化、多任务并存、跨实例持久性。
"""

import os
import sys
import tempfile
import time

import pytest

# 确保从项目根目录导入
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))

from task_store import TaskStore


# ------------------------------------------------------------------
# Fixture
# ------------------------------------------------------------------

@pytest.fixture
def tmp_db():
    """每个测试用独立的临时 SQLite 文件，避免依赖 pytest tmp_path 目录 ACL。"""
    return tempfile.mktemp(suffix="_test_tasks.db")


@pytest.fixture
def store(tmp_db):
    """返回一个干净的 TaskStore 实例。"""
    return TaskStore(db_path=tmp_db)


# ------------------------------------------------------------------
# 基础 CRUD
# ------------------------------------------------------------------

class TestCreateTask:
    def test_returns_nonempty_uuid(self, store):
        tid = store.create_task("system_start")
        assert isinstance(tid, str) and len(tid) == 36  # uuid4 格式

    def test_initial_status_is_starting(self, store):
        tid = store.create_task("system_start")
        task = store.get_task(tid)
        assert task["status"] == "starting"

    def test_payload_stored_and_deserialized(self, store):
        tid = store.create_task("system_start", payload={"key": "value", "num": 42})
        task = store.get_task(tid)
        assert task["payload"]["key"] == "value"
        assert task["payload"]["num"] == 42

    def test_empty_payload_defaults_to_dict(self, store):
        tid = store.create_task("test_type")
        task = store.get_task(tid)
        assert isinstance(task["payload"], dict)

    def test_created_at_and_updated_at_set(self, store):
        tid = store.create_task("system_start")
        task = store.get_task(tid)
        assert task["created_at"]
        assert task["updated_at"]
        assert task["created_at"] == task["updated_at"]


class TestUpdateTask:
    def test_status_changes_to_running(self, store):
        tid = store.create_task("system_start")
        store.update_task(tid, "running")
        assert store.get_task(tid)["status"] == "running"

    def test_status_changes_to_completed_with_result(self, store):
        tid = store.create_task("system_start")
        store.update_task(tid, "completed", result={"logs": ["ok"]})
        task = store.get_task(tid)
        assert task["status"] == "completed"
        assert task["result"]["logs"] == ["ok"]

    def test_status_changes_to_error_with_message(self, store):
        tid = store.create_task("system_start")
        store.update_task(tid, "error", result={"error": "timeout"})
        task = store.get_task(tid)
        assert task["status"] == "error"
        assert task["result"]["error"] == "timeout"

    def test_updated_at_advances(self, store):
        tid = store.create_task("system_start")
        task_before = store.get_task(tid)
        time.sleep(1.1)  # 保证时间戳不同（精确到秒）
        store.update_task(tid, "running")
        task_after = store.get_task(tid)
        assert task_after["updated_at"] >= task_before["updated_at"]

    def test_result_not_overwritten_when_none(self, store):
        tid = store.create_task("system_start")
        store.update_task(tid, "completed", result={"data": 1})
        store.update_task(tid, "completed")  # result=None → 不覆盖
        task = store.get_task(tid)
        assert task["result"]["data"] == 1


class TestGetTask:
    def test_returns_none_for_nonexistent_id(self, store):
        assert store.get_task("no-such-id") is None

    def test_returns_dict(self, store):
        tid = store.create_task("system_start")
        task = store.get_task(tid)
        assert isinstance(task, dict)
        for key in ("task_id", "task_type", "status", "created_at", "updated_at"):
            assert key in task


class TestListTasks:
    def test_empty_list_when_no_tasks(self, store):
        assert store.list_tasks() == []

    def test_returns_all_tasks_up_to_limit(self, store):
        for i in range(5):
            store.create_task("system_start", payload={"i": i})
        tasks = store.list_tasks(limit=3)
        assert len(tasks) == 3

    def test_ordered_by_created_at_desc(self, store):
        ids = []
        for _ in range(3):
            ids.append(store.create_task("system_start"))
            time.sleep(1.05)  # created_at 精确到秒，需保证时间戳不同
        tasks = store.list_tasks()
        # 最新创建的应排第一
        assert tasks[0]["task_id"] == ids[-1]

    def test_filter_by_task_type(self, store):
        store.create_task("system_start")
        store.create_task("other_type")
        tasks = store.list_tasks(task_type="system_start")
        assert all(t["task_type"] == "system_start" for t in tasks)
        assert len(tasks) == 1

    def test_returns_all_types_when_no_filter(self, store):
        store.create_task("system_start")
        store.create_task("other_type")
        assert len(store.list_tasks()) == 2


# ------------------------------------------------------------------
# cleanup_stale_tasks
# ------------------------------------------------------------------

class TestCleanupStaleTasks:
    def test_marks_starting_as_error(self, store):
        tid = store.create_task("system_start")
        count = store.cleanup_stale_tasks()
        assert count == 1
        assert store.get_task(tid)["status"] == "error"

    def test_marks_running_as_error(self, store):
        tid = store.create_task("system_start")
        store.update_task(tid, "running")
        count = store.cleanup_stale_tasks()
        assert count == 1
        assert store.get_task(tid)["status"] == "error"

    def test_does_not_touch_completed(self, store):
        tid = store.create_task("system_start")
        store.update_task(tid, "completed", result={"ok": True})
        count = store.cleanup_stale_tasks()
        assert count == 0
        assert store.get_task(tid)["status"] == "completed"

    def test_does_not_touch_existing_error(self, store):
        tid = store.create_task("system_start")
        store.update_task(tid, "error", result={"error": "previous"})
        count = store.cleanup_stale_tasks()
        assert count == 0

    def test_cleans_multiple_stale_tasks(self, store):
        t1 = store.create_task("system_start")
        t2 = store.create_task("system_start")
        store.update_task(t2, "running")
        count = store.cleanup_stale_tasks("restart")
        assert count == 2
        for tid in (t1, t2):
            task = store.get_task(tid)
            assert task["status"] == "error"
            assert "restart" in str(task.get("result", ""))

    def test_returns_zero_when_nothing_to_clean(self, store):
        assert store.cleanup_stale_tasks() == 0


# ------------------------------------------------------------------
# 持久性（跨实例读写）
# ------------------------------------------------------------------

class TestPersistence:
    def test_data_survives_new_instance(self, tmp_db):
        """写入后关闭实例，新实例仍可读到数据。"""
        s1 = TaskStore(db_path=tmp_db)
        tid = s1.create_task("system_start", payload={"x": 99})
        s1.update_task(tid, "completed", result={"done": True})

        s2 = TaskStore(db_path=tmp_db)
        task = s2.get_task(tid)
        assert task is not None
        assert task["status"] == "completed"
        assert task["payload"]["x"] == 99
        assert task["result"]["done"] is True

    def test_zombie_cleanup_on_fresh_instance(self, tmp_db):
        """模拟进程重启：旧实例留下 running 任务，新实例启动时清理。"""
        old = TaskStore(db_path=tmp_db)
        tid = old.create_task("system_start")
        old.update_task(tid, "running")

        fresh = TaskStore(db_path=tmp_db)
        count = fresh.cleanup_stale_tasks()
        assert count == 1
        assert fresh.get_task(tid)["status"] == "error"
