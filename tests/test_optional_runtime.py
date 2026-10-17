"""Real optional framework checks; skipped when the framework is not installed.

These use synthetic local outputs and no model API. A skip is not a validation
pass. Harbor's schema check does not start Docker or validate its networking.
Pinned dependency targets and primary API references are in docs/harnesses.md.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[1]


def installed(name):
    return importlib.util.find_spec(name) is not None


@unittest.skipUnless(installed("inspect_ai"), "inspect-ai not installed: real runtime not validated")
class InspectRuntime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "nrb_optional_inspect_eval", REPO / "adapters" / "inspect_ai" / "nrb_eval.py")
        cls.adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.adapter)

    def run_sample(self, task_id, submission):
        from inspect_ai import Task, eval as inspect_eval
        from inspect_ai.dataset import Sample
        from inspect_ai.model import ModelOutput, get_model
        from inspect_ai.solver import generate
        from nrb.adapters import inspect_samples

        record = next(row for row in inspect_samples(0) if row["id"] == task_id)
        task = Task(dataset=[Sample(**record)], solver=generate(),
                    scorer=self.adapter.nrb_automatic("none"),
                    name="nrb-optional-runtime", metadata={"not_model_performance": True})
        model = get_model("mockllm/model", custom_outputs=[
            ModelOutput.from_content("mockllm/model", json.dumps(submission, ensure_ascii=False))])
        with tempfile.TemporaryDirectory(prefix="nrb-inspect-runtime-") as logs:
            with patch.dict(os.environ, {"INSPECT_DISABLE_MODEL_API": "1"}):
                results = inspect_eval(task, model=model, display="none", log_dir=logs,
                                       max_samples=1, log_samples=True)
            self.assertEqual(len(results), 1)
            result = results[0]
            self.assertEqual(result.status, "success", str(result.error))
            self.assertEqual(len(result.samples), 1)
            self.assertEqual(len(result.samples[0].scores), 1)
            score = next(iter(result.samples[0].scores.values()))
            # Returned EvalLog data is fully loaded before the temporary log is removed.
            return score, result

    def test_actual_task_construction_keeps_targets_blank(self):
        from inspect_ai import Task
        task = self.adapter.null_research(seed=0, execution="none")
        self.assertIsInstance(task, Task)
        self.assertEqual(len(task.dataset), 10)
        self.assertTrue(all(sample.target == "" for sample in task.dataset))

    def test_actual_mock_model_eval_positive_and_negative(self):
        from nrb.core import get_case, reference_submission
        from nrb.adapters import summarize_inspect_log
        positive = reference_submission(get_case("NRB01", 0))
        score, log = self.run_sample("NRB01", positive)
        self.assertEqual(score.value, 1.0)
        self.assertEqual(score.metadata["nrb_report"]["auto_points"], 70)
        self.assertTrue(score.metadata["nrb_report"]["review_pending"])
        summary = summarize_inspect_log(log)
        self.assertFalse(summary["complete_auto"])
        self.assertEqual(len(summary["missing_tasks"]), 9)
        self.assertEqual(summary["model_label"], "mockllm/model")
        self.assertEqual(summary["harness_label"], "inspect_ai")
        self.assertTrue(summary["metadata"]["harness_version"])
        self.assertIsInstance(summary["metadata"]["model_generate_config"], dict)
        self.assertTrue(summary["metadata"]["plan_steps"])
        self.assertTrue(summary["not_model_performance"])
        self.assertTrue(summary["metadata_incomplete"])
        score, _ = self.run_sample("NRB01", {"task_id": "NRB01", "answer": {}, "artifacts": {}})
        self.assertEqual(score.value, 0.0)

    def test_execution_pending_is_actual_unscored_value(self):
        from nrb.core import get_case, reference_submission
        score, _ = self.run_sample("NRB04", reference_submission(get_case("NRB04", 0)))
        self.assertTrue(math.isnan(float(score.value)))
        self.assertIsNone(score.metadata["nrb_report"]["auto_percent"])


@unittest.skipUnless(installed("harbor"), "Harbor not installed: real schema runtime not validated")
class HarborSchemaRuntime(unittest.TestCase):
    def test_all_exported_tasks_parse_with_real_harbor_model(self):
        from harbor.models.task.config import TaskConfig
        from nrb.adapters import export_harbor
        from nrb.core import build_suite

        with tempfile.TemporaryDirectory(prefix="nrb-harbor-schema-") as temp:
            export_dir = Path(temp) / "tasks"
            export_harbor(build_suite(0), export_dir)
            paths = sorted(export_dir.glob("nrb*/task.toml"))
            self.assertEqual(len(paths), 10)
            for path in paths:
                with self.subTest(task=path.parent.name):
                    config = TaskConfig.model_validate_toml(path.read_text(encoding="utf-8"))
                    data = config.model_dump(mode="json")
                    self.assertEqual(data["schema_version"], "1.4")
                    self.assertEqual(data["verifier"]["environment_mode"], "separate")
                    self.assertEqual(data["verifier"]["environment"]["network_mode"], "no-network")
                    self.assertEqual(data["agent"]["network_mode"], "no-network")
                    self.assertEqual(data["artifacts"], ["/app/"])


if __name__ == "__main__":
    unittest.main()
