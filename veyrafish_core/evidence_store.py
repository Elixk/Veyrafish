# -*- coding: utf-8 -*-
"""
veyrafish_core.evidence_store — 共享证据存储层

Wave 5 新增：三引擎在研究过程中持续沉淀结构化证据到 SQLite evidence 表，
供 ReportEngine / ForumEngine / 前端读取。

与 TaskStore 共用同一个 SQLite 文件（logs/tasks.db），避免多数据库文件。
evidence 表在 task_store._init_db() 中创建（DDL 已在 Wave 5a 中添加）。

用法::

    from veyrafish_core.evidence_store import get_evidence_store, EvidenceStore
    from veyrafish_core.output_models import Evidence

    store = get_evidence_store()

    # 写入单条证据
    e = Evidence(
        task_id="tid-001", engine="insight",
        claim="某事件导致舆情高涨", confidence=0.85, sentiment="negative",
    )
    store.add(e)

    # 批量写入
    store.add_batch([e1, e2, e3])

    # 查询
    evidences = store.query_by_task("tid-001")
    agg = store.aggregate("tid-001")
    conflicts = store.find_conflicts("tid-001")
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from veyrafish_core.output_models import Evidence, EvidenceAggregate


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class EvidenceStore:
    """
    线程安全的证据存储，复用 task_store 的 SQLite 文件。

    表 `evidence` 的 DDL 由 task_store.TaskStore._init_db() 创建，
    EvidenceStore 启动时不重复建表，只做安全检查（idempotent DDL）。
    """

    _lock = threading.Lock()

    def __init__(self, db_path: str = "logs/tasks.db") -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_table()

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
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _ensure_table(self) -> None:
        """确保 evidence 表存在（与 TaskStore 共用 DB 时表已存在；独立 DB 时自建）。"""
        conn = self._connect()
        try:
            with self._lock:
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

    @staticmethod
    def _row_to_evidence(row: sqlite3.Row) -> Evidence:
        """将 SQLite Row 转换为 Evidence 实例。"""
        d = dict(row)
        try:
            d["tags"] = json.loads(d.get("tags") or "[]")
        except (json.JSONDecodeError, TypeError):
            d["tags"] = []
        return Evidence(**d)

    # ------------------------------------------------------------------
    # 写入 API
    # ------------------------------------------------------------------

    def add(self, evidence: Evidence) -> str:
        """写入单条证据，返回 evidence_id。"""
        tags_json = json.dumps(evidence.tags, ensure_ascii=False)
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO evidence
                    (evidence_id, task_id, engine, paragraph_index, claim,
                     supporting_text, source_url, source_title,
                     confidence, sentiment, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence.evidence_id,
                    evidence.task_id,
                    evidence.engine,
                    evidence.paragraph_index,
                    evidence.claim,
                    evidence.supporting_text,
                    evidence.source_url,
                    evidence.source_title,
                    evidence.confidence,
                    evidence.sentiment,
                    tags_json,
                    evidence.created_at or _now_iso(),
                ),
            )
            conn.commit()
        return evidence.evidence_id

    def add_batch(self, evidences: List[Evidence]) -> int:
        """批量写入证据列表，返回成功写入条数。"""
        if not evidences:
            return 0
        rows = []
        for e in evidences:
            rows.append((
                e.evidence_id,
                e.task_id,
                e.engine,
                e.paragraph_index,
                e.claim,
                e.supporting_text,
                e.source_url,
                e.source_title,
                e.confidence,
                e.sentiment,
                json.dumps(e.tags, ensure_ascii=False),
                e.created_at or _now_iso(),
            ))
        with self._lock, self._connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO evidence
                    (evidence_id, task_id, engine, paragraph_index, claim,
                     supporting_text, source_url, source_title,
                     confidence, sentiment, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()
        return len(rows)

    # ------------------------------------------------------------------
    # 查询 API
    # ------------------------------------------------------------------

    def get(self, evidence_id: str) -> Optional[Evidence]:
        """按 ID 查询单条证据。"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM evidence WHERE evidence_id = ?", (evidence_id,)
            ).fetchone()
        return self._row_to_evidence(row) if row else None

    def query_by_task(
        self,
        task_id: str,
        engine: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 200,
    ) -> List[Evidence]:
        """查询指定 task_id 下的所有证据，可按引擎和置信度过滤。"""
        if engine:
            sql = (
                "SELECT * FROM evidence WHERE task_id=? AND engine=? "
                "AND confidence>=? ORDER BY confidence DESC LIMIT ?"
            )
            params = (task_id, engine, min_confidence, limit)
        else:
            sql = (
                "SELECT * FROM evidence WHERE task_id=? AND confidence>=? "
                "ORDER BY confidence DESC LIMIT ?"
            )
            params = (task_id, min_confidence, limit)

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_evidence(r) for r in rows]

    def query_by_claim(self, task_id: str, keyword: str, limit: int = 50) -> List[Evidence]:
        """在指定任务的证据中按关键词全文搜索 claim。"""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM evidence WHERE task_id=? AND claim LIKE ? "
                "ORDER BY confidence DESC LIMIT ?",
                (task_id, f"%{keyword}%", limit),
            ).fetchall()
        return [self._row_to_evidence(r) for r in rows]

    # ------------------------------------------------------------------
    # 聚合 API
    # ------------------------------------------------------------------

    def aggregate(self, task_id: str, top_n: int = 5) -> EvidenceAggregate:
        """生成指定任务的证据聚合摘要。"""
        evidences = self.query_by_task(task_id, limit=500)
        if not evidences:
            return EvidenceAggregate()

        # 按引擎分组
        by_engine: Dict[str, int] = {}
        for e in evidences:
            by_engine[e.engine] = by_engine.get(e.engine, 0) + 1

        # 按情感分组
        by_sentiment: Dict[str, int] = {}
        for e in evidences:
            key = e.sentiment or "unknown"
            by_sentiment[key] = by_sentiment.get(key, 0) + 1

        # 平均置信度
        avg_conf = sum(e.confidence for e in evidences) / len(evidences)

        # top N claim（按置信度排序，已经是降序）
        top_claims = [e.claim for e in evidences[:top_n]]

        # 矛盾检测（同一 task 下 sentiment 方向相反的高置信度证据对）
        conflicts = self.find_conflicts(task_id)

        return EvidenceAggregate(
            total_count=len(evidences),
            by_engine=by_engine,
            by_sentiment=by_sentiment,
            avg_confidence=round(avg_conf, 3),
            top_claims=top_claims,
            conflicts=conflicts,
        )

    def find_conflicts(self, task_id: str, min_confidence: float = 0.7) -> List[Dict]:
        """
        发现矛盾证据对：同一 task 内 sentiment 分别为 positive 和 negative
        的高置信度证据。

        返回包含 (positive_claim, negative_claim) 的字典列表。
        """
        high_conf = self.query_by_task(task_id, min_confidence=min_confidence)
        positives = [e for e in high_conf if e.sentiment == "positive"]
        negatives = [e for e in high_conf if e.sentiment == "negative"]

        if not positives or not negatives:
            return []

        # 简单配对：取前 3 对
        conflicts = []
        for pos in positives[:3]:
            for neg in negatives[:3]:
                conflicts.append({
                    "positive_claim": pos.claim,
                    "positive_engine": pos.engine,
                    "negative_claim": neg.claim,
                    "negative_engine": neg.engine,
                    "note": "情感方向相反，可能存在矛盾观点",
                })
        return conflicts[:5]  # 最多返回 5 对

    # ------------------------------------------------------------------
    # 清理 API
    # ------------------------------------------------------------------

    def delete_by_task(self, task_id: str) -> int:
        """删除指定任务的所有证据，返回删除条数。"""
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM evidence WHERE task_id=?", (task_id,)
            )
            conn.commit()
            return cursor.rowcount

    def count_by_task(self, task_id: str) -> int:
        """返回指定任务的证据条数。"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM evidence WHERE task_id=?", (task_id,)
            ).fetchone()
        return row["cnt"] if row else 0


# ------------------------------------------------------------------
# 全局单例
# ------------------------------------------------------------------

_default_evidence_store: Optional[EvidenceStore] = None
_store_lock = threading.Lock()


def get_evidence_store(db_path: str = "logs/tasks.db") -> EvidenceStore:
    """获取全局 EvidenceStore 单例（与 task_store 共用同一 SQLite 文件）。"""
    global _default_evidence_store
    with _store_lock:
        if _default_evidence_store is None:
            _default_evidence_store = EvidenceStore(db_path=db_path)
    return _default_evidence_store
