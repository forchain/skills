#!/usr/bin/env python3
"""
link_agent_skills.py

Links skills from ~/.agents/skills (or custom source) to Antigravity's global
skills directory ~/.gemini/config/skills.

Conflict resolution rules:
1. Target does not exist -> create symlink.
2. Target is already a symlink pointing to the exact source -> skip (no-op).
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
from dataclasses import asdict, dataclass
from pathlib import Path


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
    message: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "skill_name": self.skill_name,
            "action": self.action.value,
            "source_path": self.source_path,
            "target_path": self.target_path,
            "message": self.message,
        }


def default_source_dir() -> Path:
    return Path.home() / ".agents" / "skills"


def default_target_dir() -> Path:
    return Path.home() / ".gemini" / "config" / "skills"


def link_skill(
    skill_name: str,
    source_dir: Path | str,
    target_dir: Path | str,
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
        action=Action.CREATED,
        source_path=str(source_skill),
        target_path=str(target_link),
        message=f"Created symlink -> {source_skill}",
    )


def sync_skills(
    source_dir: Path | str,
    target_dir: Path | str,
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
        res = link_skill(name, source_root, target_root, dry_run=dry_run, force=force)
        results.append(res)

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
        description="Symlink skills from ~/.agents/skills into Antigravity global skills directory."
    )
    parser.add_argument(
        "--source",
        "-s",
        type=Path,
        default=default_source_dir(),
        help="Source directory containing agent skills (default: ~/.agents/skills)",
    )
    parser.add_argument(
        "--target",
        "-t",
        type=Path,
        default=default_target_dir(),
        help="Target directory for Antigravity skills (default: ~/.gemini/config/skills)",
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
        help="Clean up broken/dangling symlinks in target directory",
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
    target_dir = args.target.expanduser()

    if not source_dir.exists():
        # Check if ~/.agents exists and has subdirectories directly
        alt_source = source_dir.parent
        if alt_source.exists() and (alt_source / "skills").exists():
            source_dir = alt_source / "skills"
        else:
            if not args.quiet:
                print(f"Error: Source directory {source_dir} does not exist.", file=sys.stderr)
            return 1

    cleaned: list[str] = []
    if args.clean_broken:
        cleaned = clean_broken_symlinks(target_dir, dry_run=args.dry_run)

    results = sync_skills(
        source_dir=source_dir,
        target_dir=target_dir,
        skill_names=args.skills,
        dry_run=args.dry_run,
        force=args.force,
    )

    if args.json:
        payload = {
            "dry_run": args.dry_run,
            "source": str(source_dir),
            "target": str(target_dir),
            "cleaned_broken": cleaned,
            "results": [r.to_dict() for r in results],
        }
        print(json.dumps(payload, indent=2))
        return 0

    if not args.quiet:
        prefix = "[DRY-RUN] " if args.dry_run else ""
        print(f"{prefix}Source: {source_dir}")
        print(f"{prefix}Target: {target_dir}")
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

            print(f"{symbol} {r.skill_name}: {r.message}")

        if cleaned:
            print(f"🧹 [CLEANED] Removed {len(cleaned)} broken link(s): {', '.join(cleaned)}")

        print("-" * 60)
        print(
            f"Summary: {len(results)} total | {created_count} created | "
            f"{skipped_count} skipped | {replaced_count} replaced | "
            f"{updated_count} updated | {failed_count} failed"
        )

    has_failures = any(r.action == Action.FAILED for r in results)
    return 1 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
