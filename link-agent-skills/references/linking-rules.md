# Linking Rules and Directory Mapping

## Directory Structure and Discovery

- **Community Agent Standard**: `~/.agents/skills/<skill-name>/SKILL.md`
- **Antigravity Global Configuration**: `~/.gemini/config/skills/<skill-name>/SKILL.md`
- **Antigravity Built-in Skills**: `~/.gemini/antigravity-cli/builtin/skills/<skill-name>/SKILL.md`

## Why Symlinking is Preferred

1. **Live Updates**: When you update skills in `~/.agents/skills` (via `git pull` or `skills update`), Antigravity immediately reads the updated files through the symlink.
2. **Single Source of Truth**: Prevents divergent copies and drift between tools.
3. **Safe Conflict Resolution**: If an older version was installed as a static directory directly into Antigravity, the linking tool removes the static folder before creating the symlink, avoiding nested directory bugs (`ln -s source target_dir/`).

## Verification Commands

Check active symlinks:
```bash
ls -la ~/.gemini/config/skills/
```

Test a specific skill link:
```bash
python3 link-agent-skills/scripts/link_agent_skills.py --dry-run
```
