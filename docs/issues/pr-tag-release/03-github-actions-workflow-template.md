# Issue 3: Build GitHub Actions Workflow Template & Release Publisher

## What to build

Create the production-ready GitHub Actions workflow template (`templates/pr-tag-release.yml`) and publisher runner (`scripts/publish_release.sh` or integrated workflow step).
The workflow:
- Triggers on `pull_request` closed with `merged == true` targeting `main` or `master`.
- Sets required least-privilege permissions (`contents: write`, `pull-requests: write`).
- Invokes the calculation engine.
- Creates Git tag and pushes to remote.
- Creates GitHub Release via GitHub CLI (`gh release create`).
- If out-of-order merge, tags the latest PR's commit with new version, updates the existing release (`gh release edit`), and updates higher PR's description (`gh pr edit`).

## Acceptance criteria

- [ ] `.github/workflows/pr-tag-release.yml` is valid YAML.
- [ ] Workflow handles branch triggers (`main` and `master`).
- [ ] Uses `gh` CLI commands to safely tag, release, and edit PR bodies.
- [ ] Gracefully skips non-merged PR closures.
- [ ] Contains detailed logging for transparent troubleshooting.

## Blocked by

- Issue 2: Build Version Tagging & Out-of-Order PR Calculation Engine
