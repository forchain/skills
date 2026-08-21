# PRD: Link Agent Skills to Antigravity (`link-agent-skills`)

## Problem Statement

Community `skills` CLI tools and agent standards often install skills into `~/.agents/skills/`. However, Antigravity scans `~/.gemini/config/skills/` for global skills and `~/.gemini/antigravity-cli/builtin/skills/` for builtin skills.

When a user installs skills via `skills add ...`, Antigravity cannot discover them unless they are symlinked to `~/.gemini/config/skills/`. Furthermore:
1. If Antigravity already has a real directory installed with the same name, a simple `ln -s` command fails or nests inside it. The existing directory needs to be cleanly deleted first before creating the link.
2. If an identical, valid symlink already exists, it should be preserved without unnecessary operations.
3. If a symlink is broken or points elsewhere, it should be updated.

## Solution

Build a `link-agent-skills` skill and standalone utility script `scripts/link_agent_skills.py` that:
1. Scans `~/.agents/skills/` (configurable via `--source`).
2. Iterates over each skill and checks the target in `~/.gemini/config/skills/` (configurable via `--target`).
3. Handles conflicts cleanly:
   - Target not present -> create symlink.
   - Target is valid symlink to source -> skip (no-op).
   - Target is real folder/file -> delete target and create symlink.
   - Target is invalid/broken symlink -> unlink and recreate symlink.
4. Supports `--dry-run`, `--skill <name>`, `--clean-broken`.
5. Includes automated test coverage and documentation.
