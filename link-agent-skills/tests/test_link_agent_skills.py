#!/usr/bin/env python3
"""Tests for link_agent_skills."""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from link_agent_skills import (
    Action,
    LinkResult,
    clean_broken_symlinks,
    link_skill,
    main,
    sync_skills,
)


class TestLinkAgentSkills(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base = Path(self.temp_dir.name)
        self.source_dir = self.base / "agents" / "skills"
        self.target_dir = self.base / "gemini" / "config" / "skills"
        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.target_dir.mkdir(parents=True, exist_ok=True)

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
        res = link_skill("skill-a", self.source_dir, self.target_dir)

        self.assertEqual(res.action, Action.CREATED)
        target_path = self.target_dir / "skill-a"
        self.assertTrue(target_path.is_symlink())
        self.assertEqual(target_path.resolve(), (self.source_dir / "skill-a").resolve())

    def test_skip_already_linked(self) -> None:
        """Skill that is already symlinked to source should be skipped."""
        self.create_source_skill("skill-a")
        # First link
        res1 = link_skill("skill-a", self.source_dir, self.target_dir)
        self.assertEqual(res1.action, Action.CREATED)

        # Second link (idempotent)
        res2 = link_skill("skill-a", self.source_dir, self.target_dir)
        self.assertEqual(res2.action, Action.SKIPPED_ALREADY_LINKED)
        target_path = self.target_dir / "skill-a"
        self.assertTrue(target_path.is_symlink())

    def test_replace_existing_real_directory(self) -> None:
        """If antigravity has an existing real directory, delete it and create symlink."""
        self.create_source_skill("skill-a")
        target_real_dir = self.target_dir / "skill-a"
        target_real_dir.mkdir(parents=True, exist_ok=True)
        (target_real_dir / "old_file.txt").write_text("old content", encoding="utf-8")

        res = link_skill("skill-a", self.source_dir, self.target_dir)

        self.assertEqual(res.action, Action.REPLACED_REAL_DIRECTORY)
        self.assertTrue(target_real_dir.is_symlink())
        self.assertEqual(target_real_dir.resolve(), (self.source_dir / "skill-a").resolve())
        self.assertFalse((target_real_dir / "old_file.txt").exists())
        self.assertTrue((target_real_dir / "SKILL.md").exists())

    def test_replace_existing_real_file(self) -> None:
        """If target exists as a regular file, remove it and create symlink."""
        self.create_source_skill("skill-a")
        target_file = self.target_dir / "skill-a"
        target_file.write_text("not a dir", encoding="utf-8")

        res = link_skill("skill-a", self.source_dir, self.target_dir)

        self.assertEqual(res.action, Action.REPLACED_REAL_FILE)
        self.assertTrue(target_file.is_symlink())
        self.assertEqual(target_file.resolve(), (self.source_dir / "skill-a").resolve())

    def test_update_mismatched_symlink(self) -> None:
        """If target is a symlink pointing to another path, replace it with correct symlink."""
        self.create_source_skill("skill-a")
        other_dir = self.base / "other_skills" / "skill-a"
        other_dir.mkdir(parents=True, exist_ok=True)
        target_symlink = self.target_dir / "skill-a"
        target_symlink.symlink_to(other_dir)

        res = link_skill("skill-a", self.source_dir, self.target_dir)

        self.assertEqual(res.action, Action.UPDATED_SYMLINK)
        self.assertTrue(target_symlink.is_symlink())
        self.assertEqual(target_symlink.resolve(), (self.source_dir / "skill-a").resolve())

    def test_fix_broken_symlink(self) -> None:
        """If target is a broken symlink (points to deleted path), fix it."""
        self.create_source_skill("skill-a")
        target_symlink = self.target_dir / "skill-a"
        non_existent = self.base / "does_not_exist"
        target_symlink.symlink_to(non_existent)

        res = link_skill("skill-a", self.source_dir, self.target_dir)

        self.assertEqual(res.action, Action.UPDATED_SYMLINK)
        self.assertTrue(target_symlink.is_symlink())
        self.assertEqual(target_symlink.resolve(), (self.source_dir / "skill-a").resolve())

    def test_dry_run_mode(self) -> None:
        """Dry-run should not make any modifications."""
        self.create_source_skill("skill-a")
        target_real_dir = self.target_dir / "skill-a"
        target_real_dir.mkdir(parents=True, exist_ok=True)
        (target_real_dir / "dummy.txt").write_text("dummy", encoding="utf-8")

        res = link_skill("skill-a", self.source_dir, self.target_dir, dry_run=True)

        self.assertEqual(res.action, Action.REPLACED_REAL_DIRECTORY)
        # Should NOT be a symlink because dry_run=True
        self.assertFalse(target_real_dir.is_symlink())
        self.assertTrue((target_real_dir / "dummy.txt").exists())

    def test_sync_all_skills(self) -> None:
        """Sync should process all skills in source directory."""
        self.create_source_skill("skill-1")
        self.create_source_skill("skill-2")
        self.create_source_skill("skill-3")

        # Make skill-2 already linked
        (self.target_dir / "skill-2").symlink_to(self.source_dir / "skill-2")

        # Make skill-3 an existing directory
        (self.target_dir / "skill-3").mkdir(parents=True, exist_ok=True)

        results = sync_skills(self.source_dir, self.target_dir)

        self.assertEqual(len(results), 3)
        actions = {r.skill_name: r.action for r in results}
        self.assertEqual(actions["skill-1"], Action.CREATED)
        self.assertEqual(actions["skill-2"], Action.SKIPPED_ALREADY_LINKED)
        self.assertEqual(actions["skill-3"], Action.REPLACED_REAL_DIRECTORY)

    def test_clean_broken_symlinks(self) -> None:
        """clean_broken_symlinks should remove dead links in target."""
        self.create_source_skill("skill-valid")
        (self.target_dir / "skill-valid").symlink_to(self.source_dir / "skill-valid")

        broken = self.target_dir / "skill-broken"
        broken.symlink_to(self.base / "ghost_skill")

        cleaned = clean_broken_symlinks(self.target_dir)
        self.assertEqual(cleaned, ["skill-broken"])
        self.assertFalse(broken.is_symlink())
        self.assertFalse(broken.exists())
        self.assertTrue((self.target_dir / "skill-valid").exists())

    def test_nonexistent_source_skill(self) -> None:
        """Linking a non-existent skill returns failed result."""
        res = link_skill("skill-missing", self.source_dir, self.target_dir)
        self.assertEqual(res.action, Action.FAILED)

    def test_cli_json_output(self) -> None:
        """CLI with --json should return parseable JSON."""
        self.create_source_skill("skill-cli")
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            ret = main(["--source", str(self.source_dir), "--target", str(self.target_dir), "--json"])
        self.assertEqual(ret, 0)
        data = json.loads(stdout.getvalue())
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["skill_name"], "skill-cli")
        self.assertEqual(data["results"][0]["action"], "created")

    def test_cli_single_skill(self) -> None:
        """CLI with --skill flag only links specified skill."""
        self.create_source_skill("skill-one")
        self.create_source_skill("skill-two")
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            ret = main([
                "--source", str(self.source_dir),
                "--target", str(self.target_dir),
                "--skill", "skill-one",
                "--json",
            ])
        self.assertEqual(ret, 0)
        data = json.loads(stdout.getvalue())
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["skill_name"], "skill-one")


if __name__ == "__main__":
    unittest.main()
