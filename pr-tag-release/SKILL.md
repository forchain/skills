---
name: pr-tag-release
description: "Automate PR merge tagging, releases, and versioning based on sequential merged PR counts. Tags merged PRs with v<Major>.<Merged_PR_Count>.<commits>, creates GitHub Releases, and safely force-overwrites legacy colliding tags. Use when setting up, auditing, upgrading, or configuring automated PR release tagging in a repository."
summary: "Automate PR merge tagging (`v<Major>.<Merged_PR_Count>.<commits>`), GitHub Releases, and legacy tag overwrite."
---

# PR Tag & Release Automation

## Overview

`pr-tag-release` automates version tagging and GitHub Release publishing for PR-driven repositories. Every time a Pull Request merges into the primary branch (`main` or `master`), this automation:
1. Calculates the semantic version: `v<Major>.<Merged_PR_Count>.<Patch>`
   - **Major**: Read from root `VERSION` file (defaults to `0`).
   - **Minor**: Sequential count of merged PRs on the target base branch (e.g. `5` for the 5th merged PR). Unaffected by GitHub Issue numbers.
   - **Patch**: Number of commits in the PR (e.g. `3`).
2. Creates and pushes the Git tag with force support (e.g. `v0.5.3`).
3. Publishes or updates the GitHub Release with formatted changelog notes.
4. **Handles Tag Collisions**: If a tag name collides with a legacy tag (e.g. created when Minor was PR ID), the workflow automatically force-overwrites the Git tag and updates the GitHub Release with the latest PR metadata.

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

## Repository Upgrade Workflow (已有代码库升级工作流)

When a user asks to upgrade, update, or sync `pr-tag-release` in an existing repository that already has the workflow installed:

### Step 1: Overwrite Workflow and Scripts
Copy the latest workflow template and helper scripts into the repository (preserving existing `VERSION`):
```bash
cp <skill-dir>/templates/pr-tag-release.yml .github/workflows/pr-tag-release.yml
cp <skill-dir>/scripts/calculate_release.py .github/scripts/calculate_release.py
cp <skill-dir>/scripts/publish_release.py .github/scripts/publish_release.py
```

### Step 2: Commit and Push Upgrade
```bash
git add .github/workflows/pr-tag-release.yml .github/scripts/
git commit -m "ci: upgrade pr-tag-release to sequential merged PR count scheme"
git push
```

---

## Tag Collision & Overwrite Example

| Event Order | Merged PR | Commits | Cumulative Merged PRs | Tag Generated | Overwrite Action |
|---|---|---|---|---|---|
| Legacy | **PR #17** | 3 | (old rule used PR ID) | `v0.17.3` | Published under legacy scheme |
| Current | **PR #35** | 2 | 17th merged PR | `v0.17.2` | Forces tag update on Git and overwrites GitHub Release notes |

---

## References

- [Permissions Guide](references/permissions.md) — GitHub Token and Actions permissions setup.
- [Versioning Rules](references/versioning-rules.md) — Full specification of the PR-driven versioning scheme.
- [Troubleshooting](references/troubleshooting.md) — Common error resolution and FAQs.
