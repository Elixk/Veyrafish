# -*- coding: utf-8 -*-
"""
tests/test_evidence_store.py — Wave 5 验证：EvidenceStore + Evidence 模型
"""

import os
import tempfile
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from veyrafish_core.evidence_store import EvidenceStore, get_evidence_store
from veyrafish_core.output_models import Evidence, EvidenceAggregate


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------

def _make_store() -> EvidenceStore:
    """每个测试使用独立的临时 DB 文件。"""
    db_file = tempfile.mktemp(suffix=".db")
    return EvidenceStore(db_path=db_file)


def _make_evidence(
    task_id: str = "tid-001",
    engine: str = "insight",
    claim: str = "测试证据声明",
    confidence: float = 0.8,
    sentiment: str = "neutral",
    paragraph_index: int = 0,
) -> Evidence:
    return Evidence(
        task_id=task_id,
        engine=engine,
        paragraph_index=paragraph_index,
        claim=claim,
        supporting_text=f"支撑文本：{claim}",
        source_url="https://example.com",
        source_title="测试来源",
        confidence=confidence,
        sentiment=sentiment,
    )


# ---------------------------------------------------------------------------
# Evidence 模型测试
# ---------------------------------------------------------------------------

class TestEvidenceModel:
    def test_evidence_auto_id(self):
        e = _make_evidence()
        assert e.evidence_id is not None and len(e.evidence_id) > 0

    def test_evidence_auto_created_at(self):
        e = _make_evidence()
        assert e.created_at is not None and "T" in e.created_at

    def test_evidence_confidence_bounds(self):
        with pytest.raises(Exception):
            Evidence(task_id="t", engine="insight", claim="x", confidence=1.5)
        with pytest.raises(Exception):
            Evidence(task_id="t", engine="insight", claim="x", confidence=-0.1)

    def test_evidence_default_tags(self):
        e = _make_evidence()
        assert e.tags == []


# ---------------------------------------------------------------------------
# EvidenceStore 基础 CRUD
# ---------------------------------------------------------------------------

class TestEvidenceStoreCRUD:
    def test_add_single_evidence(self):
        store = _make_store()
        e = _make_evidence()
        eid = store.add(e)
        assert eid == e.evidence_id

    def test_get_returns_evidence(self):
        store = _make_store()
        e = _make_evidence(claim="独特声明内容")
        store.add(e)
        retrieved = store.get(e.evidence_id)
        assert retrieved is not None
        assert retrieved.claim == "独特声明内容"

    def test_get_missing_returns_none(self):
        store = _make_store()
        assert store.get("nonexistent-id") is None

    def test_add_batch(self):
        store = _make_store()
        batch = [_make_evidence(claim=f"声明 {i}") for i in range(5)]
        count = store.add_batch(batch)
        assert count == 5

    def test_add_batch_empty_returns_zero(self):
        store = _make_store()
        assert store.add_batch([]) == 0

    def test_count_by_task(self):
        store = _make_store()
        for i in range(3):
            store.add(_make_evidence(claim=f"声明{i}"))
        assert store.count_by_task("tid-001") == 3

    def test_count_by_task_empty(self):
        store = _make_store()
        assert store.count_by_task("no-such-task") == 0

    def test_delete_by_task(self):
        store = _make_store()
        store.add(_make_evidence())
        store.add(_make_evidence())
        deleted = store.delete_by_task("tid-001")
        assert deleted == 2
        assert store.count_by_task("tid-001") == 0

    def test_add_batch_deduplication_by_id(self):
        """同一 evidence_id 再次写入应覆盖（INSERT OR REPLACE）。"""
        store = _make_store()
        e = _make_evidence(claim="原始声明")
        store.add(e)
        e2 = Evidence(
            evidence_id=e.evidence_id,
            task_id=e.task_id,
            engine=e.engine,
            claim="更新后的声明",
            confidence=0.9,
        )
        store.add(e2)
        retrieved = store.get(e.evidence_id)
        assert retrieved.claim == "更新后的声明"


# ---------------------------------------------------------------------------
# EvidenceStore 查询
# ---------------------------------------------------------------------------

class TestEvidenceStoreQuery:
    def test_query_by_task_returns_all(self):
        store = _make_store()
        for engine in ["insight", "media", "query"]:
            store.add(_make_evidence(engine=engine, claim=f"{engine} 声明"))
        results = store.query_by_task("tid-001")
        assert len(results) == 3

    def test_query_by_task_filter_engine(self):
        store = _make_store()
        store.add(_make_evidence(engine="insight", claim="洞察声明"))
        store.add(_make_evidence(engine="media", claim="媒体声明"))
        results = store.query_by_task("tid-001", engine="insight")
        assert len(results) == 1
        assert results[0].engine == "insight"

    def test_query_by_task_filter_confidence(self):
        store = _make_store()
        store.add(_make_evidence(claim="高置信", confidence=0.9))
        store.add(_make_evidence(claim="低置信", confidence=0.3))
        results = store.query_by_task("tid-001", min_confidence=0.7)
        assert len(results) == 1
        assert results[0].claim == "高置信"

    def test_query_by_task_sorted_by_confidence_desc(self):
        store = _make_store()
        store.add(_make_evidence(claim="低", confidence=0.3))
        store.add(_make_evidence(claim="高", confidence=0.9))
        store.add(_make_evidence(claim="中", confidence=0.6))
        results = store.query_by_task("tid-001")
        confidences = [r.confidence for r in results]
        assert confidences == sorted(confidences, reverse=True)

    def test_query_by_claim_keyword(self):
        store = _make_store()
        store.add(_make_evidence(claim="Veyrafish 舆情分析"))
        store.add(_make_evidence(claim="其他无关内容"))
        results = store.query_by_claim("tid-001", "Veyrafish")
        assert len(results) == 1
        assert "Veyrafish" in results[0].claim

    def test_query_by_task_different_tasks_isolated(self):
        store = _make_store()
        store.add(_make_evidence(task_id="tid-A", claim="A 的证据"))
        store.add(_make_evidence(task_id="tid-B", claim="B 的证据"))
        results_a = store.query_by_task("tid-A")
        assert len(results_a) == 1
        assert results_a[0].task_id == "tid-A"

    def test_tags_serialized_and_deserialized(self):
        store = _make_store()
        e = Evidence(
            task_id="tid-001", engine="insight",
            claim="带标签的证据",
            tags=["tag1", "tag2"],
        )
        store.add(e)
        retrieved = store.get(e.evidence_id)
        assert retrieved.tags == ["tag1", "tag2"]


# ---------------------------------------------------------------------------
# EvidenceStore 聚合
# ---------------------------------------------------------------------------

class TestEvidenceStoreAggregate:
    def test_aggregate_empty_task(self):
        store = _make_store()
        agg = store.aggregate("empty-task")
        assert agg.total_count == 0

    def test_aggregate_counts(self):
        store = _make_store()
        store.add(_make_evidence(engine="insight", sentiment="positive", confidence=0.8))
        store.add(_make_evidence(engine="insight", sentiment="negative", confidence=0.7))
        store.add(_make_evidence(engine="media", sentiment="neutral", confidence=0.6))

        agg = store.aggregate("tid-001")
        assert agg.total_count == 3
        assert agg.by_engine["insight"] == 2
        assert agg.by_engine["media"] == 1
        assert agg.by_sentiment["positive"] == 1
        assert agg.by_sentiment["negative"] == 1

    def test_aggregate_avg_confidence(self):
        store = _make_store()
        store.add(_make_evidence(confidence=0.8))
        store.add(_make_evidence(confidence=0.6))
        agg = store.aggregate("tid-001")
        assert abs(agg.avg_confidence - 0.7) < 0.01

    def test_aggregate_top_claims(self):
        store = _make_store()
        for i in range(5):
            store.add(_make_evidence(claim=f"声明 {i}", confidence=0.5 + i * 0.1))
        agg = store.aggregate("tid-001", top_n=3)
        assert len(agg.top_claims) == 3


# ---------------------------------------------------------------------------
# EvidenceStore 矛盾检测
# ---------------------------------------------------------------------------

class TestEvidenceStoreConflicts:
    def test_find_conflicts_opposite_sentiment(self):
        store = _make_store()
        store.add(_make_evidence(claim="积极声明1", sentiment="positive", confidence=0.9))
        store.add(_make_evidence(claim="积极声明2", sentiment="positive", confidence=0.8))
        store.add(_make_evidence(claim="消极声明1", sentiment="negative", confidence=0.85))

        conflicts = store.find_conflicts("tid-001", min_confidence=0.7)
        assert len(conflicts) > 0
        assert all("positive_claim" in c for c in conflicts)
        assert all("negative_claim" in c for c in conflicts)

    def test_find_conflicts_no_conflict_same_sentiment(self):
        store = _make_store()
        store.add(_make_evidence(sentiment="positive", confidence=0.9))
        store.add(_make_evidence(sentiment="positive", confidence=0.8))
        conflicts = store.find_conflicts("tid-001")
        assert len(conflicts) == 0

    def test_find_conflicts_low_confidence_excluded(self):
        store = _make_store()
        store.add(_make_evidence(sentiment="positive", confidence=0.5))
        store.add(_make_evidence(sentiment="negative", confidence=0.5))
        conflicts = store.find_conflicts("tid-001", min_confidence=0.7)
        assert len(conflicts) == 0


# ---------------------------------------------------------------------------
# 全局单例
# ---------------------------------------------------------------------------

class TestGetEvidenceStore:
    def test_singleton_returns_same_instance(self):
        import importlib
        import veyrafish_core.evidence_store as es_module

        # 重置单例
        es_module._default_evidence_store = None

        db = tempfile.mktemp(suffix=".db")
        store1 = es_module.get_evidence_store(db_path=db)
        store2 = es_module.get_evidence_store(db_path=db)
        assert store1 is store2

        # 清理单例避免影响其他测试
        es_module._default_evidence_store = None

    def test_store_coexists_with_task_store(self):
        """EvidenceStore 与 TaskStore 共用同一 DB 文件，不应互相干扰。"""
        from task_store import TaskStore

        db = tempfile.mktemp(suffix=".db")
        task_store = TaskStore(db_path=db)
        ev_store = EvidenceStore(db_path=db)

        # task_store 正常创建任务
        tid = task_store.create_task("test")
        assert task_store.get_task(tid) is not None

        # ev_store 正常写入证据
        store_count = ev_store.add(_make_evidence(task_id=tid))
        assert ev_store.count_by_task(tid) == 1
