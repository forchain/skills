# GitHub Actions Permissions Guide

To allow the automated workflow to tag commits, create GitHub Releases, and update Pull Request descriptions, ensure the following settings are configured:

## 1. Repository Workflow Permissions

1. Navigate to your GitHub repository.
2. Go to **Settings** > **Actions** > **General**.
3. Under **Workflow permissions**, select:
   - 🔘 **Read and write permissions**
   - ☑️ **Allow GitHub Actions to create and approve pull requests** (optional, recommended)
4. Click **Save**.

## 2. In-Workflow Declarations

The workflow automatically requests the necessary least-privilege permissions:

```yaml
permissions:
  contents: write
  pull-requests: write
```

- `contents: write`: Required to create Git tags (`git push origin <tag>`) and publish GitHub Releases (`gh release create`).
- `pull-requests: write`: Required to append out-of-order backfill citations to the latest PR's description (`gh pr edit <id> --body ...`).
