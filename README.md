# Personal Agent Skills

This repository stores personal skills for Codex and other agent runtimes.

## Skills

<!-- SKILLS_TABLE_START -->
| Skill | Purpose |
| --- | --- |
| `blackbox-acceptance-gate` | Gate changes through approved criteria, isolated black-box testing, verifiable evidence, and a traceable verdict. |
| `career-agent` | Maintain career memory and generate grounded job-search materials. |
| `git-period-report` | Generate weekly, monthly, or custom-period reports from Git history and final-state diffs. |
| `link-agents-skills` | Symlink universal agent skills from standard hub (`~/.agents/skills`) to agent directories with conflict resolution. |
| `pr-tag-release` | Automate PR merge tagging (`v<Major>.<PR_ID>.<commits>`), GitHub Releases, and out-of-order PR backfills. |
| `repair-git-history` | Audit and safely repair Git identities, messages, tags, and release history. |
<!-- SKILLS_TABLE_END -->

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

To automatically synchronize the skills table in `README.md`:

```bash
python3 scripts/validate_skills.py --sync
```

Individual skills can also be checked with Codex's skill-creator validator:

```bash
python3 /Users/tonyoutlier/.codex/skills/.system/skill-creator/scripts/quick_validate.py git-period-report
```

## Agent Guidelines

See [AGENTS.md](AGENTS.md) for repository-level rules and iron laws, including GitHub account resolution from `remote.origin.url`.
