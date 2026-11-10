import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from reputation_monitor.coverage import GROUPS, MAX_INPUT_BYTES, check, load_json, template


# Unit tests must not require a real, current business watch plan.  These IDs
# and dates are synthetic test data and never become production case evidence.
TEST_PLAN = {
    "watch_id": "fable-labs-synthetic-test",
    "review_after": "2026-09-23T00:00:00+08:00",
    "surfaces": [{"id": "fixture-x-posts"}, {"id": "fixture-comments"}],
    "topics": [{"id": "fixture-topic"}],
    "active_cases": [{"id": "DEMO-001"}],
}


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.plan = copy.deepcopy(TEST_PLAN)
        self.record = template(self.plan)
        self.record.update(started_at="2026-09-22T05:00:00+08:00",
                           ended_at="2026-09-22T05:30:00+08:00")
        for group in GROUPS:
            for item in self.record[group]:
                item.update(status="checked", observed_at="2026-09-22T05:10:00+08:00",
                            summary="Synthetic test observation, not live evidence.",
                            links=["https://example.org/test-evidence"])
                if group == "active_cases":
                    item.update(case_state="unresolved", next_check="Read original replies.")

    def test_documented_does_not_mean_risk_free(self):
        self.assertEqual(check(self.plan, self.record)["status"], "documented")
        self.assertNotIn("risk", check(self.plan, self.record))

    def test_empty_template_cannot_pass(self):
        self.assertTrue(check(self.plan, template(self.plan))["errors"])

    def test_partial_is_valid_not_blocker(self):
        self.record["surfaces"][0].update(status="partial", reason="Recovery notice inaccessible.")
        result = check(self.plan, self.record)
        self.assertEqual(result["status"], "partial")
        self.assertFalse(result["errors"])

    def test_gap_does_not_require_fabricated_read(self):
        self.record["surfaces"][0].update(status="gap", links=[], observed_at="",
                                          reason="Stage budget exhausted.")
        self.assertFalse(check(self.plan, self.record)["errors"])

    def test_omitted_comments_or_case_fails(self):
        for group in ("surfaces", "active_cases"):
            record = copy.deepcopy(self.record)
            record[group].pop()
            self.assertTrue(check(self.plan, record)["errors"])

    def test_checked_requires_url_and_current_observation(self):
        self.record["surfaces"][0]["links"] = []
        self.assertTrue(check(self.plan, self.record)["errors"])
        self.record["surfaces"][0].update(links=["https://example.org/"],
                                          observed_at="2026-09-21T05:10:00+08:00")
        self.assertTrue(check(self.plan, self.record)["errors"])

    def test_resolved_requires_evidence(self):
        self.record["active_cases"][0]["case_state"] = "resolved"
        self.assertTrue(check(self.plan, self.record)["errors"])

    def test_known_case_resolution_does_not_require_new_alert(self):
        self.record["active_cases"][0].update(case_state="resolved",
                                               resolution_evidence="User-confirmed resolution, synthetic fixture.")
        self.assertFalse(check(self.plan, self.record)["errors"])
        self.assertEqual(self.record["newSignals"], [])

    def test_unknown_followup_needs_next_action(self):
        self.record["active_cases"][0].update(case_state="unknown", next_check="")
        self.assertTrue(check(self.plan, self.record)["errors"])

    def test_new_case_not_limited_to_initial_seed(self):
        case = copy.deepcopy(self.record["active_cases"][0])
        case["id"] = "DEMO-002"
        self.record["active_cases"].append(case)
        self.assertFalse(check(self.plan, self.record)["errors"])

    def test_same_source_can_cover_multiple_topics(self):
        self.assertFalse(check(self.plan, self.record)["errors"])

    def test_stale_plan_warns_without_auto_closure(self):
        self.plan["review_after"] = "2026-09-21T13:00:00+08:00"
        result = check(self.plan, self.record)
        self.assertTrue(result["warnings"])
        self.assertFalse(result["errors"])
        self.assertEqual(self.record["active_cases"][0]["case_state"], "unresolved")

    def test_reversed_window_rejected(self):
        self.record["ended_at"] = "2026-09-21T05:30:00+08:00"
        self.assertTrue(check(self.plan, self.record)["errors"])

    def test_not_applicable_requires_reason(self):
        self.record["topics"][0].update(status="not_applicable", reason="")
        self.assertTrue(check(self.plan, self.record)["errors"])

    def test_duplicate_case_rejected(self):
        self.record["active_cases"].append(copy.deepcopy(self.record["active_cases"][0]))
        self.assertTrue(check(self.plan, self.record)["errors"])

    def test_wrong_root_types_are_results_not_exceptions(self):
        for bad in (None, [], "record", 4, True):
            with self.subTest(value=bad):
                self.assertEqual(check(self.plan, bad)["status"], "incomplete")
                self.assertEqual(check(bad, self.record)["status"], "incomplete")

    def test_malformed_plan_rejected_before_template_or_check(self):
        for field, value in (("watch_id", None), ("review_after", "2026-09-01"),
                             ("surfaces", [{"id": []}]), ("topics", []),
                             ("active_cases", None)):
            with self.subTest(field=field):
                plan = copy.deepcopy(self.plan)
                plan[field] = value
                self.assertTrue(check(plan, self.record)["errors"])
                with self.assertRaises(ValueError):
                    template(plan)

    def test_malformed_item_fields_fail_without_traceback(self):
        for field, value in (("id", []), ("id", " "), ("status", []),
                             ("summary", 3), ("reason", None), ("links", {}),
                             ("observed_at", [])):
            with self.subTest(field=field, value=value):
                record = copy.deepcopy(self.record)
                record["surfaces"][0][field] = value
                self.assertTrue(check(self.plan, record)["errors"])

    def test_all_links_must_be_valid_and_must_not_contain_credentials(self):
        for link in ("https://[bad", "https://example.org:bad/", "https://user:secret@example.org/",
                     "javascript:alert(1)", "https://example.org/\nprivate", None, "https://"):
            with self.subTest(link=link):
                record = copy.deepcopy(self.record)
                record["surfaces"][0]["links"].append(link)
                self.assertTrue(check(self.plan, record)["errors"])

    def test_all_coverage_groups_must_be_explicit_even_if_empty(self):
        plan = copy.deepcopy(self.plan)
        plan["active_cases"] = []
        record = copy.deepcopy(self.record)
        del record["active_cases"]
        self.assertTrue(check(plan, record)["errors"])

    def test_signals_are_objects_and_plan_review_is_text(self):
        for field, value in (("newSignals", ["unstructured signal"]), ("plan_review", [])):
            record = copy.deepcopy(self.record)
            record[field] = value
            self.assertTrue(check(self.plan, record)["errors"])

    def test_gap_cannot_establish_case_resolution(self):
        self.record["active_cases"][0].update(status="gap", links=[], observed_at="",
            reason="Original inaccessible", case_state="resolved", resolution_evidence="No new posts")
        result = check(self.plan, self.record)
        self.assertTrue(any("actual case-evidence read" in error for error in result["errors"]))

    def test_case_closure_and_followup_fields_have_real_types(self):
        for field, value in (("case_state", []), ("next_check", {}),
                             ("resolution_evidence", True), ("lastMaterialUpdate", 123)):
            record = copy.deepcopy(self.record)
            record["active_cases"][0][field] = value
            self.assertTrue(check(self.plan, record)["errors"])

    def test_material_update_can_be_old_but_cannot_be_in_future_or_naive(self):
        case = self.record["active_cases"][0]
        case["lastMaterialUpdate"] = "2026-09-01T00:00:00Z"
        self.assertFalse(check(self.plan, self.record)["errors"])
        for bad in ("2026-10-01T00:00:00Z", "2026-09-01T00:00:00", "unknown"):
            case["lastMaterialUpdate"] = bad
            self.assertTrue(check(self.plan, self.record)["errors"])

    def test_timezone_conversion_is_compared_as_instant(self):
        self.record["surfaces"][0]["observed_at"] = "2026-09-21T21:10:00Z"
        self.assertFalse(check(self.plan, self.record)["errors"])
        self.record["surfaces"][0]["observed_at"] = "2026-09-22T05:10:00"
        self.assertTrue(check(self.plan, self.record)["errors"])

    def test_overrun_is_visible_without_discarding_evidence(self):
        self.record["ended_at"] = "2026-09-22T06:00:00+08:00"
        result = check(self.plan, self.record)
        self.assertEqual(result["status"], "documented")
        self.assertTrue(any("50-minute" in warning for warning in result["warnings"]))


class InputAndCLITests(unittest.TestCase):
    @unittest.skipUnless(hasattr(os, 'mkfifo') and hasattr(os, 'O_NONBLOCK'), 'POSIX FIFO test')
    def test_fifo_cannot_block_cli_waiting_for_a_writer(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'plan.pipe'
            os.mkfifo(path)
            result = subprocess.run([sys.executable, '-B', '-m', 'reputation_monitor',
                                     'template', '--plan', str(path)], capture_output=True, text=True,
                                    check=False, timeout=5)
            self.assertEqual(result.returncode, 2)
            self.assertIn('input_must_be_regular_file', json.loads(result.stderr)['errors'][0])

    def test_rejects_ambiguous_or_unbounded_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            for content in ('{"state":"unknown","state":"resolved"}', '{"x":NaN}',
                            '{"x":1e999}', '{"x":"\\ud800"}',
                            '[' * 2000 + '0' + ']' * 2000, ' ' * (MAX_INPUT_BYTES + 1)):
                with self.subTest(content=content[:60]):
                    path.write_text(content)
                    with self.assertRaises(ValueError):
                        load_json(path)

    def test_cli_input_errors_return_machine_readable_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing-plan.json"
            for content in (None, '{', '[]', '{"x":Infinity}'):
                if content is not None:
                    path.write_text(content)
                result = subprocess.run([sys.executable, '-B', '-m', 'reputation_monitor',
                                         'template', '--plan', str(path)],
                                        capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(json.loads(result.stderr)["status"], "input_error")
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
