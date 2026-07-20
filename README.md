# Personal Agent Skills

This repository stores personal skills for Codex and other agent runtimes.

## Skills

| Skill | Purpose |
| --- | --- |
| `git-period-report` | Generate weekly, monthly, or custom-period reports from Git history and final-state diffs. |
| `repair-git-history` | Audit and safely repair Git identities, messages, tags, and release history. |

## Install

Install a skill with the Skills CLI:

```bash
npx skills add forchain/skills@git-period-report -g -y
```

## Repository Layout

Each skill lives in its own top-level directory:

```text
skill-name/
  SKILL.md
  agents/openai.yaml
  scripts/
  references/
  assets/
```

Only include files that support the skill directly. Put repository-level documentation and automation at the root.

## Validate

Run the repository validator before pushing changes:

```bash
python3 scripts/validate_skills.py
```

Individual skills can also be checked with Codex's skill-creator validator:

```bash
python3 /Users/tonyoutlier/.codex/skills/.system/skill-creator/scripts/quick_validate.py git-period-report
```
