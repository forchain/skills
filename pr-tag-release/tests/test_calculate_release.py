#!/usr/bin/env python3
import json
import os
import sys
import unittest
from pathlib import Path

# Add scripts directory to sys.path
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from calculate_release import (
    parse_major_version,
    calculate_current_release,
    detect_and_calculate_backfill,
    plan_release,
)


class TestCalculateRelease(unittest.TestCase):
    def test_parse_major_version_default(self):
        self.assertEqual(parse_major_version(None), 0)
        self.assertEqual(parse_major_version(""), 0)
        self.assertEqual(parse_major_version("  \n"), 0)

    def test_parse_major_version_valid(self):
        self.assertEqual(parse_major_version("0"), 0)
        self.assertEqual(parse_major_version("1\n"), 1)
        self.assertEqual(parse_major_version("  2  "), 2)

    def test_calculate_current_release(self):
        res = calculate_current_release(
            major=0,
            pr_id=17,
            commits=3,
            pr_title="feat: add login",
            pr_body="Implemented JWT login",
            pr_author="octocat",
            repo_name="forchain/skills",
        )
        self.assertEqual(res["tag_name"], "v0.17.3")
        self.assertEqual(res["release_title"], "v0.17.3 - feat: add login")
        self.assertIn("Implemented JWT login", res["release_body"])
        self.assertIn("@octocat", res["release_body"])
        self.assertIn("#17", res["release_body"])

    def test_normal_order_no_backfill(self):
        # PR 17 merges when existing releases are only older (e.g. PR 15, PR 16)
        existing_releases = [
            {"tagName": "v0.15.2", "name": "v0.15.2 - init"},
            {"tagName": "v0.16.1", "name": "v0.16.1 - setup"},
        ]
        backfill = detect_and_calculate_backfill(
            current_major=0,
            current_pr_id=17,
            current_commits=3,
            existing_releases=existing_releases,
        )
        self.assertIsNone(backfill)

    def test_out_of_order_merge_single_higher_pr(self):
        # PR 18 was merged earlier (tag v0.18.2). Now PR 17 merges (3 commits).
        existing_releases = [
            {"tagName": "v0.18.2", "name": "v0.18.2 - feat: payments"},
            {"tagName": "v0.15.1", "name": "v0.15.1 - init"},
        ]
        backfill = detect_and_calculate_backfill(
            current_major=0,
            current_pr_id=17,
            current_commits=3,
            existing_releases=existing_releases,
        )
        self.assertIsNotNone(backfill)
        self.assertEqual(backfill["pr_id"], 18)
        self.assertEqual(backfill["old_tag"], "v0.18.2")
        self.assertEqual(backfill["new_tag"], "v0.18.5")
        self.assertEqual(backfill["commits_added"], 3)
        self.assertIn("PR #17", backfill["pr_body_append"])
        self.assertIn("v0.18.5", backfill["pr_body_append"])

    def test_out_of_order_merge_multiple_higher_prs_picks_highest(self):
        # PR 18 (v0.18.2) and PR 20 (v0.20.4) exist. Now PR 17 merges (3 commits).
        existing_releases = [
            {"tagName": "v0.18.2", "name": "v0.18.2 - feat: payments"},
            {"tagName": "v0.20.4", "name": "v0.20.4 - feat: analytics"},
        ]
        backfill = detect_and_calculate_backfill(
            current_major=0,
            current_pr_id=17,
            current_commits=3,
            existing_releases=existing_releases,
        )
        self.assertIsNotNone(backfill)
        self.assertEqual(backfill["pr_id"], 20)
        self.assertEqual(backfill["old_tag"], "v0.20.4")
        self.assertEqual(backfill["new_tag"], "v0.20.7")

    def test_plan_release_full_payload(self):
        event_payload = {
            "pull_request": {
                "number": 17,
                "commits": 3,
                "title": "feat: add OAuth",
                "body": "Resolves #10",
                "user": {"login": "dev_user"},
            },
            "repository": {"full_name": "forchain/skills"},
        }
        existing_releases = [
            {"tagName": "v0.18.2", "name": "v0.18.2 - higher PR"}
        ]
        plan = plan_release(
            major_str="0",
            event_payload=event_payload,
            existing_releases=existing_releases,
        )
        self.assertEqual(plan["current_pr"]["tag_name"], "v0.17.3")
        self.assertTrue(plan["out_of_order"])
        self.assertEqual(plan["higher_pr_update"]["new_tag"], "v0.18.5")


if __name__ == "__main__":
    unittest.main()
