#!/usr/bin/env python3
"""
link_agents_skills.py

Links skills from universal directory (~/.agents/skills) to non-standard agent
directories (Google Antigravity, Claude Code, etc.).

Target Presets:
- antigravity : ~/.gemini/config/skills
- claude      : ~/.claude/skills
- all         : all supported agents

Conflict resolution rules:
1. Target does not exist -> create symlink.
2. Target is already a symlink pointing to exact source -> skip (no-op).
3. Target is an existing real directory -> remove existing directory and symlink.
4. Target is an existing real file -> remove existing file and symlink.
5. Target is a broken or mismatched symlink -> replace with valid symlink.
"""

from __future__ import annotations

import argparse
import enum
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


AGENT_TARGET_PRESETS: dict[str, Path] = {
    "antigravity": Path.home() / ".gemini" / "config" / "skills",
    "claude": Path.home() / ".claude" / "skills",
}


class Action(str, enum.Enum):
    CREATED = "created"
    SKIPPED_ALREADY_LINKED = "skipped_already_linked"
    REPLACED_REAL_DIRECTORY = "replaced_real_directory"
    REPLACED_REAL_FILE = "replaced_real_file"
    UPDATED_SYMLINK = "updated_symlink"
    FAILED = "failed"


@dataclass
class LinkResult:
    skill_name: str
    action: Action
    source_path: str
    target_path: str
    agent: str = "custom"
    message: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "skill_name": self.skill_name,
            "agent": self.agent,
            "action": self.action.value,
            "source_path": self.source_path,
            "target_path": self.target_path,
            "message": self.message,
        }


def default_source_dir() -> Path:
    return Path.home() / ".agents" / "skills"


def link_skill(
    skill_name: str,
    source_dir: Path | str,
    target_dir: Path | str,
    agent_name: str = "custom",
    dry_run: bool = False,
    force: bool = False,
) -> LinkResult:
    source_root = Path(source_dir).expanduser().resolve()
    target_root = Path(target_dir).expanduser().resolve()

    source_skill = source_root / skill_name
    target_link = target_root / skill_name

    if not source_skill.exists():
        return LinkResult(
            skill_name=skill_name,
            agent=agent_name,
            action=Action.FAILED,
            source_path=str(source_skill),
            target_path=str(target_link),
            message=f"Source skill does not exist: {source_skill}",
        )

    # Check if target is a symlink (including broken symlinks)
    if target_link.is_symlink():
        try:
            raw_target = os.readlink(target_link)
            resolved_link = Path(raw_target).expanduser()
            if not resolved_link.is_absolute():
                resolved_link = (target_link.parent / resolved_link).resolve()
            else:
                resolved_link = resolved_link.resolve()

            if not force and (resolved_link == source_skill.resolve() or raw_target == str(source_skill)):
                return LinkResult(
                    skill_name=skill_name,
                    agent=agent_name,
                    action=Action.SKIPPED_ALREADY_LINKED,
                    source_path=str(source_skill),
                    target_path=str(target_link),
                    message=f"Already linked to {source_skill}",
                )
        except Exception:
            pass

        # If it's a symlink pointing elsewhere or broken or force=True
        if not dry_run:
            target_link.unlink()
            target_link.symlink_to(source_skill)
        return LinkResult(
            skill_name=skill_name,
            agent=agent_name,
            action=Action.UPDATED_SYMLINK,
            source_path=str(source_skill),
            target_path=str(target_link),
            message=f"Updated symlink -> {source_skill}",
        )

    # Check if target exists as a regular directory or file
    if target_link.exists():
        if target_link.is_dir():
            if not dry_run:
                shutil.rmtree(target_link)
                target_link.symlink_to(source_skill)
            return LinkResult(
                skill_name=skill_name,
                agent=agent_name,
                action=Action.REPLACED_REAL_DIRECTORY,
                source_path=str(source_skill),
                target_path=str(target_link),
                message=f"Removed existing real directory and linked -> {source_skill}",
            )
        else:
            if not dry_run:
                target_link.unlink()
                target_link.symlink_to(source_skill)
            return LinkResult(
                skill_name=skill_name,
                agent=agent_name,
                action=Action.REPLACED_REAL_FILE,
                source_path=str(source_skill),
                target_path=str(target_link),
                message=f"Removed existing real file and linked -> {source_skill}",
            )

    # Target does not exist at all
    if not dry_run:
        target_root.mkdir(parents=True, exist_ok=True)
        target_link.symlink_to(source_skill)

    return LinkResult(
        skill_name=skill_name,
        agent=agent_name,
        action=Action.CREATED,
        source_path=str(source_skill),
        target_path=str(target_link),
        message=f"Created symlink -> {source_skill}",
    )


def sync_skills(
    source_dir: Path | str,
    target_dir: Path | str,
    agent_name: str = "custom",
    skill_names: list[str] | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> list[LinkResult]:
    source_root = Path(source_dir).expanduser().resolve()
    target_root = Path(target_dir).expanduser().resolve()

    if not source_root.exists():
        return []

    if not dry_run:
        target_root.mkdir(parents=True, exist_ok=True)

    if skill_names:
        names_to_link = skill_names
    else:
        names_to_link = sorted(
            [d.name for d in source_root.iterdir() if d.is_dir() and not d.name.startswith(".")]
        )

    results: list[LinkResult] = []
    for name in names_to_link:
        res = link_skill(
            skill_name=name,
            source_dir=source_root,
            target_dir=target_root,
            agent_name=agent_name,
            dry_run=dry_run,
            force=force,
        )
        results.append(res)

    return results


def sync_to_agents(
    source_dir: Path | str,
    target_agents: list[str],
    skill_names: list[str] | None = None,
    dry_run: bool = False,
    force: bool = False,
    presets: dict[str, Path] | None = None,
) -> list[LinkResult]:
    active_presets = presets or AGENT_TARGET_PRESETS
    results: list[LinkResult] = []

    for agent_key in target_agents:
        if agent_key not in active_presets:
            continue
        agent_dir = active_presets[agent_key]
        agent_results = sync_skills(
            source_dir=source_dir,
            target_dir=agent_dir,
            agent_name=agent_key,
            skill_names=skill_names,
            dry_run=dry_run,
            force=force,
        )
        results.extend(agent_results)

    return results


def clean_broken_symlinks(target_dir: Path | str, dry_run: bool = False) -> list[str]:
    target_root = Path(target_dir).expanduser().resolve()
    if not target_root.exists():
        return []

    removed: list[str] = []
    for item in target_root.iterdir():
        if item.is_symlink() and not item.exists():
            if not dry_run:
                item.unlink()
            removed.append(item.name)
    return removed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Symlink skills from ~/.agents/skills into non-standard agent directories (Antigravity, Claude, etc.)."
    )
    parser.add_argument(
        "--source",
        "-s",
        type=Path,
        default=default_source_dir(),
        help="Source directory containing universal agent skills (default: ~/.agents/skills)",
    )
    parser.add_argument(
        "--agent",
        "-a",
        default="all",
        choices=["antigravity", "claude", "all"],
        help="Target agent preset to link into (choices: antigravity, claude, all; default: all)",
    )
    parser.add_argument(
        "--target",
        "-t",
        type=Path,
        help="Explicit target directory for a custom agent (overrides --agent)",
    )
    parser.add_argument(
        "--skill",
        action="append",
        dest="skills",
        help="Specific skill name(s) to link. Can be specified multiple times.",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Simulate the actions without making filesystem modifications",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force recreating existing symlinks",
    )
    parser.add_argument(
        "--clean-broken",
        action="store_true",
        help="Clean up broken/dangling symlinks in target directory(ies)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress informational output",
    )

    args = parser.parse_args(argv)

    source_dir = args.source.expanduser()

    if not source_dir.exists():
        alt_source = source_dir.parent
        if alt_source.exists() and (alt_source / "skills").exists():
            source_dir = alt_source / "skills"
        else:
            if not args.quiet:
                print(f"Error: Source directory {source_dir} does not exist.", file=sys.stderr)
            return 1

    # Determine targets
    cleaned: dict[str, list[str]] = {}
    results: list[LinkResult] = []

    if args.target:
        target_dir = args.target.expanduser()
        if args.clean_broken:
            cleaned["custom"] = clean_broken_symlinks(target_dir, dry_run=args.dry_run)
        results = sync_skills(
            source_dir=source_dir,
            target_dir=target_dir,
            agent_name="custom",
            skill_names=args.skills,
            dry_run=args.dry_run,
            force=args.force,
        )
    else:
        agents_to_sync = (
            list(AGENT_TARGET_PRESETS.keys()) if args.agent == "all" else [args.agent]
        )
        if args.clean_broken:
            for ag in agents_to_sync:
                c = clean_broken_symlinks(AGENT_TARGET_PRESETS[ag], dry_run=args.dry_run)
                if c:
                    cleaned[ag] = c

        results = sync_to_agents(
            source_dir=source_dir,
            target_agents=agents_to_sync,
            skill_names=args.skills,
            dry_run=args.dry_run,
            force=args.force,
        )

    if args.json:
        payload = {
            "dry_run": args.dry_run,
            "source": str(source_dir),
            "cleaned_broken": cleaned,
            "results": [r.to_dict() for r in results],
        }
        print(json.dumps(payload, indent=2))
        return 0

    if not args.quiet:
        prefix = "[DRY-RUN] " if args.dry_run else ""
        print(f"{prefix}Source (Universal): {source_dir}")
        print("-" * 60)

        created_count = 0
        skipped_count = 0
        replaced_count = 0
        updated_count = 0
        failed_count = 0

        for r in results:
            if r.action == Action.CREATED:
                created_count += 1
                symbol = "➕ [CREATED]"
            elif r.action == Action.SKIPPED_ALREADY_LINKED:
                skipped_count += 1
                symbol = "⏭️  [SKIPPED]"
            elif r.action in (Action.REPLACED_REAL_DIRECTORY, Action.REPLACED_REAL_FILE):
                replaced_count += 1
                symbol = "🔄 [REPLACED]"
            elif r.action == Action.UPDATED_SYMLINK:
                updated_count += 1
                symbol = "🔗 [UPDATED]"
            else:
                failed_count += 1
                symbol = "❌ [FAILED]"

            print(f"{symbol} [{r.agent}] {r.skill_name}: {r.message}")

        for ag, items in cleaned.items():
            print(f"🧹 [CLEANED] [{ag}] Removed {len(items)} broken link(s): {', '.join(items)}")

        print("-" * 60)
        print(
            f"Summary: {len(results)} operations | {created_count} created | "
            f"{skipped_count} skipped | {replaced_count} replaced | "
            f"{updated_count} updated | {failed_count} failed"
        )

    has_failures = any(r.action == Action.FAILED for r in results)
    return 1 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
