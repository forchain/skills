# PRD: Link Agent Skills to Non-Standard Agents (`link-agents-skills`)

## Problem Statement

Community `skills` CLI tools and agent standards install skills into `~/.agents/skills/`. However, different AI agents discover skills from their own vendor-specific directory trees:
- **Google Antigravity**: `~/.gemini/config/skills/` (global) and `~/.gemini/antigravity-cli/builtin/skills/` (builtin)
- **Claude Code**: `~/.claude/skills/`
- **Future Non-Standard Agents**: Custom vendor directories

When a user installs or maintains skills in the universal `~/.agents/skills/` hub, other non-standard agents cannot discover them unless they are symlinked to each agent's config directory. Furthermore:
1. If an agent already has an existing static folder installed with the same name, creating a symlink without deleting the folder will fail or nest inside it.
2. If an identical, valid symlink already exists, it should be skipped (idempotent).
3. If a symlink is broken or points to a stale location, it should be updated.

## Solution

Build the `link-agents-skills` skill and CLI utility (`scripts/link_agents_skills.py`) that:
1. Uses `~/.agents/skills/` as the single source of truth (configurable via `--source`).
2. Supports built-in agent target presets:
   - `antigravity`: `~/.gemini/config/skills`
   - `claude`: `~/.claude/skills`
   - `all` (default): automatically syncs all supported agent directories
   - Custom targets via `--target <path>`
3. Handles conflicts cleanly on every target:
   - Target not present -> create symlink.
   - Target is valid symlink to source -> skip (no-op).
   - Target is real folder/file -> delete target and create symlink.
   - Target is invalid/broken symlink -> unlink and recreate symlink.
4. Supports `--dry-run`, `--skill <name>`, `--agent <name>`, `--clean-broken`.
5. Includes automated test coverage and documentation.
