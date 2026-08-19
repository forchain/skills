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
- **Minor (次版本号 / PR 编号)**:
  - The integer ID of the merged Pull Request (e.g. `17`).
- **Patch (修订号 / Commit 数量)**:
  - The total number of commits contained in that PR (read directly from GitHub PR metadata `pull_request.commits`).

### Example
- `VERSION` contains `0`.
- PR #17 containing 3 commits merges into `main`.
- Resulting tag: `v0.17.3`.
- Release Title: `v0.17.3 - feat: add login`

---

## 2. Out-of-Order PR Merge Handling (乱序合并处理)

### Scenario
1. PR #18 (containing 2 commits) merges first -> Tagged as `v0.18.2` and Release published.
2. PR #17 (containing 3 commits) merges later.

### Actions Taken
1. **Tag & Release PR #17**:
   - PR #17 receives tag `v0.17.3` and its own GitHub Release.
2. **Backfill Latest PR #18**:
   - The engine detects that PR #18 was merged earlier with a higher PR ID.
   - PR #18's patch version is incremented by PR #17's commit count: `2 + 3 = 5`.
   - A new tag `v0.18.5` is created on PR #18's commit.
   - PR #18's GitHub Release is updated to `v0.18.5`.
3. **Trace Citation in PR Description**:
   - PR #18's description on GitHub is updated to append:
     > `> 📌 **关联合并追溯**: 后续已合并包含 3 个 commit 的 PR #17，最新小版本升级为 v0.18.5。`
