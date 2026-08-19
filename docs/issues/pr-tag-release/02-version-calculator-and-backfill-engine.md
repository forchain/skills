# Issue 2: Build Version Tagging & Out-of-Order PR Calculation Engine

## What to build

Implement the version calculation and out-of-order PR backfill engine (`scripts/calculate_release.py`).
The engine reads:
1. `VERSION` file (Major version, defaults to `0`)
2. PR event metadata (PR ID, Commit count, Title, Body, Author, Merge commit SHA)
3. Historical releases / tags from GitHub API or git

It outputs:
- Target tag name (e.g. `v0.17.3`) and release title/body for current PR.
- Detection if a higher PR ID (e.g. #18) was already merged previously.
- If out-of-order merge detected:
  - Higher PR's new bumped tag (e.g. `v0.18.5`)
  - Updated release metadata for #18
  - Formatted text snippet to append to PR #18's description referencing PR #17.

## Acceptance criteria

- [ ] Calculates version tag correctly (`v<Major>.<PR_ID>.<commits>`).
- [ ] Handles single commit and multi-commit PRs.
- [ ] Accurately detects out-of-order merges when current PR ID < highest released PR ID.
- [ ] Accurately computes new patch count for higher PR (`existing_patch + current_pr_commits`).
- [ ] Generates clean release markdown notes and PR backfill text.
- [ ] Complete unit test suite (`tests/test_calculate_release.py`) passes all test cases.

## Blocked by

- Issue 1: Build the `pr-tag-release` Skill Router and Metadata Layout
