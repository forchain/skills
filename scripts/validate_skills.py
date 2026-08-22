#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
TABLE_START_MARKER = "<!-- SKILLS_TABLE_START -->"
TABLE_END_MARKER = "<!-- SKILLS_TABLE_END -->"


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("unterminated YAML frontmatter")
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        if ":" in value and not value.strip().startswith(("\"", "'")):
            raise ValueError(f"frontmatter value containing ':' must be quoted: {key.strip()}")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def extract_purpose(frontmatter: dict[str, str]) -> str:
    if "summary" in frontmatter and frontmatter["summary"].strip():
        return frontmatter["summary"].strip()
    
    desc = frontmatter.get("description", "").strip()
    if not desc:
        return ""
    
    # Remove trigger phrases like 'Use when...' or 'Use this when...'
    match = re.split(r"\s+Use (?:this|when)\b", desc, maxsplit=1, flags=re.IGNORECASE)
    first_part = match[0].strip()
    if not first_part.endswith("."):
        first_part += "."
    return first_part


def get_skill_entries(root: Path) -> list[dict[str, str]]:
    skill_dirs = [
        path for path in root.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists() and not path.name.startswith(".")
    ]
    entries: list[dict[str, str]] = []
    for skill_dir in sorted(skill_dirs, key=lambda p: p.name):
        skill_md = skill_dir / "SKILL.md"
        try:
            frontmatter = parse_frontmatter(skill_md)
            name = frontmatter.get("name", skill_dir.name)
            purpose = extract_purpose(frontmatter)
        except Exception:
            name = skill_dir.name
            purpose = ""
        entries.append({"name": name, "purpose": purpose})
    return entries


def generate_skills_table(skills: list[dict[str, str]]) -> str:
    lines = [
        "| Skill | Purpose |",
        "| --- | --- |",
    ]
    for item in skills:
        lines.append(f"| `{item['name']}` | {item['purpose']} |")
    return "\n".join(lines)


def update_readme_text(content: str, table: str) -> str:
    start_idx = content.find(TABLE_START_MARKER)
    end_idx = content.find(TABLE_END_MARKER)
    if start_idx == -1 or end_idx == -1 or start_idx >= end_idx:
        raise ValueError(
            f"markers not found or malformed: {TABLE_START_MARKER} and {TABLE_END_MARKER}"
        )
    before = content[: start_idx + len(TABLE_START_MARKER)]
    after = content[end_idx:]
    return f"{before}\n{table}\n{after}"


def validate_readme_catalog(root: Path) -> list[str]:
    readme_path = root / "README.md"
    if not readme_path.exists():
        return ["README.md: file does not exist"]
    content = readme_path.read_text(encoding="utf-8")
    if TABLE_START_MARKER not in content or TABLE_END_MARKER not in content:
        return [
            f"README.md: missing table markers {TABLE_START_MARKER} and {TABLE_END_MARKER}"
        ]
    skills = get_skill_entries(root)
    table = generate_skills_table(skills)
    try:
        expected_content = update_readme_text(content, table)
    except ValueError as exc:
        return [f"README.md: {exc}"]
    
    if content != expected_content:
        return [
            "README.md: skill catalog is out of sync. Run 'python3 scripts/validate_skills.py --sync' to update."
        ]
    return []


def sync_readme(root: Path) -> None:
    readme_path = root / "README.md"
    if not readme_path.exists():
        raise FileNotFoundError(f"{readme_path} not found")
    content = readme_path.read_text(encoding="utf-8")
    skills = get_skill_entries(root)
    table = generate_skills_table(skills)
    updated_content = update_readme_text(content, table)
    readme_path.write_text(updated_content, encoding="utf-8")


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return []
    try:
        frontmatter = parse_frontmatter(skill_md)
    except Exception as exc:
        return [f"{skill_md}: {exc}"]

    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")
    if name != skill_dir.name:
        errors.append(f"{skill_md}: name must match directory ({skill_dir.name})")
    if not SKILL_NAME_RE.match(name):
        errors.append(f"{skill_md}: invalid skill name {name!r}")
    if not description:
        errors.append(f"{skill_md}: description is required")

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        errors.append(f"{openai_yaml}: missing agents metadata")
    else:
        text = openai_yaml.read_text(encoding="utf-8")
        if f"${name}" not in text:
            errors.append(f"{openai_yaml}: default prompt should mention ${name}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and sync repository skills and README catalog.")
    parser.add_argument(
        "--sync",
        "--fix",
        dest="sync",
        action="store_true",
        help="Synchronize the skills table in README.md with existing skills.",
    )
    args = parser.parse_args(argv)

    errors: list[str] = []
    skill_dirs = [
        path for path in ROOT.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists() and not path.name.startswith(".")
    ]
    if not skill_dirs:
        errors.append("no skills found")
    for skill_dir in sorted(skill_dirs, key=lambda p: p.name):
        errors.extend(validate_skill(skill_dir))

    if args.sync:
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        try:
            sync_readme(ROOT)
            print(f"synchronized README.md catalog for {len(skill_dirs)} skill(s)")
            return 0
        except Exception as exc:
            print(f"failed to sync README.md: {exc}", file=sys.stderr)
            return 1

    errors.extend(validate_readme_catalog(ROOT))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"validated {len(skill_dirs)} skill(s) and README.md catalog")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
