---
name: link-agent-skills
description: "Symlink agent skills from standard directory (~/.agents/skills) to Antigravity global skills directory (~/.gemini/config/skills) with automatic conflict resolution. Use when the user asks to link, sync, or make skills installed via the community `skills` CLI work seamlessly inside Antigravity."
---

# Link Agent Skills

## Overview

Community `skills` CLI tools install skills into `~/.agents/skills/`. However, Google Antigravity discovers global skills in `~/.gemini/config/skills/` and builtin skills in `~/.gemini/antigravity-cli/builtin/skills/`.

This skill provides an automated, idempotent bridge that symlinks skills from `~/.agents/skills/` into Antigravity's global skills path (`~/.gemini/config/skills/`), with built-in conflict resolution:
- **Not installed in Antigravity**: Creates a symlink pointing to `~/.agents/skills/<skill-name>`.
- **Already linked correctly**: Skips without modifying (idempotent no-op).
- **Installed as a real directory or file**: Safely removes the existing Antigravity folder/file first, then creates the symlink.
- **Broken or mismatched symlink**: Replaces the symlink with the correct target.

## Usage

### 1. Synchronize All Skills

Run the sync script to link all skills in `~/.agents/skills`:

```bash
python3 <skill-dir>/scripts/link_agent_skills.py
```

### 2. Preview Changes (Dry Run)

To see what actions would be taken without modifying the filesystem:

```bash
python3 <skill-dir>/scripts/link_agent_skills.py --dry-run
```

### 3. Link a Specific Skill

To link only a specific skill:

```bash
python3 <skill-dir>/scripts/link_agent_skills.py --skill <skill-name>
```

### 4. Clean Up Broken Links

To remove dead/dangling symlinks in Antigravity's skill directory:

```bash
python3 <skill-dir>/scripts/link_agent_skills.py --clean-broken
```

### 5. Custom Directories

If using non-standard directory locations:

```bash
python3 <skill-dir>/scripts/link_agent_skills.py --source /path/to/source/skills --target /path/to/gemini/skills
```

### 6. JSON Output

For programmatic consumption:

```bash
python3 <skill-dir>/scripts/link_agent_skills.py --json
```

## Conflict Resolution Rules

| Current Antigravity Target State | Action Taken |
| --- | --- |
| Does not exist | Create symlink to `~/.agents/skills/<name>` |
| Symlink pointing to exact source | Skip (no-op, idempotent) |
| Symlink pointing to wrong / broken path | Unlink and recreate symlink |
| Real directory (existing non-symlink install) | Delete existing directory and create symlink |
| Real file (non-symlink) | Delete existing file and create symlink |

## Verification

After linking, verify the links in Antigravity's skills directory:

```bash
ls -la ~/.gemini/config/skills/
```

Restart or launch Antigravity CLI to immediately load the linked skills.
