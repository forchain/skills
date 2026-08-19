# Issue 1: Build the `pr-tag-release` Skill Router and Metadata Layout

## What to build

Create the `pr-tag-release` skill foundation including `SKILL.md` and `agents/openai.yaml`. The skill guides users and agents to install, audit, and configure automated PR tagging and release mechanisms in any GitHub repository.

## Acceptance criteria

- [ ] `pr-tag-release/SKILL.md` has valid frontmatter (name, description matching directory).
- [ ] `pr-tag-release/agents/openai.yaml` is present and references `$pr-tag-release`.
- [ ] `SKILL.md` clearly explains the versioning model (`v<Major>.<PR_ID>.<commits>`), normal merge vs out-of-order merge behavior, and installation steps.
- [ ] `python3 scripts/validate_skills.py` passes without errors.

## Blocked by

None - can start immediately.
