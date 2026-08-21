# Multi-Agent Linking Rules and Directory Mapping

## Directory Structure and Discovery

- **Universal Agent Hub (Source)**: `~/.agents/skills/<skill-name>/`
- **Google Antigravity Target**: `~/.gemini/config/skills/<skill-name>/`
- **Claude Code Target**: `~/.claude/skills/<skill-name>/`
- **Custom / Future Agent Target**: Configurable via `--target <path>`

## Why Symlinking to Universal Hub is Preferred

1. **Centralized Management**: Install or update skills once in `~/.agents/skills` (via `skills add ...` or `git pull`), and all agents immediately access the updated skills.
2. **Prevents Drift & Redundancy**: Avoids multiple diverging copies across tools.
3. **Safe Conflict Handling**: Replaces static directory copies with symlinks so updates propagate cleanly without nesting issues.

## Adding Future Non-Standard Agents

To add support for a new AI agent runtime, simply add its default skill config directory to `AGENT_TARGET_PRESETS` in `scripts/link_agents_skills.py`:

```python
AGENT_TARGET_PRESETS: dict[str, Path] = {
    "antigravity": Path.home() / ".gemini" / "config" / "skills",
    "claude": Path.home() / ".claude" / "skills",
    "new_agent": Path.home() / ".new_agent" / "skills",
}
```
