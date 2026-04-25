# -*- coding: utf-8 -*-
"""Phase 2.5 replay evaluation helpers."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Mapping

from veyrafish_core.skill import SkillContext
from veyrafish_core.skills import default_registry
from veyrafish_core.skills._models import QualityGateInput

DEFAULT_REQUIRED_ENGINES = ["insight", "media", "query"]
DEFAULT_DIMENSION_WEIGHTS = {
    "structure_integrity": 0.20,
    "coverage": 0.25,
    "conflict_retention": 0.20,
    "evidence_citation_stability": 0.20,
    "quality_gate_pass_rate": 0.15,
}
DEFAULT_DIMENSION_THRESHOLDS = {
    "structure_integrity": 0.75,
    "coverage": 0.60,
    "conflict_retention": 0.60,
    "evidence_citation_stability": 0.50,
    "quality_gate_pass_rate": 0.60,
}
DEFAULT_PASS_THRESHOLD = 0.70

UNCERTAINTY_MARKERS = (
    "冲突",
    "不一致",
    "分歧",
    "尚不确定",
    "需进一步验证",
    "存在争议",
    "uncertain",
    "conflict",
    "inconclusive",
)


def evaluate_replay_case(case: Mapping[str, Any], run: Mapping[str, Any]) -> Dict[str, Any]:
    """Evaluate one replay case and return a structured score report."""
    case_id = str(case.get("case_id", "")).strip()
    query = str(case.get("query", "")).strip()
    required_engines = [
        str(engine).strip()
        for engine in (case.get("required_engines") or DEFAULT_REQUIRED_ENGINES)
        if str(engine).strip()
    ]
    if not required_engines:
        required_engines = list(DEFAULT_REQUIRED_ENGINES)

    engine_outputs = run.get("engine_outputs")
    if not isinstance(engine_outputs, Mapping):
        # Backward compatible shape: run itself is engine -> text
        engine_outputs = run
    quality_gate = run.get("quality_gate")
    evidence = run.get("evidence") if isinstance(run.get("evidence"), Mapping) else {}

    combined_text = "\n".join(
        _safe_text(engine_outputs.get(engine, "")) for engine in required_engines
    ).lower()

    structure_score, structure_detail = _score_structure(required_engines, engine_outputs)
    coverage_score, coverage_detail = _score_coverage(
        case.get("expected_keypoints") or [],
        combined_text,
    )
    conflict_score, conflict_detail = _score_conflict_retention(
        case.get("expected_conflict_hints") or [],
        combined_text,
    )
    evidence_score, evidence_detail = _score_evidence_citation(
        case=case,
        evidence=evidence,
        combined_text=combined_text,
    )
    quality_score, quality_detail = _score_quality_gate(
        required_engines=required_engines,
        engine_outputs=engine_outputs,
        quality_gate=quality_gate,
    )

    dimensions: Dict[str, Dict[str, Any]] = {
        "structure_integrity": {"score": structure_score, "detail": structure_detail},
        "coverage": {"score": coverage_score, "detail": coverage_detail},
        "conflict_retention": {"score": conflict_score, "detail": conflict_detail},
        "evidence_citation_stability": {"score": evidence_score, "detail": evidence_detail},
        "quality_gate_pass_rate": {"score": quality_score, "detail": quality_detail},
    }

    thresholds = dict(DEFAULT_DIMENSION_THRESHOLDS)
    custom_thresholds = case.get("min_dimension_scores")
    if isinstance(custom_thresholds, Mapping):
        for key, value in custom_thresholds.items():
            try:
                thresholds[str(key)] = _clamp01(float(value))
            except (TypeError, ValueError):
                continue

    weights = dict(DEFAULT_DIMENSION_WEIGHTS)
    custom_weights = case.get("dimension_weights")
    if isinstance(custom_weights, Mapping):
        for key, value in custom_weights.items():
            try:
                weights[str(key)] = max(0.0, float(value))
            except (TypeError, ValueError):
                continue
    weight_sum = sum(weights.values()) or 1.0

    overall_score = 0.0
    all_dimensions_passed = True
    for name, payload in dimensions.items():
        threshold = thresholds.get(name, 0.0)
        passed = payload["score"] >= threshold
        payload["threshold"] = round(threshold, 3)
        payload["passed"] = passed
        if not passed:
            all_dimensions_passed = False
        overall_score += payload["score"] * (weights.get(name, 0.0) / weight_sum)

    pass_threshold = _clamp01(float(case.get("pass_threshold", DEFAULT_PASS_THRESHOLD)))
    overall_score = round(overall_score, 3)
    passed = bool(overall_score >= pass_threshold and all_dimensions_passed)

    return {
        "case_id": case_id,
        "query": query,
        "overall_score": overall_score,
        "pass_threshold": round(pass_threshold, 3),
        "passed": passed,
        "dimensions": dimensions,
        "required_engines": required_engines,
        "missing_engines": structure_detail.get("missing_engines", []),
    }


def evaluate_replay_run(
    cases: List[Mapping[str, Any]],
    runs_by_case_id: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    """Evaluate all replay cases and return aggregate summary."""
    reports: List[Dict[str, Any]] = []
    for case in cases:
        case_id = str(case.get("case_id", "")).strip()
        run = runs_by_case_id.get(case_id, {})
        reports.append(evaluate_replay_case(case=case, run=run))

    passed_count = sum(1 for item in reports if item["passed"])
    total_count = len(reports)
    avg_score = round(
        (sum(item["overall_score"] for item in reports) / total_count) if total_count else 0.0,
        3,
    )

    return {
        "summary": {
            "total_cases": total_count,
            "passed_cases": passed_count,
            "failed_cases": total_count - passed_count,
            "pass_rate": round((passed_count / total_count) if total_count else 0.0, 3),
            "avg_overall_score": avg_score,
        },
        "cases": reports,
    }


def index_runs_by_case_id(items: Iterable[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Convert a list of replay run items to {case_id -> run_payload}."""
    indexed: Dict[str, Dict[str, Any]] = {}
    for item in items:
        case_id = str(item.get("case_id", "")).strip()
        if not case_id:
            continue
        indexed[case_id] = dict(item)
    return indexed


def _score_structure(
    required_engines: List[str],
    engine_outputs: Mapping[str, Any],
) -> tuple[float, Dict[str, Any]]:
    text_lengths: Dict[str, int] = {}
    present_engines: List[str] = []
    missing_engines: List[str] = []
    for engine in required_engines:
        content = _safe_text(engine_outputs.get(engine, ""))
        length = len(content.strip())
        text_lengths[engine] = length
        if length >= 20:
            present_engines.append(engine)
        else:
            missing_engines.append(engine)

    score = (len(present_engines) / len(required_engines)) if required_engines else 1.0
    detail = {
        "present_engines": present_engines,
        "missing_engines": missing_engines,
        "content_length_by_engine": text_lengths,
    }
    return round(score, 3), detail


def _score_coverage(
    expected_keypoints: Iterable[Any],
    combined_text: str,
) -> tuple[float, Dict[str, Any]]:
    normalized = [str(item).strip() for item in expected_keypoints if str(item).strip()]
    if not normalized:
        return 1.0, {"matched_keypoints": [], "missing_keypoints": []}

    matched: List[str] = []
    missing: List[str] = []
    for keypoint in normalized:
        if _has_hint(combined_text, keypoint):
            matched.append(keypoint)
        else:
            missing.append(keypoint)

    score = len(matched) / len(normalized)
    detail = {
        "matched_keypoints": matched,
        "missing_keypoints": missing,
    }
    return round(score, 3), detail


def _score_conflict_retention(
    expected_conflicts: Iterable[Any],
    combined_text: str,
) -> tuple[float, Dict[str, Any]]:
    normalized = [str(item).strip() for item in expected_conflicts if str(item).strip()]
    uncertainty_hits = [token for token in UNCERTAINTY_MARKERS if token in combined_text]

    if not normalized:
        score = 1.0 if uncertainty_hits else 0.85
        return round(score, 3), {
            "matched_conflicts": [],
            "missing_conflicts": [],
            "uncertainty_markers": uncertainty_hits,
        }

    matched: List[str] = []
    missing: List[str] = []
    for hint in normalized:
        if _has_hint(combined_text, hint):
            matched.append(hint)
        else:
            missing.append(hint)

    base = len(matched) / len(normalized)
    bonus = 0.15 if uncertainty_hits else 0.0
    score = min(1.0, base + bonus)
    detail = {
        "matched_conflicts": matched,
        "missing_conflicts": missing,
        "uncertainty_markers": uncertainty_hits,
    }
    return round(score, 3), detail


def _score_evidence_citation(
    case: Mapping[str, Any],
    evidence: Mapping[str, Any],
    combined_text: str,
) -> tuple[float, Dict[str, Any]]:
    expect_evidence = bool(case.get("expect_evidence", True))
    total_count = _safe_int(evidence.get("total_count"), default=0)
    top_claims = [
        str(item).strip()
        for item in (evidence.get("top_claims") or [])
        if str(item).strip()
    ][:5]
    top_claim_hits = [claim for claim in top_claims if _has_hint(combined_text, claim)]

    if not expect_evidence:
        score = 1.0 if total_count == 0 else min(1.0, 0.6 + 0.4 * _ratio(len(top_claim_hits), len(top_claims)))
    else:
        if total_count <= 0:
            score = 0.0
        else:
            claim_ratio = _ratio(len(top_claim_hits), len(top_claims))
            score = min(1.0, 0.55 + 0.45 * claim_ratio)

    detail = {
        "expect_evidence": expect_evidence,
        "total_count": total_count,
        "top_claims_checked": top_claims,
        "matched_top_claims": top_claim_hits,
    }
    return round(score, 3), detail


def _score_quality_gate(
    required_engines: List[str],
    engine_outputs: Mapping[str, Any],
    quality_gate: Any,
) -> tuple[float, Dict[str, Any]]:
    provided = quality_gate if isinstance(quality_gate, Mapping) else {}
    context = SkillContext()

    engine_scores: Dict[str, float] = {}
    engine_passed: Dict[str, bool] = {}

    for engine in required_engines:
        if engine in provided:
            passed, score = _normalize_quality_gate_result(provided.get(engine))
        else:
            content = _safe_text(engine_outputs.get(engine, ""))
            if not content.strip():
                passed, score = False, 0.0
            else:
                result = default_registry.execute(
                    "quality_gate",
                    QualityGateInput(content=content, content_type="summary"),
                    context,
                )
                passed = bool(getattr(result, "passed", False))
                score = _clamp01(float(getattr(result, "score", 0.0)))
        engine_scores[engine] = round(score, 3)
        engine_passed[engine] = bool(passed)

    pass_rate = _ratio(sum(1 for ok in engine_passed.values() if ok), len(required_engines))
    avg_gate_score = _ratio(sum(engine_scores.values()), len(required_engines))
    blended_score = round(0.7 * pass_rate + 0.3 * avg_gate_score, 3)

    detail = {
        "engine_passed": engine_passed,
        "engine_scores": engine_scores,
        "pass_rate": round(pass_rate, 3),
        "avg_gate_score": round(avg_gate_score, 3),
    }
    return blended_score, detail


def _normalize_quality_gate_result(raw: Any) -> tuple[bool, float]:
    if isinstance(raw, Mapping):
        passed = bool(raw.get("passed", False))
        score = raw.get("score", 1.0 if passed else 0.0)
        try:
            return passed, _clamp01(float(score))
        except (TypeError, ValueError):
            return passed, (1.0 if passed else 0.0)
    if isinstance(raw, bool):
        return raw, (1.0 if raw else 0.0)
    try:
        score = _clamp01(float(raw))
        return score >= 0.5, score
    except (TypeError, ValueError):
        return False, 0.0


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _ratio(num: float, den: float) -> float:
    return float(num) / float(den) if den else 0.0


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _has_hint(text: str, hint: str) -> bool:
    normalized_text = text.lower()
    candidates = [item.strip().lower() for item in hint.split("|") if item.strip()]
    return any(candidate in normalized_text for candidate in candidates)


__all__ = [
    "evaluate_replay_case",
    "evaluate_replay_run",
    "index_runs_by_case_id",
]

