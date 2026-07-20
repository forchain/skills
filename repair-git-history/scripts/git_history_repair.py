#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def optional_git(repo: Path, *args: str) -> str:
    try:
        return git(repo, *args)
    except RuntimeError:
        return ""


def command(*args: str, cwd: Path) -> None:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"{' '.join(args)} failed")


def github_login_hint(remote: str) -> str | None:
    parsed = urlsplit(remote)
    if parsed.hostname != "github.com" or not parsed.username:
        return None
    return unquote(parsed.username)


def identity_rows(repo: Path, format_string: str) -> list[dict[str, Any]]:
    counts = Counter(
        tuple(row.split("\x1f", 1))
        for row in git(repo, "log", "--all", f"--format={format_string}").splitlines()
        if row
    )
    return [
        {"count": count, "email": email, "name": name}
        for (name, email), count in sorted(counts.items())
    ]


def audit(repo: Path) -> dict[str, Any]:
    root = Path(git(repo, "rev-parse", "--show-toplevel").strip())
    commits = git(root, "rev-list", "--all").splitlines()
    subjects = [
        tuple(row.split("\x1f", 1))
        for row in git(root, "log", "--all", "--format=%H%x1f%s").splitlines()
        if row
    ]
    refs = git(root, "for-each-ref", "--format=%(refname)", "refs/heads", "refs/tags").splitlines()
    tags = [ref for ref in refs if ref.startswith("refs/tags/")]
    branches = [ref for ref in refs if ref.startswith("refs/heads/")]
    remote = optional_git(root, "remote", "get-url", "origin").strip()
    status = git(root, "status", "--porcelain")

    return {
        "schema_version": 1,
        "repository": {
            "path": str(root),
            "head": git(root, "rev-parse", "HEAD").strip(),
            "commit_count": len(commits),
            "origin": remote or None,
        },
        "github": {"login_hint": github_login_hint(remote)},
        "identities": {
            "authors": identity_rows(root, "%an%x1f%ae"),
            "committers": identity_rows(root, "%cn%x1f%ce"),
        },
        "messages": {
            "non_ascii": [
                {"commit": commit, "subject": subject}
                for commit, subject in subjects
                if not subject.isascii()
            ],
        },
        "refs": {"branches": branches, "tags": tags},
        "safety": {"clean_worktree": not status.strip()},
    }


def plan_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_plan(plan: dict[str, Any], repo: Path) -> None:
    if plan.get("schema_version") != 1:
        raise RuntimeError("plan schema_version must be 1")
    if plan.get("audit", {}).get("head") != git(repo, "rev-parse", "HEAD").strip():
        raise RuntimeError("plan audit.head does not match the current repository HEAD")
    identity = plan.get("canonical_identity", {})
    if not isinstance(identity.get("name"), str) or not isinstance(identity.get("email"), str):
        raise RuntimeError("plan canonical_identity must include name and email")
    if not isinstance(plan.get("identity_mappings"), list):
        raise RuntimeError("plan identity_mappings must be a list")
    if not isinstance(plan.get("message_mappings"), list):
        raise RuntimeError("plan message_mappings must be a list")
    if not isinstance(plan.get("refs"), list) or not plan["refs"] or not all(isinstance(ref, str) for ref in plan["refs"]):
        raise RuntimeError("plan refs must be a non-empty list")
    for ref in plan["refs"]:
        git(repo, "rev-parse", "--verify", ref)
    for mapping in plan["identity_mappings"]:
        source = mapping.get("from", {})
        if not isinstance(source.get("name"), str) or not isinstance(source.get("email"), str):
            raise RuntimeError("each identity mapping must include from.name and from.email")
    for mapping in plan["message_mappings"]:
        if not isinstance(mapping.get("commit"), str) or not isinstance(mapping.get("message"), str):
            raise RuntimeError("each message mapping must include commit and message")


def commit_callback(plan: dict[str, Any]) -> str:
    encoded_plan = base64.b64encode(json.dumps(plan, ensure_ascii=False).encode("utf-8")).decode("ascii")
    return f'''import base64, json
plan = json.loads(base64.b64decode(b"{encoded_plan}").decode("utf-8"))
target = plan["canonical_identity"]
for mapping in plan["identity_mappings"]:
    source = mapping["from"]
    name = source["name"].encode("utf-8")
    email = source["email"].encode("utf-8")
    if commit.author_name == name and commit.author_email == email:
        commit.author_name = target["name"].encode("utf-8")
        commit.author_email = target["email"].encode("utf-8")
    if commit.committer_name == name and commit.committer_email == email:
        commit.committer_name = target["name"].encode("utf-8")
        commit.committer_email = target["email"].encode("utf-8")
messages = {{item["commit"]: item["message"] for item in plan["message_mappings"]}}
original_id = commit.original_id.decode("ascii")
if original_id in messages:
    message = messages[original_id]
    commit.message = (message if message.endswith("\\n") else message + "\\n").encode("utf-8")
'''


def ref_oids(repo: Path, refs: list[str]) -> dict[str, str]:
    return {ref: git(repo, "rev-parse", ref).strip() for ref in refs}


def apply(repo: Path, plan_path: Path, approval: str, output: Path) -> None:
    if approval != plan_digest(plan_path):
        raise RuntimeError("--approval must equal the SHA-256 digest of --plan")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    validate_plan(plan, repo)
    if git(repo, "status", "--porcelain").strip():
        raise RuntimeError("apply requires a clean worktree")
    if output.exists():
        raise RuntimeError("--output must not already exist")
    if shutil.which("git-filter-repo") is None:
        raise RuntimeError("git-filter-repo is required; install it before running apply")
    output.parent.mkdir(parents=True, exist_ok=True)
    command("git", "clone", "--mirror", "--no-local", str(repo), str(output), cwd=repo.parent)
    git(output, "bundle", "create", str(output / "before-rewrite.bundle"), "--all")
    command(
        "git-filter-repo",
        "--force",
        "--refs",
        *plan["refs"],
        "--commit-callback",
        commit_callback(plan),
        cwd=output,
    )
    result = {
        "plan_digest": plan_digest(plan_path),
        "source_repository": str(repo),
        "mirror_repository": str(output),
        "backup_bundle": str(output / "before-rewrite.bundle"),
        "rewritten_head": git(output, "rev-parse", "HEAD").strip(),
        "refs": {"source": ref_oids(repo, plan["refs"]), "rewritten": ref_oids(output, plan["refs"])},
    }
    (output / "repair-result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


def read_commit_map(mirror: Path) -> list[tuple[str, str]]:
    map_path = mirror / "filter-repo" / "commit-map"
    if not map_path.exists():
        raise RuntimeError("git-filter-repo commit map is missing from the mirror")
    mappings: list[tuple[str, str]] = []
    for line in map_path.read_text(encoding="utf-8").splitlines():
        old, new = line.split()
        if old == "old" or new == "0" * len(new):
            continue
        mappings.append((old, new))
    if not mappings:
        raise RuntimeError("git-filter-repo commit map contains no rewritten commits")
    return mappings


def commit_metadata(repo: Path, commit: str) -> tuple[str, str, str, str]:
    return tuple(git(repo, "show", "-s", "--format=%an%x1f%ae%x1f%cn%x1f%ce", commit).strip().split("\x1f"))


def commit_message(repo: Path, commit: str) -> str:
    raw = git(repo, "cat-file", "commit", commit)
    try:
        return raw.split("\n\n", 1)[1]
    except IndexError as exc:
        raise RuntimeError(f"commit {commit} has no message separator") from exc


def verify(source: Path, mirror: Path, plan_path: Path) -> dict[str, Any]:
    git(source, "rev-parse", "--git-dir")
    if git(mirror, "rev-parse", "--is-bare-repository").strip() != "true":
        raise RuntimeError("--mirror must be a bare mirror repository")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    validate_plan(plan, source)
    git(mirror, "fsck", "--strict")
    commit_map = dict(read_commit_map(mirror))
    expected_commits = set(git(source, "rev-list", *plan["refs"]).splitlines())
    missing = expected_commits - set(commit_map)
    if missing:
        raise RuntimeError(f"git-filter-repo commit map is incomplete; missing {len(missing)} source commits")
    for old, new in commit_map.items():
        old_tree = git(source, "rev-parse", f"{old}^{{tree}}").strip()
        new_tree = git(mirror, "rev-parse", f"{new}^{{tree}}").strip()
        if old_tree != new_tree:
            raise RuntimeError(f"content changed while rewriting commit {old}")
        old_parents = git(source, "show", "-s", "--format=%P", old).strip().split()
        new_parents = git(mirror, "show", "-s", "--format=%P", new).strip().split()
        expected_parents = [commit_map[parent] for parent in old_parents if parent in commit_map]
        if new_parents != expected_parents:
            raise RuntimeError(f"parent topology changed while rewriting commit {old}")
        old_dates = git(source, "show", "-s", "--format=%aI%x1f%cI", old).strip()
        new_dates = git(mirror, "show", "-s", "--format=%aI%x1f%cI", new).strip()
        if old_dates != new_dates:
            raise RuntimeError(f"dates changed while rewriting commit {old}")
    target = plan["canonical_identity"]
    for mapping in plan["identity_mappings"]:
        source_identity = mapping["from"]
        for old, new in commit_map.items():
            old_author_name, old_author_email, old_committer_name, old_committer_email = commit_metadata(source, old)
            new_author_name, new_author_email, new_committer_name, new_committer_email = commit_metadata(mirror, new)
            if (old_author_name, old_author_email) == (source_identity["name"], source_identity["email"]):
                if (new_author_name, new_author_email) != (target["name"], target["email"]):
                    raise RuntimeError(f"author identity was not repaired for {old}")
            if (old_committer_name, old_committer_email) == (source_identity["name"], source_identity["email"]):
                if (new_committer_name, new_committer_email) != (target["name"], target["email"]):
                    raise RuntimeError(f"committer identity was not repaired for {old}")
    for mapping in plan["message_mappings"]:
        old = mapping["commit"]
        if old not in commit_map:
            raise RuntimeError(f"message mapping commit is absent from the rewrite: {old}")
        actual = commit_message(mirror, commit_map[old])
        expected = mapping["message"] if mapping["message"].endswith("\n") else mapping["message"] + "\n"
        if actual != expected:
            raise RuntimeError(f"message was not repaired for {old}")
    return {
        "checked_commit_count": len(commit_map),
        "content_preserved": True,
        "mirror_head": git(mirror, "rev-parse", "HEAD").strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit and safely repair Git history.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    audit_parser = subcommands.add_parser("audit", help="Inspect a repository without changing it.")
    audit_parser.add_argument("--repo", default=".", help="Repository to inspect.")
    apply_parser = subcommands.add_parser("apply", help="Rewrite an approved plan in an isolated mirror.")
    apply_parser.add_argument("--repo", default=".", help="Repository to repair.")
    apply_parser.add_argument("--plan", required=True, help="Approved repair plan JSON.")
    apply_parser.add_argument("--approval", required=True, help="SHA-256 digest of --plan.")
    apply_parser.add_argument("--output", required=True, help="New directory for the isolated mirror.")
    verify_parser = subcommands.add_parser("verify", help="Verify a rewritten mirror against its source.")
    verify_parser.add_argument("--source", required=True, help="Original repository.")
    verify_parser.add_argument("--mirror", required=True, help="Rewritten bare mirror repository.")
    verify_parser.add_argument("--plan", required=True, help="Approved repair plan JSON.")

    args = parser.parse_args()
    try:
        if args.command == "audit":
            print(json.dumps(audit(Path(args.repo).resolve()), ensure_ascii=False, indent=2))
        elif args.command == "apply":
            apply(
                Path(args.repo).resolve(),
                Path(args.plan).resolve(),
                args.approval,
                Path(args.output).resolve(),
            )
        elif args.command == "verify":
            print(
                json.dumps(
                    verify(Path(args.source).resolve(), Path(args.mirror).resolve(), Path(args.plan).resolve()),
                    indent=2,
                )
            )
    except (OSError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
