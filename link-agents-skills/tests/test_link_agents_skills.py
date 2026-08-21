#!/usr/bin/env python3
"""Tests for link_agents_skills."""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from link_agents_skills import (
    AGENT_TARGET_PRESETS,
    Action,
    LinkResult,
    clean_broken_symlinks,
    link_skill,
    main,
    sync_skills,
    sync_to_agents,
)


class TestLinkAgentsSkills(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)
        self.source_dir = self.base / "agents" / "skills"
        self.antigravity_dir = self.base / "gemini" / "config" / "skills"
        self.claude_dir = self.base / "claude" / "skills"

        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.antigravity_dir.mkdir(parents=True, exist_ok=True)
        self.claude_dir.mkdir(parents=True, exist_ok=True)

        self.custom_presets = {
            "antigravity": self.antigravity_dir,
            "claude": self.claude_dir,
        }

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def create_source_skill(self, name: str) -> Path:
        skill_path = self.source_dir / name
        skill_path.mkdir(parents=True, exist_ok=True)
        (skill_path / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Test skill\n---\n# {name}\n", encoding="utf-8")
        return skill_path

    def test_link_new_skill(self) -> None:
        """New skill in source should be symlinked to target."""
        self.create_source_skill("skill-a")
        res = link_skill("skill-a", self.source_dir, self.antigravity_dir)

        self.assertEqual(res.action, Action.CREATED)
        target_path = self.antigravity_dir / "skill-a"
        self.assertTrue(target_path.is_symlink())
        self.assertEqual(target_path.resolve(), (self.source_dir / "skill-a").resolve())

    def test_skip_already_linked(self) -> None:
        """Skill that is already symlinked to source should be skipped."""
        self.create_source_skill("skill-a")
        # First link
        res1 = link_skill("skill-a", self.source_dir, self.antigravity_dir)
        self.assertEqual(res1.action, Action.CREATED)

        # Second link (idempotent)
        res2 = link_skill("skill-a", self.source_dir, self.antigravity_dir)
        self.assertEqual(res2.action, Action.SKIPPED_ALREADY_LINKED)
        target_path = self.antigravity_dir / "skill-a"
        self.assertTrue(target_path.is_symlink())

    def test_replace_existing_real_directory(self) -> None:
        """If target has an existing real directory, delete it and create symlink."""
        self.create_source_skill("skill-a")
        target_real_dir = self.antigravity_dir / "skill-a"
        target_real_dir.mkdir(parents=True, exist_ok=True)
        (target_real_dir / "old_file.txt").write_text("old content", encoding="utf-8")

        res = link_skill("skill-a", self.source_dir, self.antigravity_dir)

        self.assertEqual(res.action, Action.REPLACED_REAL_DIRECTORY)
        self.assertTrue(target_real_dir.is_symlink())
        self.assertEqual(target_real_dir.resolve(), (self.source_dir / "skill-a").resolve())
        self.assertFalse((target_real_dir / "old_file.txt").exists())
        self.assertTrue((target_real_dir / "SKILL.md").exists())

    def test_replace_existing_real_file(self) -> None:
        """If target exists as a regular file, remove it and create symlink."""
        self.create_source_skill("skill-a")
        target_file = self.antigravity_dir / "skill-a"
        target_file.write_text("not a dir", encoding="utf-8")

        res = link_skill("skill-a", self.source_dir, self.antigravity_dir)

        self.assertEqual(res.action, Action.REPLACED_REAL_FILE)
        self.assertTrue(target_file.is_symlink())
        self.assertEqual(target_file.resolve(), (self.source_dir / "skill-a").resolve())

    def test_update_mismatched_symlink(self) -> None:
        """If target is a symlink pointing to another path, replace it with correct symlink."""
        self.create_source_skill("skill-a")
        other_dir = self.base / "other_skills" / "skill-a"
        other_dir.mkdir(parents=True, exist_ok=True)
        target_symlink = self.antigravity_dir / "skill-a"
        target_symlink.symlink_to(other_dir)

        res = link_skill("skill-a", self.source_dir, self.antigravity_dir)

        self.assertEqual(res.action, Action.UPDATED_SYMLINK)
        self.assertTrue(target_symlink.is_symlink())
        self.assertEqual(target_symlink.resolve(), (self.source_dir / "skill-a").resolve())

    def test_fix_broken_symlink(self) -> None:
        """If target is a broken symlink (points to deleted path), fix it."""
        self.create_source_skill("skill-a")
        target_symlink = self.antigravity_dir / "skill-a"
        non_existent = self.base / "does_not_exist"
        target_symlink.symlink_to(non_existent)

        res = link_skill("skill-a", self.source_dir, self.antigravity_dir)

        self.assertEqual(res.action, Action.UPDATED_SYMLINK)
        self.assertTrue(target_symlink.is_symlink())
        self.assertEqual(target_symlink.resolve(), (self.source_dir / "skill-a").resolve())

    def test_dry_run_mode(self) -> None:
        """Dry-run should not make any modifications."""
        self.create_source_skill("skill-a")
        target_real_dir = self.antigravity_dir / "skill-a"
        target_real_dir.mkdir(parents=True, exist_ok=True)
        (target_real_dir / "dummy.txt").write_text("dummy", encoding="utf-8")

        res = link_skill("skill-a", self.source_dir, self.antigravity_dir, dry_run=True)

        self.assertEqual(res.action, Action.REPLACED_REAL_DIRECTORY)
        self.assertFalse(target_real_dir.is_symlink())
        self.assertTrue((target_real_dir / "dummy.txt").exists())

    def test_sync_to_multiple_agents_all(self) -> None:
        """Sync should link skills to all target agent directories."""
        self.create_source_skill("skill-1")
        self.create_source_skill("skill-2")

        results = sync_to_agents(
            source_dir=self.source_dir,
            target_agents=["antigravity", "claude"],
            presets=self.custom_presets,
        )

        self.assertEqual(len(results), 4)  # 2 skills * 2 agents
        self.assertTrue((self.antigravity_dir / "skill-1").is_symlink())
        self.assertTrue((self.antigravity_dir / "skill-2").is_symlink())
        self.assertTrue((self.claude_dir / "skill-1").is_symlink())
        self.assertTrue((self.claude_dir / "skill-2").is_symlink())

    def test_sync_to_single_agent(self) -> None:
        """Sync to only claude should leave antigravity untouched."""
        self.create_source_skill("skill-1")

        results = sync_to_agents(
            source_dir=self.source_dir,
            target_agents=["claude"],
            presets=self.custom_presets,
        )

        self.assertEqual(len(results), 1)
        self.assertTrue((self.claude_dir / "skill-1").is_symlink())
        self.assertFalse((self.antigravity_dir / "skill-1").exists())

    def test_clean_broken_symlinks(self) -> None:
        """clean_broken_symlinks should remove dead links in target."""
        self.create_source_skill("skill-valid")
        (self.antigravity_dir / "skill-valid").symlink_to(self.source_dir / "skill-valid")

        broken = self.antigravity_dir / "skill-broken"
        broken.symlink_to(self.base / "ghost_skill")

        cleaned = clean_broken_symlinks(self.antigravity_dir)
        self.assertEqual(cleaned, ["skill-broken"])
        self.assertFalse(broken.is_symlink())
        self.assertFalse(broken.exists())
        self.assertTrue((self.antigravity_dir / "skill-valid").exists())

    def test_cli_json_multi_agent(self) -> None:
        """CLI with --agent all and --json should return results per agent."""
        self.create_source_skill("skill-cli")
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            ret = main([
                "--source", str(self.source_dir),
                "--target", str(self.claude_dir),
                "--json",
            ])
        self.assertEqual(ret, 0)
        data = json.loads(stdout.getvalue())
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["skill_name"], "skill-cli")
        self.assertEqual(data["results"][0]["agent"], "custom")


if __name__ == "__main__":
    unittest.main()
