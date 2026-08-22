---
name: git-period-report
description: "Generate git-based period reports from repository history: weekly reports by default, monthly reports, custom date-range summaries, commit-history reports, and squashed-diff/final-state reports. Use when the user asks for a weekly report, monthly report, work report, changelog-like status report, or asks to summarize commits or changes over a time window."
summary: "Generate weekly, monthly, or custom-period reports from Git history and final-state diffs."
---

# Git Period Report

## Overview

Generate a weekly, monthly, or custom period report from a Git repository. Treat the squashed diff between the period's start baseline and end snapshot as the source of truth; use commits as trace evidence.

Default period: the last completed ISO week, Monday through Sunday.

## Workflow

1. **Resolve the period**
   - Use `--period weekly` when the user does not specify a period.
   - Use `--period monthly` for a completed previous-month report.
   - Use `--since YYYY-MM-DD --until YYYY-MM-DD` for a custom range.
   - Completion criterion: the report has exact inclusive start and end dates.

2. **Extract git context**
   - Run:
     ```bash
     python3 <skill-dir>/scripts/git_period_context.py --repo . --period weekly --output /tmp/git-period-report.json
     ```
   - For monthly:
     ```bash
     python3 <skill-dir>/scripts/git_period_context.py --repo . --period monthly --output /tmp/git-period-report.json
     ```
   - For custom:
     ```bash
     python3 <skill-dir>/scripts/git_period_context.py --repo . --since 2026-06-01 --until 2026-06-30 --output /tmp/git-period-report.json
     ```
   - Completion criterion: the JSON contains `base_commit`, `end_commit`, `shortstat`, changed files, and period commits.

3. **Read the final-state diff**
   - Use the JSON as a map, then inspect important files with:
     ```bash
     git -C <repo> diff <base_commit> <end_commit> -- <path>
     git -C <repo> show <end_commit>:<path>
     ```
   - Give priority to files with high churn, user-facing paths, runtime-critical paths, migrations, tests, docs, and configuration.
   - Completion criterion: every major theme in the report is backed by final diff evidence, not only a commit title.

4. **Write the report**
   - Read `references/report-writing.md` before drafting.
   - Organize by final capabilities and user impact. Do not list every commit unless the user specifically asks for a commit ledger.
   - Include the exact range, baseline commit, end commit, and diff scale.
   - Completion criterion: the report explains what changed, why it mattered, and what residual risks or follow-ups remain.

5. **Verify saved output**
   - If writing into a repository, run `git diff --check`.
   - If the repository has a docs build or markdown lint command, run the relevant lightweight check.
   - Completion criterion: report file is saved where requested, and verification results are stated.

## Notes

- For weekly reports, prefer the last completed week over the current partial week.
- For monthly reports, prefer the last completed calendar month over the current partial month.
- If the user explicitly asks for current week/month-to-date, honor that override and label the report as partial.
- If no commit exists before the start boundary or before the end boundary, stop and report the missing boundary.
