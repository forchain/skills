#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


class TestE2ESimulation(unittest.TestCase):
    def test_full_pipeline_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            version_file = tmp_path / "VERSION"
            version_file.write_text("1\n", encoding="utf-8")

            event_file = tmp_path / "event.json"
            event_payload = {
                "pull_request": {
                    "number": 42,
                    "commits": 5,
                    "title": "feat: major redesign",
                    "body": "Detailed redesign notes",
                    "user": {"login": "alice"},
                    "merged": True,
                },
                "repository": {"full_name": "example-org/demo-repo"},
            }
            event_file.write_text(json.dumps(event_payload), encoding="utf-8")

            plan_file = tmp_path / "plan.json"

            # 1. Run calculate_release.py
            calc_cmd = [
                sys.executable,
                str(SCRIPTS_DIR / "calculate_release.py"),
                "--version-file",
                str(version_file),
                "--event-path",
                str(event_file),
                "--output",
                str(plan_file),
            ]
            res_calc = subprocess.run(calc_cmd, capture_output=True, text=True, check=True)
            self.assertTrue(plan_file.exists())

            plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
            self.assertEqual(plan_data["major"], 1)
            self.assertEqual(plan_data["current_pr"]["tag_name"], "v1.42.5")
            self.assertFalse(plan_data["out_of_order"])

            # 2. Run publish_release.py in dry-run mode
            pub_cmd = [
                sys.executable,
                str(SCRIPTS_DIR / "publish_release.py"),
                "--plan",
                str(plan_file),
                "--dry-run",
            ]
            res_pub = subprocess.run(pub_cmd, capture_output=True, text=True, check=True)
            self.assertIn("v1.42.5", res_pub.stdout)
            self.assertIn("Processing Release for PR #42", res_pub.stdout)


if __name__ == "__main__":
    unittest.main()
