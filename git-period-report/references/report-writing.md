# Report Writing Reference

## Source of Truth

Use the squashed diff as the source of truth: `git diff <base_commit> <end_commit>`. Commits explain the route; the final diff explains what remained.

This avoids reporting work that was later deleted, reverted, renamed away, or replaced by a better implementation within the same period.

## Recommended Structure

1. Title with report type and exact date range.
2. Data basis: base commit, end commit, ref, diff scale, and generation mode.
3. Executive summary in one short paragraph.
4. Major themes, ordered by importance.
5. For each major theme:
   - Problem: what was painful or risky before.
   - Final capability: what the code now does.
   - Why it matters: explain in plain language for non-specialists.
   - Evidence: key files, tests, migrations, or docs.
6. User impact.
7. Engineering quality and verification signals.
8. Risks or follow-up work.

## Theme Selection

Choose themes by impact, not by commit count.

Prefer themes that touch:
- user-visible workflows,
- production or runtime safety,
- data integrity,
- database migrations,
- authentication or credentials,
- financial or external-service behavior,
- large test additions,
- documentation that records operational decisions.

## Writing Rules

- Write for a reader who did not follow the implementation.
- Explain acronyms and internal terms when they first matter.
- Avoid a raw chronological commit list unless asked.
- Keep commit hashes as trace evidence, not as the report's main structure.
- Mark partial periods clearly.
- Separate final shipped capabilities from branch-only or unmerged work.
- Do not infer business outcomes that the diff cannot prove.

## Useful Git Commands

```bash
git diff --shortstat <base_commit> <end_commit>
git diff --stat <base_commit> <end_commit>
git diff --dirstat=files,5,cumulative <base_commit> <end_commit>
git log --reverse --no-merges --date=iso-strict --pretty=format:'%h%x09%cI%x09%an%x09%s' <base_commit>..<end_commit>
git diff <base_commit> <end_commit> -- <path>
git show <end_commit>:<path>
```
