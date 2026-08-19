# Issue 4: Build Setup Automation, Verification Suite, and Reference Docs

## What to build

Deliver the complete package integration:
- `pr-tag-release/templates/VERSION` (baseline file with content `0`).
- `pr-tag-release/templates/pr-tag-release.yml` (template for user projects).
- `pr-tag-release/references/` detailed documentation covering permissions, troubleshooting, and edge cases.
- Comprehensive end-to-end simulation test suite verifying full workflow behavior.

## Acceptance criteria

- [ ] `pr-tag-release/templates/` contains required template files.
- [ ] Documentation covers how to configure GitHub Actions permissions (`Read and write permissions` under Actions settings).
- [ ] End-to-end simulation tests pass.
- [ ] Skill validator `python3 scripts/validate_skills.py` passes cleanly across all repository skills.

## Blocked by

- Issue 3: Build GitHub Actions Workflow Template & Release Publisher
