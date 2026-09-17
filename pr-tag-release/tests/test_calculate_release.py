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
    count_merged_prs,
    check_tag_collision,
    calculate_current_release,
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

    def test_count_merged_prs(self):
        # When current PR #17 is in the list
        merged_prs = [{"number": 17}, {"number": 11}, {"number": 8}]
        self.assertEqual(count_merged_prs(merged_prs, current_pr_id=17), 3)

        # When current PR #17 is not yet in the list
        merged_prs_before = [{"number": 11}, {"number": 8}]
        self.assertEqual(count_merged_prs(merged_prs_before, current_pr_id=17), 3)

        # When merged_prs is empty
        self.assertEqual(count_merged_prs([], current_pr_id=1), 1)

    def test_calculate_current_release(self):
        res = calculate_current_release(
            major=0,
            pr_count=5,
            commits=3,
            pr_id=17,
            pr_title="feat: add login",
            pr_body="Implemented JWT login",
            pr_author="octocat",
            repo_name="forchain/skills",
        )
        self.assertEqual(res["tag_name"], "v0.5.3")
        self.assertEqual(res["release_title"], "v0.5.3 - feat: add login")
        self.assertIn("Implemented JWT login", res["release_body"])
        self.assertIn("@octocat", res["release_body"])
        self.assertIn("#17", res["release_body"])
        self.assertNotIn("overwrites a legacy tag", res["release_body"])

    def test_calculate_current_release_with_collision(self):
        res = calculate_current_release(
            major=0,
            pr_count=5,
            commits=3,
            pr_id=17,
            pr_title="feat: add login",
            pr_body="Implemented JWT login",
            pr_author="octocat",
            repo_name="forchain/skills",
            is_collision=True,
        )
        self.assertEqual(res["tag_name"], "v0.5.3")
        self.assertIn("overwrites a legacy tag", res["release_body"])

    def test_check_tag_collision(self):
        existing_releases = [
            {"tagName": "v0.5.3", "name": "v0.5.3 - old release"},
            {"tagName": "v0.4.1", "name": "v0.4.1 - setup"},
        ]
        self.assertTrue(check_tag_collision("v0.5.3", existing_releases))
        self.assertFalse(check_tag_collision("v0.6.1", existing_releases))

    def test_plan_release_uses_merged_pr_count(self):
        event_payload = {
            "pull_request": {
                "number": 42,
                "commits": 2,
                "title": "feat: new feature",
                "body": "Resolves #10",
                "user": {"login": "dev_user"},
            },
            "repository": {"full_name": "forchain/skills"},
        }
        # 4 merged PRs exist in repo history + current PR #42 = 5th PR
        merged_prs = [
            {"number": 1},
            {"number": 5},
            {"number": 8},
            {"number": 11},
        ]
        existing_releases = [
            {"tagName": "v0.42.2", "name": "legacy release"}
        ]
        plan = plan_release(
            major_str="0",
            event_payload=event_payload,
            existing_releases=existing_releases,
            merged_prs=merged_prs,
        )
        self.assertEqual(plan["current_pr"]["pr_id"], 42)
        self.assertEqual(plan["current_pr"]["pr_count"], 5)
        self.assertEqual(plan["current_pr"]["commits"], 2)
        self.assertEqual(plan["current_pr"]["tag_name"], "v0.5.2")
        self.assertFalse(plan["is_collision"])
        self.assertNotIn("out_of_order", plan)

    def test_plan_release_detects_collision(self):
        event_payload = {
            "pull_request": {
                "number": 42,
                "commits": 2,
                "title": "feat: colliding feature",
                "body": "",
                "user": {"login": "dev_user"},
            },
            "repository": {"full_name": "forchain/skills"},
        }
        merged_prs = [{"number": 1}, {"number": 2}]
        # Current PR is 3rd PR -> tag v0.3.2
        # But an old release v0.3.2 already exists
        existing_releases = [
            {"tagName": "v0.3.2", "name": "v0.3.2 - old PR #3 release"}
        ]
        plan = plan_release(
            major_str="0",
            event_payload=event_payload,
            existing_releases=existing_releases,
            merged_prs=merged_prs,
        )
        self.assertEqual(plan["current_pr"]["tag_name"], "v0.3.2")
        self.assertTrue(plan["is_collision"])


if __name__ == "__main__":
    unittest.main()
