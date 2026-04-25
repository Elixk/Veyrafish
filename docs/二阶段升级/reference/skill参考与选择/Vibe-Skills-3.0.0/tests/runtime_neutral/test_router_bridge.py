from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BRIDGE_SCRIPT = REPO_ROOT / "scripts" / "router" / "invoke-pack-route.py"
ROUTE_FIXTURE = REPO_ROOT / "tests" / "replay" / "route" / "recovery-wave-curated-prompts.json"
PLATFORM_FIXTURE = REPO_ROOT / "tests" / "replay" / "platform" / "linux-without-pwsh.json"


def run_bridge(prompt: str, grade: str, task_type: str, requested_skill: str | None = None) -> dict:
    command = [
        sys.executable,
        str(BRIDGE_SCRIPT),
        "--prompt",
        prompt,
        "--grade",
        grade,
        "--task-type",
        task_type,
        "--force-runtime-neutral",
    ]
    if requested_skill:
        command.extend(["--requested-skill", requested_skill])
    completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return json.loads(completed.stdout)


class RouterBridgeTests(unittest.TestCase):
    def test_linux_without_pwsh_fixture_points_to_bridge_contract(self) -> None:
        platform = json.loads(PLATFORM_FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual("linux_without_pwsh", platform["lane"])
        self.assertEqual("scripts/router/invoke-pack-route.py", platform["entry_script"])
        self.assertTrue(platform["constraints"]["force_runtime_neutral"])
        self.assertFalse(platform["constraints"]["requires_powershell_host"])

    def test_runtime_neutral_bridge_satisfies_curated_route_cases(self) -> None:
        fixture = json.loads(ROUTE_FIXTURE.read_text(encoding="utf-8"))
        for case in fixture["cases"]:
            with self.subTest(case=case["id"]):
                result = run_bridge(case["prompt"], case["grade"], case["task_type"])
                expected = case["expected"]

                self.assertIn("route_mode", result)
                self.assertIn("route_reason", result)
                self.assertIn("selected", result)
                self.assertIn("ranked", result)
                self.assertIn("runtime_neutral_bridge", result)
                self.assertEqual("python", result["runtime_neutral_bridge"]["engine"])

                if "route_mode" in expected:
                    self.assertEqual(expected["route_mode"], result["route_mode"])
                if "allowed_route_modes" in expected:
                    self.assertIn(result["route_mode"], expected["allowed_route_modes"])
                if "selected_pack" in expected:
                    self.assertEqual(expected["selected_pack"], result["selected"]["pack_id"])
                if "selected_skill" in expected:
                    self.assertEqual(expected["selected_skill"], result["selected"]["skill"])

    def test_confirm_required_returns_confirm_ui(self) -> None:
        result = run_bridge(
            "create PRD and user story backlog with quality gate",
            "L",
            "planning",
        )
        if result["route_mode"] == "confirm_required":
            self.assertIn("confirm_ui", result)
            self.assertTrue(result["confirm_ui"]["enabled"])
            self.assertGreaterEqual(len(result["confirm_ui"]["options"]), 1)

    def test_requested_vibe_can_preserve_runtime_authority_while_router_selects_specialist(self) -> None:
        result = run_bridge(
            "I have a failing test and a stack trace. Help me debug systematically before proposing fixes.",
            "XL",
            "debug",
            requested_skill="vibe",
        )

        self.assertEqual("confirm_required", result["route_mode"])
        self.assertEqual("code-quality", result["selected"]["pack_id"])
        self.assertEqual("systematic-debugging", result["selected"]["skill"])
        self.assertEqual("vibe", result["alias"]["requested_canonical"])
        self.assertEqual("vibe", result["ranked"][1]["selected_candidate"])
        self.assertIn("confirm_ui", result)
        self.assertTrue(result["confirm_ui"]["enabled"])


if __name__ == "__main__":
    unittest.main()
