---
name: link-agents-skills
description: "Symlink universal agent skills from standard hub (~/.agents/skills) to non-standard agent directories (Google Antigravity ~/.gemini/config/skills, Claude Code ~/.claude/skills, etc.) with automatic conflict resolution. Use when the user asks to link, sync, or make skills installed via the community `skills` CLI work seamlessly across Antigravity, Claude, and other AI agents."
---

# Link Agents Skills

## Overview

Community `skills` CLI tools install skills into the universal directory `~/.agents/skills/`. However, different AI agents scan their own vendor-specific directory paths:
- **Google Antigravity**: `~/.gemini/config/skills/`
- **Claude Code**: `~/.claude/skills/`
- **Other Non-Standard Agents**: Custom agent directories

This skill provides an automated, idempotent bridge that symlinks skills from the universal `~/.agents/skills/` hub to all supported or targeted non-standard agents, with built-in conflict resolution:
- **Not installed in target agent**: Creates a symlink pointing to `~/.agents/skills/<skill-name>`.
- **Already linked correctly**: Skips without modifying (idempotent no-op).
- **Installed as a real directory or file in agent**: Safely removes the existing agent folder/file first, then creates the symlink.
- **Broken or mismatched symlink**: Replaces the symlink with the correct target.

## Usage

### 1. Synchronize to All Supported Agents (Default)

Links all skills in `~/.agents/skills` to both Antigravity and Claude:

```bash
python3 <skill-dir>/scripts/link_agents_skills.py
```

### 2. Synchronize to a Specific Agent

Target only Antigravity:
```bash
python3 <skill-dir>/scripts/link_agents_skills.py --agent antigravity
```

Target only Claude Code:
```bash
python3 <skill-dir>/scripts/link_agents_skills.py --agent claude
```

### 3. Preview Changes (Dry Run)

To see what actions would be taken without modifying the filesystem:

```bash
python3 <skill-dir>/scripts/link_agents_skills.py --dry-run
```

### 4. Link a Specific Skill

To link only a specific skill to all agents:

```bash
python3 <skill-dir>/scripts/link_agents_skills.py --skill <skill-name>
```

### 5. Clean Up Broken Links

To remove dead/dangling symlinks in target directories:

```bash
python3 <skill-dir>/scripts/link_agents_skills.py --clean-broken
```

### 6. Custom Directories

Target a custom or future non-standard agent directory:

```bash
python3 <skill-dir>/scripts/link_agents_skills.py --target /path/to/custom/agent/skills
```

### 7. JSON Output

For programmatic consumption:

```bash
python3 <skill-dir>/scripts/link_agents_skills.py --json
```

## Conflict Resolution Rules

| Current Agent Target State | Action Taken |
| --- | --- |
| Does not exist | Create symlink to `~/.agents/skills/<name>` |
| Symlink pointing to exact source | Skip (no-op, idempotent) |
| Symlink pointing to wrong / broken path | Unlink and recreate symlink |
| Real directory (existing non-symlink install) | Delete existing directory and create symlink |
| Real file (non-symlink) | Delete existing file and create symlink |

## Verification

After linking, verify the links in the respective agent directories:

```bash
# Antigravity
ls -la ~/.gemini/config/skills/

# Claude Code
ls -la ~/.claude/skills/
```
