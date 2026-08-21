# Issue 1 (#7): Build the `link-agent-skills` Skill Package and Conflict-Resolving Symlink Engine

## What to build

Create the `link-agent-skills` skill package and execution script that automatically symlinks skills from `~/.agents/skills` to Antigravity's global skill directory `~/.gemini/config/skills`.

The engine should inspect each skill directory in the source path and apply the following deterministic rules:
1. **Target does not exist**: Create symlink pointing to the source skill directory.
2. **Target is already a valid symlink to source**: Do nothing (no-op, idempotent).
3. **Target is an existing regular directory or file (Antigravity already installed a copy)**: Remove the existing directory/file in Antigravity first, then create the symlink to the source skill directory.
4. **Target is a broken or mismatched symlink**: Replace with the correct symlink.

The skill must also provide:
- `link-agent-skills/SKILL.md`: Standardized frontmatter and clear instructions for running, dry-running, and managing links.
- `link-agent-skills/agents/openai.yaml`: Standard agent metadata referencing `$link-agent-skills`.
- `link-agent-skills/scripts/link_agent_skills.py`: Python CLI supporting `--source`, `--target`, `--dry-run`, `--skill <name>`, and `--clean-broken`.
- `link-agent-skills/tests/test_link_agent_skills.py`: Unit test suite covering all decision branches (new link, already linked, delete existing real directory, fix broken link, dry-run).

## Acceptance criteria

- [x] `link-agent-skills/SKILL.md` contains valid frontmatter (`name: link-agent-skills`, description) matching directory name.
- [x] `link-agent-skills/agents/openai.yaml` exists and references `$link-agent-skills`.
- [x] `python3 scripts/validate_skills.py` passes with zero errors.
- [x] `link-agent-skills/scripts/link_agent_skills.py` correctly links `~/.agents/skills/*` to `~/.gemini/config/skills/*`.
- [x] Existing regular folders/files in target are safely removed before creating symlinks.
- [x] Existing valid symlinks pointing to target are preserved without redundant operations.
- [x] Broken or redirected symlinks are cleanly replaced.
- [x] `--dry-run` accurately previews actions without making filesystem modifications.
- [x] Comprehensive unit test suite in `tests/test_link_agent_skills.py` passes all test cases.

## Blocked by

None - can start immediately.
