# Issue 1 (#7): Build the `link-agents-skills` Skill Package and Multi-Agent Symlink Engine

## What to build

Create the `link-agents-skills` skill package and execution script that automatically symlinks skills from the universal directory `~/.agents/skills` to non-standard agent directories (Antigravity `~/.gemini/config/skills`, Claude `~/.claude/skills`, and future custom agents).

The engine should inspect each skill directory in the source path and apply the following deterministic rules across all target agents:
1. **Target does not exist**: Create symlink pointing to the source skill directory.
2. **Target is already a valid symlink to source**: Do nothing (no-op, idempotent).
3. **Target is an existing regular directory or file (agent already installed a copy)**: Remove the existing directory/file first, then create the symlink to the source skill directory.
4. **Target is a broken or mismatched symlink**: Replace with the correct symlink.

The skill must also provide:
- `link-agents-skills/SKILL.md`: Standardized frontmatter and clear instructions for running, dry-running, and managing links across Antigravity and Claude.
- `link-agents-skills/agents/openai.yaml`: Standard agent metadata referencing `$link-agents-skills`.
- `link-agents-skills/scripts/link_agents_skills.py`: Python CLI supporting `--source`, `--agent [antigravity|claude|all]`, `--target <path>`, `--dry-run`, `--skill <name>`, and `--clean-broken`.
- `link-agents-skills/tests/test_link_agents_skills.py`: Unit test suite covering all agent presets and conflict resolution decision branches.

## Acceptance criteria

- [x] `link-agents-skills/SKILL.md` contains valid frontmatter (`name: link-agents-skills`, description) matching directory name.
- [x] `link-agents-skills/agents/openai.yaml` exists and references `$link-agents-skills`.
- [x] `python3 scripts/validate_skills.py` passes with zero errors.
- [x] `link-agents-skills/scripts/link_agents_skills.py` supports target agents (`antigravity`, `claude`, `all`, custom target path).
- [x] Existing regular folders/files in targets are safely removed before creating symlinks.
- [x] Existing valid symlinks pointing to target are preserved without redundant operations.
- [x] Broken or redirected symlinks are cleanly replaced.
- [x] `--dry-run` accurately previews actions without making filesystem modifications.
- [x] Comprehensive unit test suite in `tests/test_link_agents_skills.py` passes all test cases.

## Blocked by

None - can start immediately.
