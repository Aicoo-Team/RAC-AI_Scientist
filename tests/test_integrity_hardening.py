import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from rac_ai_scientist.config import validate_config
from rac_ai_scientist.hosts.ark import ArkBridge
from rac_ai_scientist.schemas import Budget, CoordinationDecision, Action, InvocationResult


class IntegrityHardeningTests(unittest.TestCase):
    def test_ark_native_completion_is_terminal_independent_of_r3_advisory(self):
        bridge = object.__new__(ArkBridge)
        bridge.terminal = False
        bridge.open_issues = [object()]
        bridge._pending_transition = ("planner", [object()])
        bridge._publish_evaluation = Mock()
        result = InvocationResult("reviewer", "Score: 9/10", [], [], proposed_done=True)
        advisory = CoordinationDecision(Action.REVERIFY, None, "verification advisory")

        bridge.accept_invocation(result, advisory)

        self.assertTrue(bridge.terminal)
        self.assertEqual(bridge.open_issues, [])
        self.assertIsNone(bridge._pending_transition)
        bridge._publish_evaluation.assert_called_once_with(advisory, None)

    def test_doctor_rejects_structurally_incomplete_configuration(self):
        findings = validate_config(
            {
                "schema_version": 1,
                "experiment_id": "demo",
                "conditions": ["N0"],
                "hosts": [],
                "tasks": ["Math_000"],
                "model": {"name": "model"},
                "budget": {},
                "paths": {},
            },
            Path.cwd(),
        )
        messages = "\n".join(item.message for item in findings)
        self.assertIn("hosts must not be empty", messages)
        self.assertIn("budget is missing limits", messages)
        self.assertIn("seeds", messages)
        self.assertIn("run_root path is required", messages)
        self.assertFalse(any(item.level == "OK" for item in findings))

    def test_complete_configuration_passes_structural_validation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "upstreams" / "researchclawbench").mkdir(parents=True)
            config = {
                "schema_version": 1,
                "experiment_id": "demo",
                "hosts": ["ark"],
                "conditions": ["N0"],
                "tasks": ["Math_000"],
                "seeds": [0],
                "repeats": 1,
                "max_parallel_episodes": 1,
                "model": {"name": "model"},
                "budget": {
                    "max_provider_cost_usd": 1,
                    "max_input_tokens": 1,
                    "max_output_tokens": 1,
                    "max_agent_calls": 1,
                    "max_wall_seconds": 1,
                    "max_hops": 1,
                },
                "paths": {
                    "upstream_root": "upstreams",
                    "benchmark": "upstreams/researchclawbench",
                    "run_root": "runs",
                },
            }
            findings = validate_config(config, root)

        self.assertEqual([(item.level, item.message) for item in findings], [
            ("OK", "configuration is ready for a dry-run")
        ])

    def test_compose_mounts_only_the_selected_cell_root(self):
        compose = (Path(__file__).parents[1] / "compose.yaml").read_text(encoding="utf-8")
        self.assertIn("${CELL_RUN_ROOT:-./runs/current-cell}:/runs", compose)
        self.assertNotIn("${RUN_ROOT:-./runs}:/runs", compose)
        self.assertIn("RAC_IMAGE_ID: ${RAC_IMAGE_ID:-}", compose)
        self.assertIn("SCORER_IMAGE_ID: ${SCORER_IMAGE_ID:-}", compose)


if __name__ == "__main__":
    unittest.main()
