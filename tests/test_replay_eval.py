# -*- coding: utf-8 -*-
"""tests/test_replay_eval.py — Phase 2.5 回放评分逻辑验证。"""

from __future__ import annotations

from veyrafish_core.replay_eval import evaluate_replay_case, evaluate_replay_run, index_runs_by_case_id


def _sample_case(case_id: str = "c1") -> dict:
    return {
        "case_id": case_id,
        "query": "测试主题",
        "required_engines": ["insight", "media", "query"],
        "expected_keypoints": ["价格战", "销量", "利润压力"],
        "expected_conflict_hints": ["销量增长|销量放缓"],
        "expect_evidence": True,
        "pass_threshold": 0.7,
    }


def test_evaluate_replay_case_passes_with_complete_signals():
    case = _sample_case("pass-case")
    run = {
        "engine_outputs": {
            "insight": "价格战推动销量增长，但利润压力增加，存在分歧。",
            "media": "媒体指出销量放缓与促销并存，存在冲突且渠道库存压力增加。",
            "query": "新闻显示利润压力上升，结论尚不确定，需要进一步验证。",
        },
        "evidence": {
            "total_count": 6,
            "top_claims": ["价格战推动销量增长", "利润压力增加"],
        },
        "quality_gate": {
            "insight": {"passed": True, "score": 0.9},
            "media": {"passed": True, "score": 0.8},
            "query": {"passed": True, "score": 0.85},
        },
    }

    report = evaluate_replay_case(case, run)
    assert report["passed"] is True
    assert report["overall_score"] >= 0.7
    assert report["dimensions"]["structure_integrity"]["passed"] is True
    assert report["dimensions"]["coverage"]["score"] >= 0.66


def test_evaluate_replay_case_fails_when_engine_missing():
    case = _sample_case("fail-case")
    run = {
        "engine_outputs": {
            "insight": "只有一个引擎有输出。",
            "media": "",
            "query": "",
        },
        "evidence": {"total_count": 0, "top_claims": []},
        "quality_gate": {"insight": False, "media": False, "query": False},
    }

    report = evaluate_replay_case(case, run)
    assert report["passed"] is False
    assert "media" in report["missing_engines"]
    assert report["dimensions"]["structure_integrity"]["score"] < 0.5


def test_index_runs_and_evaluate_replay_run_summary():
    cases = [_sample_case("case-a"), _sample_case("case-b")]
    runs = [
        {
            "case_id": "case-a",
            "engine_outputs": {
                "insight": "价格战 销量 利润压力",
                "media": "销量放缓 冲突",
                "query": "存在争议 尚不确定",
            },
            "evidence": {"total_count": 3, "top_claims": ["价格战"]},
            "quality_gate": {"insight": True, "media": True, "query": True},
        }
    ]
    indexed = index_runs_by_case_id(runs)
    result = evaluate_replay_run(cases, indexed)

    assert result["summary"]["total_cases"] == 2
    assert result["summary"]["failed_cases"] >= 1
    assert len(result["cases"]) == 2
