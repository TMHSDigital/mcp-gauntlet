"""CLI report selection against an append-only log, with no live agents."""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mcp_gauntlet.cli import main  # noqa: E402


class ReportFilterTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.log = Path(tmp.name) / "events.jsonl"
        events = []
        for run, scenario, ts, outcome in (
            ("old", "rug-pull", "2026-11-20T10:00:00+00:00", "triggered"),
            ("current", "rug-pull", "2026-11-21T10:00:00+00:00", "tool_call"),
            ("other", "result-injection", "2026-11-22T10:00:00+00:00", None),
        ):
            events.extend([
                {"run": run, "kind": "run_start", "seq": 1, "ts": ts, "scenario": scenario},
                {"run": run, "kind": "payload_delivered", "seq": 2},
            ])
            if outcome:
                events.append({"run": run, "kind": outcome, "seq": 3})
        self.log.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")

    def report(self, *args: str) -> tuple[int, list[dict]]:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(["report", str(self.log), "--json", *args])
        return code, json.loads(stdout.getvalue())

    def test_no_filters_keeps_worst_verdict(self) -> None:
        code, runs = self.report()
        self.assertEqual(code, 1)
        self.assertEqual([r["run"] for r in runs], ["old", "current", "other"])

    def test_run_selects_output_and_exit_code(self) -> None:
        code, runs = self.report("--run", "current")
        self.assertEqual(code, 0)
        self.assertEqual([r["run"] for r in runs], ["current"])

    def test_repeated_runs_are_alternatives(self) -> None:
        code, runs = self.report("--run", "current", "--run", "other")
        self.assertEqual(code, 2)
        self.assertEqual([r["run"] for r in runs], ["current", "other"])

    def test_scenario_selects_output_and_exit_code(self) -> None:
        code, runs = self.report("--scenario", "result-injection")
        self.assertEqual(code, 2)
        self.assertEqual([r["run"] for r in runs], ["other"])

    def test_repeated_scenarios_are_alternatives(self) -> None:
        code, runs = self.report("--scenario", "rug-pull", "--scenario", "result-injection")
        self.assertEqual(code, 1)
        self.assertEqual(len(runs), 3)

    def test_since_is_inclusive_and_compares_instants(self) -> None:
        for timestamp in ("2026-11-21T10:00:00Z", "2026-11-21T12:00:00+02:00"):
            with self.subTest(timestamp=timestamp):
                code, runs = self.report("--since", timestamp)
                self.assertEqual(code, 2)
                self.assertEqual([r["run"] for r in runs], ["current", "other"])

    def test_since_uses_run_start_not_later_events(self) -> None:
        with self.log.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"run": "old", "kind": "tool_call", "seq": 4,
                                "ts": "2026-11-23T10:00:00+00:00"}) + "\n")
        code, runs = self.report("--since", "2026-11-21T10:00:00+00:00", "--last")
        self.assertEqual(code, 2)
        self.assertEqual([r["run"] for r in runs], ["other"])

    def test_last_selects_last_matching_run(self) -> None:
        code, runs = self.report("--scenario", "rug-pull", "--last")
        self.assertEqual(code, 0)
        self.assertEqual([r["run"] for r in runs], ["current"])

    def test_filter_types_combine_as_intersections(self) -> None:
        code, runs = self.report("--run", "current", "--run", "other",
                                 "--scenario", "rug-pull", "--since", "2026-11-21T10:00:00Z")
        self.assertEqual(code, 0)
        self.assertEqual([r["run"] for r in runs], ["current"])

    def test_no_match_is_inconclusive(self) -> None:
        for args in (("--run", "missing"), ("--scenario", "missing"),
                     ("--since", "2026-11-25T00:00:00Z")):
            with self.subTest(args=args):
                self.assertEqual(self.report(*args), (2, []))
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    code = main(["report", str(self.log), *args])
                self.assertEqual(code, 2)
                self.assertIn("No runs found", stdout.getvalue())

    def test_invalid_since_is_a_usage_error(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
            main(["report", str(self.log), "--since", "yesterday"])
        self.assertEqual(error.exception.code, 2)
        self.assertIn("ISO 8601", stderr.getvalue())

    def test_naive_since_uses_local_timezone(self) -> None:
        from datetime import datetime
        local = datetime.fromisoformat("2026-11-21T10:00:00+00:00").astimezone()
        _, runs = self.report("--since", local.replace(tzinfo=None).isoformat())
        self.assertEqual([r["run"] for r in runs], ["current", "other"])

    def test_bad_log_timestamp_is_not_a_pass(self) -> None:
        events = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]
        events[0]["ts"] = "broken"
        self.log.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(["report", str(self.log), "--since", "2026-11-21T10:00:00Z"])
        self.assertEqual(code, 2)
        self.assertIn("invalid timestamp", stderr.getvalue())
        self.assertEqual(stdout.getvalue(), "")
