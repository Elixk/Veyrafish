# -*- coding: utf-8 -*-
"""Phase 2.5 fixed-case replay runner."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping

# Ensure project root is importable when running this file directly.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from veyrafish_core.evidence_store import get_evidence_store
from veyrafish_core.replay_eval import evaluate_replay_run, index_runs_by_case_id

DEFAULT_CASES_FILE = Path("docs/implementation/phase-2-5-replay-samples.json")
DEFAULT_FIXTURES_FILE = Path("docs/implementation/phase-2-5-replay-fixtures.json")
DEFAULT_OUTPUT_ROOT = Path("outputs/phase25_replay")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 2.5 replay evaluation")
    parser.add_argument(
        "--mode",
        choices=["fixture", "live"],
        default="fixture",
        help="fixture: 使用固定夹具回放；live: 实际调用三引擎",
    )
    parser.add_argument("--cases", default=str(DEFAULT_CASES_FILE), help="固定样例文件路径")
    parser.add_argument(
        "--fixtures",
        default=str(DEFAULT_FIXTURES_FILE),
        help="固定回放夹具文件路径（mode=fixture 时使用）",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="评估结果输出目录根路径",
    )
    parser.add_argument(
        "--db-path",
        default="logs/tasks.db",
        help="共享 task/evidence 的数据库路径",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=0,
        help="最多执行多少个样例（0 表示全部）",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="存在失败样例时返回非零退出码",
    )
    return parser.parse_args()


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _ensure_cases(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, dict):
        cases = payload.get("cases")
        if isinstance(cases, list):
            return [dict(item) for item in cases if isinstance(item, Mapping)]
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, Mapping)]
    raise ValueError("cases 文件格式不合法，期望 list 或 {'cases': [...]} 结构")


def _collect_fixture_runs(fixtures_path: Path) -> Dict[str, Dict[str, Any]]:
    payload = _load_json(fixtures_path)
    if isinstance(payload, dict):
        items = payload.get("cases")
        if items is None:
            items = payload.get("runs")
    else:
        items = payload
    if not isinstance(items, list):
        raise ValueError("fixtures 文件格式不合法，期望 list 或包含 cases/runs 的字典")
    return index_runs_by_case_id(item for item in items if isinstance(item, Mapping))


def _collect_live_runs(
    cases: List[Dict[str, Any]],
    db_path: str,
) -> Dict[str, Dict[str, Any]]:
    """Run live three-engine replay for fixed cases."""
    # Delayed import so fixture mode does not depend on heavy runtime modules.
    try:
        from InsightEngine.agent import create_agent as create_insight_agent
        from MediaEngine.agent import create_agent as create_media_agent
        from QueryEngine.agent import create_agent as create_query_agent
        from veyrafish_core.dispatcher import ResearchDispatcher
    except Exception as exc:
        runs: Dict[str, Dict[str, Any]] = {}
        for case in cases:
            case_id = str(case.get("case_id", "")).strip()
            query = str(case.get("query", "")).strip()
            required_engines = case.get("required_engines") or ["insight", "media", "query"]
            runs[case_id] = {
                "case_id": case_id,
                "query": query,
                "engine_outputs": {str(engine): "" for engine in required_engines},
                "errors": {"live_setup": str(exc)},
                "evidence": {"task_ids": [], "total_count": 0, "aggregates": {}, "top_claims": []},
            }
        return runs

    dispatcher = ResearchDispatcher(max_workers=3)
    store = get_evidence_store(db_path)
    runs: Dict[str, Dict[str, Any]] = {}

    for case in cases:
        case_id = str(case.get("case_id", "")).strip()
        query = str(case.get("query", "")).strip()
        if not case_id or not query:
            continue

        required_engines = [str(item) for item in (case.get("required_engines") or [])]
        if not required_engines:
            required_engines = ["insight", "media", "query"]

        try:
            agents = {
                "insight": create_insight_agent(),
                "media": create_media_agent(),
                "query": create_query_agent(),
            }
            task_ids = {
                engine: f"phase25-{engine}-{uuid.uuid4().hex[:10]}"
                for engine in agents.keys()
            }

            result = dispatcher.dispatch(
                query=query,
                agents=agents,
                task_ids=task_ids,
                save_report=False,
            )
            errors = result.get("_errors", {})
            engine_outputs = {engine: result.get(engine, "") for engine in agents.keys()}
            evidence_context = _build_evidence_context(store, task_ids)

            runs[case_id] = {
                "case_id": case_id,
                "query": query,
                "task_ids": task_ids,
                "engine_outputs": engine_outputs,
                "errors": errors,
                "evidence": evidence_context,
            }
        except Exception as exc:
            runs[case_id] = {
                "case_id": case_id,
                "query": query,
                "engine_outputs": {engine: "" for engine in required_engines},
                "errors": {"dispatch_error": str(exc)},
                "evidence": {"task_ids": [], "total_count": 0, "aggregates": {}, "top_claims": []},
            }
    return runs


def _build_evidence_context(store: Any, task_ids: Mapping[str, str]) -> Dict[str, Any]:
    aggregates: Dict[str, Any] = {}
    top_claims: List[str] = []
    total_count = 0

    for task_id in task_ids.values():
        try:
            aggregate = store.aggregate(task_id)
            aggregate_dict = aggregate.model_dump()
            aggregates[task_id] = aggregate_dict
            total_count += int(aggregate.total_count)
            top_claims.extend(list(aggregate.top_claims or []))
        except Exception as exc:
            aggregates[task_id] = {"error": str(exc)}

    return {
        "task_ids": list(task_ids.values()),
        "total_count": total_count,
        "aggregates": aggregates,
        "top_claims": top_claims[:20],
    }


def _write_report_markdown(result: Dict[str, Any], target: Path, mode: str) -> None:
    lines = [
        "# Phase 2.5 Replay Report",
        "",
        f"- Generated At: {datetime.now().isoformat(timespec='seconds')}",
        f"- Mode: {mode}",
        "",
        "## Summary",
        "",
    ]

    summary = result.get("summary", {})
    lines.append(f"- Total Cases: {summary.get('total_cases', 0)}")
    lines.append(f"- Passed Cases: {summary.get('passed_cases', 0)}")
    lines.append(f"- Failed Cases: {summary.get('failed_cases', 0)}")
    lines.append(f"- Pass Rate: {summary.get('pass_rate', 0.0)}")
    lines.append(f"- Avg Overall Score: {summary.get('avg_overall_score', 0.0)}")
    lines.extend(["", "## Case Scores", ""])
    lines.append("| Case ID | Score | Status | Missing Engines |")
    lines.append("| --- | ---: | --- | --- |")
    for item in result.get("cases", []):
        status = "PASS" if item.get("passed") else "FAIL"
        missing = ", ".join(item.get("missing_engines", []))
        lines.append(
            f"| {item.get('case_id', '')} | {item.get('overall_score', 0.0)} | "
            f"{status} | {missing or '-'} |"
        )
    lines.append("")
    lines.append("## Dimension Details")
    lines.append("")
    for item in result.get("cases", []):
        lines.append(f"### {item.get('case_id', '')}")
        dimensions = item.get("dimensions", {})
        for name, payload in dimensions.items():
            score = payload.get("score", 0.0)
            threshold = payload.get("threshold", 0.0)
            passed = payload.get("passed", False)
            lines.append(
                f"- {name}: score={score} threshold={threshold} passed={passed}"
            )
        lines.append("")

    target.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = _parse_args()

    cases_path = Path(args.cases)
    fixtures_path = Path(args.fixtures)
    output_root = Path(args.output_root)

    if not cases_path.exists():
        raise FileNotFoundError(f"cases 文件不存在: {cases_path}")
    if args.mode == "fixture" and not fixtures_path.exists():
        raise FileNotFoundError(f"fixtures 文件不存在: {fixtures_path}")

    cases = _ensure_cases(_load_json(cases_path))
    if args.max_cases and args.max_cases > 0:
        cases = cases[: args.max_cases]

    if args.mode == "fixture":
        runs_by_case_id = _collect_fixture_runs(fixtures_path)
    else:
        runs_by_case_id = _collect_live_runs(cases=cases, db_path=args.db_path)

    evaluation = evaluate_replay_run(cases=cases, runs_by_case_id=runs_by_case_id)

    run_dir = output_root / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    input_payload = {
        "mode": args.mode,
        "cases": cases,
        "runs_by_case_id": runs_by_case_id,
    }
    (run_dir / "replay_input.json").write_text(
        json.dumps(input_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "evaluation.json").write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_report_markdown(evaluation, run_dir / "report.md", mode=args.mode)

    summary = evaluation.get("summary", {})
    print(
        f"[phase25-replay] total={summary.get('total_cases', 0)} "
        f"passed={summary.get('passed_cases', 0)} "
        f"failed={summary.get('failed_cases', 0)} "
        f"pass_rate={summary.get('pass_rate', 0.0)}"
    )
    print(f"[phase25-replay] report_dir={run_dir}")

    if args.strict and summary.get("failed_cases", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
