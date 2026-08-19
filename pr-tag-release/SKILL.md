---
name: pr-tag-release
description: "Automate PR merge tagging, releases, and backfills. Tags merged PRs with v<Major>.<PR_ID>.<commits>, creates GitHub Releases, and handles out-of-order PR merges by updating the latest release and PR description. Use when setting up, auditing, or configuring automated PR release tagging in a repository."
---

# PR Tag & Release Automation

## Overview

`pr-tag-release` automates version tagging and GitHub Release publishing for PR-driven repositories. Every time a Pull Request merges into the primary branch (`main` or `master`), this automation:
1. Calculates the semantic version: `v<Major>.<PR_ID>.<Patch>`
   - **Major**: Read from root `VERSION` file (defaults to `0`).
   - **Minor**: Merged PR ID (e.g. `17`).
   - **Patch**: Number of commits in the PR (e.g. `3`).
2. Creates and pushes the Git tag (e.g. `v0.17.3`).
3. Publishes a GitHub Release with formatted changelog notes.
4. **Handles Out-of-Order PR merges**: If a lower PR ID merges after a higher PR ID was already merged (e.g., #18 was merged before #17), it tags #17, increments #18's patch version by #17's commit count (e.g., `v0.18.5`), updates #18's release, and appends a backfill citation to PR #18's description.

---

## Repository Setup & Integration Workflow

When a user asks to enable or setup automated PR release tagging in their repository:

### Step 1: Initialize Version Baseline
Create a `VERSION` file at the repository root if it does not exist:
```bash
echo "0" > VERSION
```

### Step 2: Install Workflow and Scripts
Copy the workflow template and helper scripts into the repository:
```bash
mkdir -p .github/workflows .github/scripts
cp <skill-dir>/templates/pr-tag-release.yml .github/workflows/pr-tag-release.yml
cp <skill-dir>/scripts/calculate_release.py .github/scripts/calculate_release.py
cp <skill-dir>/scripts/publish_release.py .github/scripts/publish_release.py
```

### Step 3: Verify GitHub Actions Permissions
Ensure that repository Actions permissions are set to **Read and write permissions** (under **Settings** > **Actions** > **General** > **Workflow permissions**).

### Step 4: Commit and Push
```bash
git add VERSION .github/workflows/pr-tag-release.yml .github/scripts/
git commit -m "ci: setup automated PR tagging and release workflow"
git push
```

---

## Out-of-Order PR Merging Example

| Event Order | PR Merged | Commits | Tag Generated | Special Action |
|---|---|---|---|---|
| 1st | **PR #18** | 2 | `v0.18.2` | Initial release for PR #18 |
| 2nd | **PR #17** | 3 | `v0.17.3` | Released. Bumps PR #18 to `v0.18.5` (`2 + 3`) and updates PR #18 description |

---

## References

- [Permissions Guide](references/permissions.md) — GitHub Token and Actions permissions setup.
- [Versioning Rules](references/versioning-rules.md) — Full specification of the PR-driven versioning scheme.
- [Troubleshooting](references/troubleshooting.md) — Common error resolution and FAQs.
