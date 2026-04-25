# -*- coding: utf-8 -*-
"""
task_store.py — 轻量 SQLite 任务状态层

职责
----
为长时任务（目前主要是系统启动 system_start）提供持久化的状态记录。
进程重启后历史任务仍可查询，为前端「最近任务」功能提供数据基础。

设计约束
--------
- 纯 Python 标准库（sqlite3），无额外依赖
- 线程安全：每次操作使用 check_same_thread=False + 独立连接（WAL 模式）
- 不依赖 Flask / SocketIO，可在测试中单独使用
- 数据库文件路径在构造时传入，默认 logs/tasks.db

表结构
------
tasks
  task_id     TEXT PRIMARY KEY   -- uuid4
  task_type   TEXT               -- e.g. "system_start"
  status      TEXT               -- starting | running | completed | error
  created_at  TEXT               -- ISO8601 UTC
  updated_at  TEXT               -- ISO8601 UTC
  payload     TEXT               -- JSON 编码的输入参数
  result      TEXT               -- JSON 编码的结果 / 错误信息
"""

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _now_iso() -> str:
    """返回当前 UTC 时间的 ISO8601 字符串（精确到秒）。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class TaskStore:
    """线程安全的 SQLite 任务状态存储。"""

    _lock = threading.Lock()

    def __init__(self, db_path: str = "logs/tasks.db") -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            str(self._db_path),
            check_same_thread=False,
            timeout=10,
        )
        conn.row_factory = sqlite3.Row
        # WAL 模式：读写不互斥，适合并发少量写入 + 频繁读取
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            with self._lock:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id    TEXT PRIMARY KEY,
                        task_type  TEXT NOT NULL,
                        status     TEXT NOT NULL DEFAULT 'starting',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        payload    TEXT,
                        result     TEXT
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS task_events (
                        event_id   TEXT PRIMARY KEY,
                        task_id    TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        node_name  TEXT,
                        paragraph  INTEGER,
                        iteration  INTEGER,
                        detail     TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_task_events_task_id "
                    "ON task_events (task_id)"
                )
                # Wave 5：共享证据表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS evidence (
                        evidence_id     TEXT PRIMARY KEY,
                        task_id         TEXT NOT NULL,
                        engine          TEXT NOT NULL,
                        paragraph_index INTEGER,
                        claim           TEXT NOT NULL,
                        supporting_text TEXT DEFAULT '',
                        source_url      TEXT DEFAULT '',
                        source_title    TEXT DEFAULT '',
                        confidence      REAL DEFAULT 0.5,
                        sentiment       TEXT,
                        tags            TEXT DEFAULT '[]',
                        created_at      TEXT NOT NULL
                    )
                """)
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_evidence_task_id "
                    "ON evidence (task_id)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_evidence_engine "
                    "ON evidence (task_id, engine)"
                )
                conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def create_task(
        self,
        task_type: str,
        payload: Optional[dict] = None,
    ) -> str:
        """创建一条新任务记录，返回 task_id。"""
        task_id = str(uuid.uuid4())
        now = _now_iso()
        payload_json = json.dumps(payload or {}, ensure_ascii=False)

        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (task_id, task_type, status, created_at, updated_at, payload)
                VALUES (?, ?, 'starting', ?, ?, ?)
                """,
                (task_id, task_type, now, now, payload_json),
            )
            conn.commit()

        return task_id

    def update_task(
        self,
        task_id: str,
        status: str,
        result: Optional[Any] = None,
    ) -> None:
        """更新任务状态，可选更新 result 字段。"""
        now = _now_iso()
        result_json = json.dumps(result, ensure_ascii=False) if result is not None else None

        with self._lock, self._connect() as conn:
            if result_json is not None:
                conn.execute(
                    """
                    UPDATE tasks
                    SET status = ?, updated_at = ?, result = ?
                    WHERE task_id = ?
                    """,
                    (status, now, result_json, task_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE tasks
                    SET status = ?, updated_at = ?
                    WHERE task_id = ?
                    """,
                    (status, now, task_id),
                )
            conn.commit()

    def get_task(self, task_id: str) -> Optional[dict]:
        """按 task_id 查询单条任务，不存在时返回 None。"""
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()

        if row is None:
            return None
        return _row_to_dict(row)

    # ------------------------------------------------------------------
    # 节点级进度事件
    # ------------------------------------------------------------------

    def add_event(
        self,
        task_id: str,
        event_type: str,
        node_name: Optional[str] = None,
        paragraph: Optional[int] = None,
        iteration: Optional[int] = None,
        detail: Optional[Any] = None,
    ) -> str:
        """
        向 task_events 表写入一条节点级进度事件，返回 event_id。

        event_type 建议值：
          research_start / research_done
          paragraph_start / paragraph_done
          node_start / node_done
          error
        """
        event_id = str(uuid.uuid4())
        now = _now_iso()
        detail_json = json.dumps(detail, ensure_ascii=False) if detail is not None else None

        conn = self._connect()
        try:
            with self._lock:
                conn.execute(
                    """
                    INSERT INTO task_events
                        (event_id, task_id, event_type, node_name, paragraph,
                         iteration, detail, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (event_id, task_id, event_type, node_name,
                     paragraph, iteration, detail_json, now),
                )
                conn.commit()
        finally:
            conn.close()

        return event_id

    def list_events(
        self,
        task_id: str,
        event_type: Optional[str] = None,
        limit: int = 200,
    ) -> list:
        """
        查询某个 task 的事件列表（按时间正序）。
        可按 event_type 过滤。
        """
        conn = self._connect()
        try:
            with self._lock:
                if event_type:
                    rows = conn.execute(
                        """
                        SELECT * FROM task_events
                        WHERE task_id = ? AND event_type = ?
                        ORDER BY created_at ASC
                        LIMIT ?
                        """,
                        (task_id, event_type, limit),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        """
                        SELECT * FROM task_events
                        WHERE task_id = ?
                        ORDER BY created_at ASC
                        LIMIT ?
                        """,
                        (task_id, limit),
                    ).fetchall()
        finally:
            conn.close()

        result = []
        for row in rows:
            d = dict(row)
            if d.get("detail"):
                try:
                    d["detail"] = json.loads(d["detail"])
                except (json.JSONDecodeError, TypeError):
                    pass
            result.append(d)
        return result

    def get_completed_paragraphs(self, task_id: str) -> set:
        """
        返回已完成段落的 index 集合（有 paragraph_done 事件的段落）。
        用于断点恢复时跳过已完成段落。
        """
        events = self.list_events(task_id, event_type="paragraph_done")
        return {e["paragraph"] for e in events if e.get("paragraph") is not None}

    # ------------------------------------------------------------------
    # 清理僵尸任务
    # ------------------------------------------------------------------

    def cleanup_stale_tasks(self, reason: str = "进程重启，任务未正常结束") -> int:
        """
        将所有处于 starting 或 running 状态的历史任务标记为 error。

        应在进程启动时调用一次，防止上次异常退出遗留的"僵尸任务"永远卡在
        运行中状态，误导前端查询。

        返回被清理的任务数量。
        """
        now = _now_iso()
        result_json = json.dumps({"error": reason}, ensure_ascii=False)

        conn = self._connect()
        try:
            with self._lock:
                cursor = conn.execute(
                    """
                    UPDATE tasks
                    SET status = 'error', updated_at = ?, result = ?
                    WHERE status IN ('starting', 'running')
                    """,
                    (now, result_json),
                )
                count = cursor.rowcount
                conn.commit()
        finally:
            conn.close()

        return count

    def list_tasks(self, limit: int = 20, task_type: Optional[str] = None) -> list:
        """
        查询最近 N 条任务（按创建时间倒序）。
        可按 task_type 过滤。
        """
        with self._lock, self._connect() as conn:
            if task_type:
                rows = conn.execute(
                    """
                    SELECT * FROM tasks
                    WHERE task_type = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (task_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM tasks
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

        return [_row_to_dict(r) for r in rows]


def _row_to_dict(row: sqlite3.Row) -> dict:
    """将 sqlite3.Row 转为普通 dict，解析 JSON 字段。"""
    d = dict(row)
    for field in ("payload", "result"):
        raw = d.get(field)
        if raw:
            try:
                d[field] = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                pass
    return d


# 全局单例（供 app.py 直接 import 使用）
_default_store: Optional[TaskStore] = None
_store_lock = threading.Lock()


def get_task_store(db_path: str = "logs/tasks.db") -> TaskStore:
    """获取全局 TaskStore 单例，首次调用时初始化。"""
    global _default_store
    if _default_store is None:
        with _store_lock:
            if _default_store is None:
                _default_store = TaskStore(db_path)
    return _default_store
