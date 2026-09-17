# PR-Driven Versioning Rules & Mechanics

## 1. Version Format

The version tag is structured as:

```
v<Major>.<Minor>.<Patch>
```

- **Major (大版本号 / 里程碑)**:
  - Read from the `VERSION` file located at the repository root.
  - Defaults to `0` if the file is absent or empty.
  - Maintainers bump this manually (e.g. `0` -> `1`) via a commit/PR when a milestone changes.
- **Minor (次版本号 / 累计合并 PR 数量)**:
  - The sequential count of merged Pull Requests targeting the base branch (e.g. `5` for the 5th merged PR).
  - Queried via GitHub API to ensure accuracy across all merge strategies (merge commits, squash merges, rebase merges).
  - Unaffected by GitHub Issue or Discussion counters.
- **Patch (修订号 / Commit 数量)**:
  - The total number of commits contained in that PR (read directly from GitHub PR metadata `pull_request.commits`).

### Example
- `VERSION` contains `0`.
- The repository has previously merged 4 PRs on `main`.
- PR #17 containing 3 commits merges into `main` (making it the 5th merged PR).
- Resulting tag: `v0.5.3`.
- Release Title: `v0.5.3 - feat: add login`

---

## 2. Tag Collision & Force-Overwrite Handling (同名版本覆盖机制)

### Scenario
When migrating from legacy rules (where Minor was the GitHub PR ID) to the sequential PR-count rule:
1. Under the legacy scheme, PR numbers might have skipped ahead (e.g. `v0.17.3` generated earlier due to issues inflating PR numbers).
2. Under the new scheme, as PRs continue to merge, the cumulative merged PR count will eventually catch up to 17 (e.g. generating `v0.17.2`).

### Actions Taken
1. **Force Tag Update**:
   - The engine detects the pre-existing tag and executes `git tag -f -a <tag> -m ...` followed by `git push origin <tag> --force`.
   - The remote Git tag is updated to point to the new merge commit.
2. **Release Overwrite**:
   - The engine updates the existing GitHub Release via `gh release edit` with the new release title and notes corresponding to the newly merged PR.
   - Release notes include a clear indication that the tag was updated under the sequential PR-count rule.
