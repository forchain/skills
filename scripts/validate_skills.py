#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")


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


def main() -> int:
    errors: list[str] = []
    skill_dirs = [path for path in ROOT.iterdir() if path.is_dir() and (path / "SKILL.md").exists()]
    if not skill_dirs:
        errors.append("no skills found")
    for skill_dir in sorted(skill_dirs):
        errors.extend(validate_skill(skill_dir))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"validated {len(skill_dirs)} skill(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
