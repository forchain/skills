# Troubleshooting & FAQs

## 1. Release Workflow Skipped or Failed

### Symptom: PR merged but no tag or release was created
* **Check 1: Target Branch**
  - Verify if the PR was merged into `main` or `master`. If your default branch is different (e.g. `develop`), update `branches:` in `.github/workflows/pr-tag-release.yml`.
* **Check 2: PR Merged Status**
  - The workflow checks `github.event.pull_request.merged == true`. Closing a PR without merging will not trigger a release.
* **Check 3: GitHub Actions Permissions**
  - If the error log shows `HTTP 403: Resource not accessible by integration`, go to **Settings** > **Actions** > **General** > **Workflow permissions** and enable **Read and write permissions**.

## 2. Tag Collision or Force Push

### Symptom: `fatal: tag 'vX.Y.Z' already exists`
* The engine detects existing tags. If a release was manually created with the same name, either delete the conflicting tag or bump the `VERSION` file.

## 3. How to bump Major version
* Simply edit the `VERSION` file in the root of the repository, change the number (e.g. from `0` to `1`), and merge it into `main`. All subsequent PR merges will use the new Major version prefix.
