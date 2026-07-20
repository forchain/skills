from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "git_history_repair.py"


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True)


def run_without_check(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


class GitHistoryRepairCliTests(unittest.TestCase):
    def test_audit_reports_exact_identities_non_ascii_messages_and_refs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            run("git", "init", "-q", cwd=repo)
            run("git", "config", "user.name", "Alice", cwd=repo)
            run("git", "config", "user.email", "alice@example.com", cwd=repo)
            (repo / "README.md").write_text("first\n", encoding="utf-8")
            run("git", "add", "README.md", cwd=repo)
            run("git", "commit", "-qm", "Initial commit", cwd=repo)
            run("git", "config", "user.name", "Alice Old", cwd=repo)
            run("git", "config", "user.email", "old@example.com", cwd=repo)
            (repo / "README.md").write_text("second\n", encoding="utf-8")
            run("git", "commit", "-am", "修复播放器", cwd=repo)
            translated_commit = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
            run("git", "tag", "-a", "v0.1.0", "-m", "Initial release", cwd=repo)

            result = run(sys.executable, str(SCRIPT), "audit", "--repo", str(repo), cwd=repo)
            report = json.loads(result.stdout)

            self.assertEqual(report["schema_version"], 1)
            self.assertEqual(report["repository"]["commit_count"], 2)
            self.assertEqual(
                report["identities"]["authors"],
                [
                    {"count": 1, "email": "alice@example.com", "name": "Alice"},
                    {"count": 1, "email": "old@example.com", "name": "Alice Old"},
                ],
            )
            self.assertEqual(
                report["messages"]["non_ascii"],
                [{"commit": translated_commit, "subject": "修复播放器"}],
            )
            self.assertEqual(report["refs"]["tags"], ["refs/tags/v0.1.0"])
            self.assertTrue(report["safety"]["clean_worktree"])

    def test_audit_extracts_an_explicit_github_login_hint_from_origin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            run("git", "init", "-q", cwd=repo)
            run("git", "config", "user.name", "Alice", cwd=repo)
            run("git", "config", "user.email", "alice@example.com", cwd=repo)
            run(
                "git",
                "remote",
                "add",
                "origin",
                "https://forchain@github.com/forchain/example.git",
                cwd=repo,
            )
            (repo / "README.md").write_text("first\n", encoding="utf-8")
            run("git", "add", "README.md", cwd=repo)
            run("git", "commit", "-qm", "Initial commit", cwd=repo)

            result = run(sys.executable, str(SCRIPT), "audit", "--repo", str(repo), cwd=repo)
            report = json.loads(result.stdout)

            self.assertEqual(report["github"]["login_hint"], "forchain")

    def test_apply_requires_a_matching_plan_approval_before_rewriting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            run("git", "init", "-q", cwd=repo)
            run("git", "config", "user.name", "Alice", cwd=repo)
            run("git", "config", "user.email", "alice@example.com", cwd=repo)
            (repo / "README.md").write_text("first\n", encoding="utf-8")
            run("git", "add", "README.md", cwd=repo)
            run("git", "commit", "-qm", "Initial commit", cwd=repo)
            plan = Path(directory) / "plan.json"
            plan.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")

            result = run_without_check(
                sys.executable,
                str(SCRIPT),
                "apply",
                "--repo",
                str(repo),
                "--plan",
                str(plan),
                cwd=repo,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--approval", result.stderr)
            self.assertFalse((repo / "history-repair").exists())

    def test_apply_stops_before_cloning_when_git_filter_repo_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "source"
            repo.mkdir()
            run("git", "init", "-q", cwd=repo)
            run("git", "config", "user.name", "Alice", cwd=repo)
            run("git", "config", "user.email", "alice@example.com", cwd=repo)
            (repo / "README.md").write_text("first\n", encoding="utf-8")
            run("git", "add", "README.md", cwd=repo)
            run("git", "commit", "-qm", "Initial commit", cwd=repo)
            head = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
            plan = Path(directory) / "plan.json"
            plan.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "audit": {"head": head},
                        "refs": ["HEAD"],
                        "canonical_identity": {"name": "Alice", "email": "alice@example.com"},
                        "identity_mappings": [],
                        "message_mappings": [],
                    }
                ),
                encoding="utf-8",
            )
            output = Path(directory) / "rewritten.git"

            result = run_without_check(
                sys.executable,
                str(SCRIPT),
                "apply",
                "--repo",
                str(repo),
                "--plan",
                str(plan),
                "--approval",
                __import__("hashlib").sha256(plan.read_bytes()).hexdigest(),
                "--output",
                str(output),
                cwd=repo,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("git-filter-repo is required", result.stderr)
            self.assertFalse(output.exists())

    def test_apply_rewrites_only_an_isolated_mirror_and_creates_a_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "source"
            repo.mkdir()
            run("git", "init", "-q", cwd=repo)
            run("git", "config", "user.name", "Alice Old", cwd=repo)
            run("git", "config", "user.email", "old@example.com", cwd=repo)
            (repo / "README.md").write_text("first\n", encoding="utf-8")
            run("git", "add", "README.md", cwd=repo)
            run("git", "commit", "-qm", "修复播放器", cwd=repo)
            head = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
            plan = Path(directory) / "plan.json"
            plan.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "audit": {"head": head},
                        "refs": ["HEAD"],
                        "canonical_identity": {"name": "Alice", "email": "alice@example.com"},
                        "identity_mappings": [
                            {"from": {"name": "Alice Old", "email": "old@example.com"}}
                        ],
                        "message_mappings": [{"commit": head, "message": "fix: player"}],
                    }
                ),
                encoding="utf-8",
            )
            fake_bin = Path(directory) / "bin"
            fake_bin.mkdir()
            fake_filter_repo = fake_bin / "git-filter-repo"
            fake_filter_repo.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake_filter_repo.chmod(0o755)
            output = Path(directory) / "rewritten.git"
            environment = os.environ | {"PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}"}

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "apply",
                    "--repo",
                    str(repo),
                    "--plan",
                    str(plan),
                    "--approval",
                    __import__("hashlib").sha256(plan.read_bytes()).hexdigest(),
                    "--output",
                    str(output),
                ],
                cwd=repo,
                text=True,
                capture_output=True,
                check=False,
                env=environment,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip(), head)
            self.assertTrue((output / "before-rewrite.bundle").exists())
            self.assertTrue((output / "repair-result.json").exists())

    def test_apply_rejects_a_dirty_source_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "source"
            repo.mkdir()
            run("git", "init", "-q", cwd=repo)
            run("git", "config", "user.name", "Alice", cwd=repo)
            run("git", "config", "user.email", "alice@example.com", cwd=repo)
            (repo / "README.md").write_text("first\n", encoding="utf-8")
            run("git", "add", "README.md", cwd=repo)
            run("git", "commit", "-qm", "Initial commit", cwd=repo)
            head = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
            (repo / "dirty.txt").write_text("do not rewrite this\n", encoding="utf-8")
            plan = Path(directory) / "plan.json"
            plan.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "audit": {"head": head},
                        "refs": ["HEAD"],
                        "canonical_identity": {"name": "Alice", "email": "alice@example.com"},
                        "identity_mappings": [],
                        "message_mappings": [],
                    }
                ),
                encoding="utf-8",
            )
            result = run_without_check(
                sys.executable,
                str(SCRIPT),
                "apply",
                "--repo",
                str(repo),
                "--plan",
                str(plan),
                "--approval",
                __import__("hashlib").sha256(plan.read_bytes()).hexdigest(),
                "--output",
                str(Path(directory) / "rewritten.git"),
                cwd=repo,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("clean worktree", result.stderr)

    def test_verify_confirms_rewritten_commits_preserve_their_trees(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.mkdir()
            run("git", "init", "-q", cwd=source)
            run("git", "config", "user.name", "Alice", cwd=source)
            run("git", "config", "user.email", "alice@example.com", cwd=source)
            (source / "README.md").write_text("first\n", encoding="utf-8")
            run("git", "add", "README.md", cwd=source)
            run("git", "commit", "-qm", "Initial commit", cwd=source)
            old_commit = run("git", "rev-parse", "HEAD", cwd=source).stdout.strip()
            mirror = Path(directory) / "mirror.git"
            run("git", "clone", "--mirror", str(source), str(mirror), cwd=source.parent)
            mapping_dir = mirror / "filter-repo"
            mapping_dir.mkdir()
            (mapping_dir / "commit-map").write_text(
                f"old new\n{old_commit} {old_commit}\n", encoding="utf-8"
            )
            plan = Path(directory) / "plan.json"
            plan.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "audit": {"head": old_commit},
                        "refs": ["HEAD"],
                        "canonical_identity": {"name": "Alice", "email": "alice@example.com"},
                        "identity_mappings": [],
                        "message_mappings": [],
                    }
                ),
                encoding="utf-8",
            )

            result = run(
                sys.executable,
                str(SCRIPT),
                "verify",
                "--source",
                str(source),
                "--mirror",
                str(mirror),
                "--plan",
                str(plan),
                cwd=source,
            )
            report = json.loads(result.stdout)

            self.assertEqual(report["checked_commit_count"], 1)
            self.assertTrue(report["content_preserved"])


if __name__ == "__main__":
    unittest.main()
