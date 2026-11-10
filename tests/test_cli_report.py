import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from reputation_monitor.coverage import check, load_json, template
from reputation_monitor.report import render_report

ROOT = Path(__file__).resolve().parents[1]


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.plan = load_json(ROOT / "examples/watch-plan.json")
        self.record = load_json(ROOT / "examples/partial-run.json")

    def test_example_is_partial_without_risk_inference(self):
        verdict = check(self.plan, self.record)
        self.assertEqual(verdict["status"], "partial")
        self.assertFalse(verdict["errors"])
        report = render_report(self.plan, self.record)
        self.assertIn("**Coverage accounting:** partial", report)
        self.assertIn("Open case status", report)
        self.assertNotIn("Overall risk: Green", report)
        self.assertEqual(self.record["active_cases"][0]["case_state"], "unknown")

    def test_report_cannot_bypass_validation_with_forged_result(self):
        self.record["surfaces"] = []
        with self.assertRaises(ValueError):
            render_report(self.plan, self.record, {"errors": [], "status": "documented"})

    def test_html_images_tables_and_markdown_are_literal(self):
        malicious = '<script>alert(1)</script> ![x](https://example.com/tracker) | **risk free**\n# injected'
        self.record["topics"][0]["summary"] = malicious
        self.record["newSignals"] = [{"summary": malicious}]
        report = render_report(self.plan, self.record)
        self.assertNotIn("<script>", report)
        self.assertNotIn("![x](", report)
        self.assertNotIn("\n# injected", report)
        self.assertIn("\\|", report)
        self.assertIn("&lt;script&gt;", report)

    def test_render_is_read_only(self):
        before = copy.deepcopy((self.plan, self.record))
        render_report(self.plan, self.record)
        self.assertEqual(before, (self.plan, self.record))


class CLITests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run([sys.executable, "-B", "-m", "reputation_monitor", *args],
                              cwd=ROOT, capture_output=True, text=True, timeout=15)

    def test_template_has_no_fabricated_reads(self):
        result = self.invoke("template", "--plan", "examples/watch-plan.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["started_at"], "")
        self.assertEqual(data["newSignals"], [])
        self.assertEqual(data["surfaces"][0]["status"], "")

    def test_check_and_report_from_examples(self):
        for mode in ("check", "report"):
            result = self.invoke(mode, "--plan", "examples/watch-plan.json", "--record", "examples/partial-run.json")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("partial", result.stdout)

    def test_unfilled_template_check_and_report_exit_one(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "record.json"
            plan = load_json(ROOT / "examples/watch-plan.json")
            path.write_text(json.dumps(template(plan)))
            for mode in ("check", "report"):
                result = self.invoke(mode, "--plan", "examples/watch-plan.json", "--record", str(path))
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)["status"], "incomplete")
                self.assertNotIn("# Reputation", result.stdout)

    def test_missing_record_argument_is_usage_error(self):
        result = self.invoke("check", "--plan", "examples/watch-plan.json")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    def test_input_error_exit_two(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "record.json"
            path.write_text('{"x":1,"x":2}')
            result = self.invoke("check", "--plan", "examples/watch-plan.json", "--record", str(path))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stderr)["status"], "input_error")


if __name__ == "__main__":
    unittest.main()
