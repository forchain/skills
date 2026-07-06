#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


def run_git(repo: str, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", repo, *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def parse_day(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid date {value!r}; expected YYYY-MM-DD") from exc


def previous_iso_week(today: date) -> tuple[date, date]:
    start = today - timedelta(days=today.weekday() + 7)
    return start, start + timedelta(days=6)


def previous_month(today: date) -> tuple[date, date]:
    first_this_month = today.replace(day=1)
    end = first_this_month - timedelta(days=1)
    return end.replace(day=1), end


def resolve_period(args: argparse.Namespace) -> tuple[date, date, str]:
    today = parse_day(args.today) if args.today else date.today()
    if args.since or args.until:
        if not args.since or not args.until:
            raise ValueError("--since and --until must be provided together")
        since = parse_day(args.since)
        until = parse_day(args.until)
        label = "custom"
    elif args.period == "monthly":
        since, until = previous_month(today)
        label = "monthly"
    else:
        since, until = previous_iso_week(today)
        label = "weekly"
    if since > until:
        raise ValueError("period start must be on or before period end")
    return since, until, label


def commit_before(repo: str, ref: str, boundary: str) -> str:
    return run_git(repo, ["rev-list", "-1", f"--before={boundary}", ref]).strip()


def commit_summary(repo: str, commit: str) -> dict[str, str]:
    raw = run_git(repo, ["show", "-s", "--format=%H%x01%h%x01%cI%x01%s", commit]).strip()
    full_hash, short_hash, committed_at, subject = raw.split("\x01", 3)
    return {
        "hash": full_hash,
        "short_hash": short_hash,
        "committed_at": committed_at,
        "subject": subject,
    }


def parse_commits(repo: str, base: str, end: str, include_merges: bool, max_commits: int) -> list[dict[str, str]]:
    cmd = ["log", "--reverse", "--date=iso-strict"]
    if not include_merges:
        cmd.append("--no-merges")
    cmd.extend([f"--max-count={max_commits}", "--pretty=format:%H%x01%h%x01%cI%x01%an%x01%s", f"{base}..{end}"])
    output = run_git(repo, cmd)
    commits: list[dict[str, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        full_hash, short_hash, committed_at, author, subject = line.split("\x01", 4)
        commits.append(
            {
                "hash": full_hash,
                "short_hash": short_hash,
                "committed_at": committed_at,
                "author": author,
                "subject": subject,
            }
        )
    return commits


def parse_numstat(output: str) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added_raw, deleted_raw, path = parts[0], parts[1], parts[-1]
        added = None if added_raw == "-" else int(added_raw)
        deleted = None if deleted_raw == "-" else int(deleted_raw)
        churn = (added or 0) + (deleted or 0)
        files.append({"path": path, "insertions": added, "deletions": deleted, "churn": churn})
    files.sort(key=lambda item: item["churn"], reverse=True)
    return files


def parse_name_status(output: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        path = parts[-1]
        previous_path = parts[1] if len(parts) > 2 else ""
        rows.append({"status": status, "path": path, "previous_path": previous_path})
    return rows


def build_context(args: argparse.Namespace) -> dict[str, Any]:
    repo = os.path.abspath(args.repo)
    if not Path(repo).exists():
        raise FileNotFoundError(repo)
    run_git(repo, ["rev-parse", "--git-dir"])

    since, until, label = resolve_period(args)
    base = commit_before(repo, args.ref, f"{since.isoformat()}T00:00:00")
    end = commit_before(repo, args.ref, f"{until.isoformat()}T23:59:59")
    if not base:
        raise RuntimeError(f"no base commit found before {since.isoformat()} on {args.ref}")
    if not end:
        raise RuntimeError(f"no end commit found before {until.isoformat()} on {args.ref}")

    shortstat = run_git(repo, ["diff", "--shortstat", base, end]).strip()
    dirstat = run_git(repo, ["diff", "--dirstat=files,5,cumulative", base, end]).splitlines()
    numstat = parse_numstat(run_git(repo, ["diff", "--numstat", base, end]))
    name_status = parse_name_status(run_git(repo, ["diff", "--name-status", base, end]))
    commits = parse_commits(repo, base, end, args.include_merges, args.max_commits)

    return {
        "repo": repo,
        "ref": args.ref,
        "period": {
            "type": label,
            "since": since.isoformat(),
            "until": until.isoformat(),
            "inclusive": True,
        },
        "base_commit": commit_summary(repo, base),
        "end_commit": commit_summary(repo, end),
        "squashed_diff": {
            "shortstat": shortstat,
            "dirstat": dirstat,
            "changed_file_count": len(name_status),
            "name_status": name_status[: args.max_files],
            "top_files": numstat[: args.max_files],
        },
        "commits": commits,
        "commit_count": len(commits),
        "truncated": {
            "commits": len(commits) >= args.max_commits,
            "files": len(name_status) > args.max_files,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build git period report context as JSON.")
    parser.add_argument("--repo", default=".", help="Git repository path.")
    parser.add_argument("--ref", default="HEAD", help="Ref to report on, such as HEAD, main, or origin/main.")
    parser.add_argument("--period", choices=["weekly", "monthly"], default="weekly", help="Default period when dates are omitted.")
    parser.add_argument("--since", help="Inclusive start date, YYYY-MM-DD.")
    parser.add_argument("--until", help="Inclusive end date, YYYY-MM-DD.")
    parser.add_argument("--today", help="Override today's date for deterministic testing, YYYY-MM-DD.")
    parser.add_argument("--include-merges", action="store_true", help="Include merge commits in the commit list.")
    parser.add_argument("--max-commits", type=int, default=200, help="Maximum commits to include.")
    parser.add_argument("--max-files", type=int, default=120, help="Maximum changed files to include in file lists.")
    parser.add_argument("--output", help="Write JSON to this path instead of stdout.")
    args = parser.parse_args()

    try:
        context = build_context(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    payload = json.dumps(context, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
