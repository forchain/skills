# PRD: PR Tag and Release Automation Skill (`pr-tag-release`)

## Problem Statement

Engineering teams that follow PR-driven workflows often struggle with manual, inconsistent, or lagging version tagging and release creation. When PRs merge into main branches, developers frequently forget to bump version numbers, generate releases, or link releases to their originating PRs.

Furthermore, PRs are frequently merged out of numerical order (e.g. PR #18 merges before PR #17). Standard automated semver bump tools fail to maintain a clean trace of commit increments and PR references when out-of-order merges occur, resulting in missing commit counts or unlinked release notes.

The user wants an automated skill and reusable GitHub Actions workflow that automatically computes version tags (`v<Major>.<PR_ID>.<commits>`), publishes GitHub Releases upon PR merge, handles out-of-order PR merges by backfilling commit counts onto the latest PR release, and updates PR descriptions with trace references.

## Solution

Build a `pr-tag-release` skill package containing:
1. A thin, actionable `SKILL.md` that guides AI agents and developers in setting up, auditing, and operating the automated PR tagging and release pipeline in any repository.
2. A robust, self-contained GitHub Actions workflow template (`.github/workflows/pr-tag-release.yml`) that listens to `pull_request` (`closed`, `merged == true`) on `main` and `master` branches.
3. A deterministic version calculation engine:
   - **Major**: Read from a root repository `VERSION` file (defaults to `0`).
   - **Minor**: The merged Pull Request ID (e.g. `17`).
   - **Patch**: The PR's total commit count directly extracted from GitHub PR metadata (`pull_request.commits`).
   - **Tag Format**: `v<Major>.<PR_ID>.<Patch>` (e.g. `v0.17.3`).
4. An out-of-order merge handler:
   - When a lower PR ID (e.g. #17 with 3 commits) is merged after a higher PR ID (e.g. #18 with 2 commits, originally `v0.18.2`), #17 receives `v0.17.3`.
   - The engine detects that #18 is a higher merged PR, bumps #18's version to `v0.18.(2+3) = v0.18.5`, creates/updates the Git tag and Release for #18, and appends a reference note to PR #18's body.
5. Automated GitHub Release creation with rich notes including PR title, author, description, commit lists, and backfill notes.

## User Stories

1. As a project maintainer, I want to install the `pr-tag-release` skill into my repository, so that all subsequent PR merges are automatically tagged and released.
2. As a project maintainer, I want the Major version to be read from a root `VERSION` file, so that I can bump Major versions via standard Git commits or PRs.
3. As a developer, I want my merged PR to be tagged with `v<Major>.<PR_ID>.<Patch>`, so that the version directly reflects my PR number and its commit count.
4. As a developer, I want the commit count to be extracted directly from PR metadata, so that squash-merges, rebase-merges, and standard merges all accurately reflect the PR's original commit count.
5. As a maintainer, I want a GitHub Release to be created automatically when a PR merges, so that release notes and downloadable assets are immediately available.
6. As a maintainer, I want the Release title to be formatted as `v<Major>.<PR_ID>.<Patch> - <PR Title>`, so that the changelog is instantly readable.
7. As a maintainer, I want the Release body to contain the PR description, author attribution, and commit list, so that release context is preserved without manual writing.
8. As a developer, when PR #18 merges before PR #17, I want PR #17 to receive its tag `v0.17.3`, so that its specific history is tagged.
9. As a developer, when PR #17 merges after PR #18, I want the latest release for PR #18 to have its patch incremented by PR #17's commit count (e.g. `v0.18.5`), so that the tip of the main branch accurately reflects cumulative commit increments.
10. As a maintainer, when an out-of-order merge occurs, I want PR #18's description to be automatically updated with a note linking to PR #17, so that the backfill relationship is auditable.
11. As a developer, I want the GitHub Actions workflow to support both `main` and `master` default branch names.
12. As a maintainer, I want the workflow to require minimal permissions (`contents: write` and `pull-requests: write`), so that principle of least privilege is preserved.
13. As an agent, I want repository and skill validation scripts (`scripts/validate_skills.py`) to pass cleanly on the new skill directory.
14. As an agent, I want clear test harnesses and mock PR events, so that I can verify version bumping and backfill logic without live GitHub deployments.

## Implementation Decisions

- **Skill Layout**: Create a dedicated skill directory `pr-tag-release/` adhering to the repository conventions (`SKILL.md`, `agents/openai.yaml`, `templates/`, `scripts/`, `references/`).
- **Major Version Configuration**: Use a plain-text `VERSION` file in the root of the repository, containing a single integer (e.g. `0`).
- **PR Metadata Extraction**: Read `github.event.pull_request.number`, `github.event.pull_request.commits`, `github.event.pull_request.title`, `github.event.pull_request.body`, and `github.event.pull_request.user.login` from GitHub Actions event payload.
- **Out-of-Order Detection Engine**: Implement a deterministic helper script (using GitHub API / `gh` CLI) that queries previous releases and merged PRs to identify if any existing merged PR has an ID strictly greater than the current PR ID. If so, calculate `new_patch = existing_patch + current_commits`, apply new tag, update release metadata, and append a backfill citation to the higher PR's body.
- **Workflow Security & Permissions**: Explicitly declare `permissions: contents: write, pull-requests: write` inside the workflow YAML.
- **No Heavy Dependencies**: The workflow script will use standard Node.js / Python / Bash + `gh` CLI bundled in GitHub Actions runners to avoid slow `npm install` or external Docker containers.

## Testing Decisions

- **Testing Seam**: The primary test seam is the standalone version and backfill calculation script executed against mock GitHub event JSON payloads.
  - Good tests verify that given input event `{number: 17, commits: 3, major: 0}` and existing release state `[{tag: "v0.18.2", pr_id: 18, patch: 2}]`, the script correctly outputs planned operations: Tag `v0.17.3`, Update Tag `v0.18.5`, and Edit PR #18 body.
- **Skill Validation Seam**: Repository skill validator `python3 scripts/validate_skills.py` to ensure valid frontmatter and agent metadata.
- **Prior Art**: Follow the modular script and reference patterns established in `git-period-report` and `career-agent`.

## Out of Scope

- Support for non-GitHub git hosting providers (GitLab, Bitbucket, Gitea) in V1.
- Automatic SemVer MAJOR incrementing heuristics (MAJOR remains explicitly configured in `VERSION`).
- Generating binary release asset builds or package registry publishing (handled by downstream CI pipelines).
- Multi-branch release streams (e.g., release-1.x maintenance branches) in V1.

## Further Notes

V1 delivers a complete, installable skill and verified GitHub Actions template ready for deployment to any repository with zero external SaaS dependencies.
