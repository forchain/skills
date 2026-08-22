from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Ensure root is in sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

from scripts.validate_skills import (
    generate_skills_table,
    update_readme_text,
    validate_readme_catalog,
    get_skill_entries,
    parse_frontmatter,
)


def test_parse_frontmatter_with_summary(tmp_path: Path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(
        "---\n"
        "name: my-skill\n"
        "description: Full description for agents. Use when needed.\n"
        "summary: Short human summary.\n"
        "---\n"
        "# My Skill\n",
        encoding="utf-8",
    )
    data = parse_frontmatter(skill_md)
    assert data["name"] == "my-skill"
    assert data["description"] == "Full description for agents. Use when needed."
    assert data["summary"] == "Short human summary."


def test_generate_skills_table():
    skills = [
        {"name": "alpha-skill", "purpose": "Alpha purpose description."},
        {"name": "beta-skill", "purpose": "Beta purpose description."},
    ]
    table = generate_skills_table(skills)
    expected = (
        "| Skill | Purpose |\n"
        "| --- | --- |\n"
        "| `alpha-skill` | Alpha purpose description. |\n"
        "| `beta-skill` | Beta purpose description. |"
    )
    assert table.strip() == expected.strip()


def test_update_readme_text():
    content = (
        "# Title\n\n"
        "## Skills\n\n"
        "<!-- SKILLS_TABLE_START -->\n"
        "old table\n"
        "<!-- SKILLS_TABLE_END -->\n\n"
        "## Next Section\n"
    )
    new_table = "| Skill | Purpose |\n| --- | --- |\n| `foo` | Bar. |"
    updated = update_readme_text(content, new_table)
    expected = (
        "# Title\n\n"
        "## Skills\n\n"
        "<!-- SKILLS_TABLE_START -->\n"
        "| Skill | Purpose |\n"
        "| --- | --- |\n"
        "| `foo` | Bar. |\n"
        "<!-- SKILLS_TABLE_END -->\n\n"
        "## Next Section\n"
    )
    assert updated == expected


def test_update_readme_text_missing_markers():
    content = "# Title\n\n## Skills\n\nNo markers here\n"
    with pytest.raises(ValueError, match="markers not found"):
        update_readme_text(content, "some table")


def test_validate_readme_catalog_out_of_sync(tmp_path: Path):
    root = tmp_path
    skill_dir = root / "skill-a"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: skill-a\ndescription: Skill A.\nsummary: Purpose of A.\n---\n",
        encoding="utf-8",
    )
    readme = root / "README.md"
    readme.write_text(
        "<!-- SKILLS_TABLE_START -->\n<!-- SKILLS_TABLE_END -->\n",
        encoding="utf-8",
    )

    errors = validate_readme_catalog(root)
    assert len(errors) == 1
    assert "README.md: skill catalog is out of sync" in errors[0]


def test_validate_readme_catalog_in_sync(tmp_path: Path):
    root = tmp_path
    skill_dir = root / "skill-a"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: skill-a\ndescription: Skill A.\nsummary: Purpose of A.\n---\n",
        encoding="utf-8",
    )
    skills = get_skill_entries(root)
    table = generate_skills_table(skills)
    readme = root / "README.md"
    readme.write_text(
        f"# Readme\n\n<!-- SKILLS_TABLE_START -->\n{table}\n<!-- SKILLS_TABLE_END -->\n",
        encoding="utf-8",
    )

    errors = validate_readme_catalog(root)
    assert errors == []


def test_cli_check_and_sync_flags(tmp_path: Path):
    root = tmp_path
    # Copy scripts to tmp_path / scripts
    scripts_dir = root / "scripts"
    scripts_dir.mkdir()
    validate_script = ROOT_DIR / "scripts" / "validate_skills.py"
    (scripts_dir / "validate_skills.py").write_text(validate_script.read_text(encoding="utf-8"), encoding="utf-8")

    # Create dummy skill
    skill_dir = root / "dummy-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: dummy-skill\ndescription: A dummy skill. Use when testing.\nsummary: A dummy skill.\n---\n",
        encoding="utf-8",
    )
    agents_dir = skill_dir / "agents"
    agents_dir.mkdir()
    (agents_dir / "openai.yaml").write_text("prompt: $dummy-skill\n", encoding="utf-8")

    readme = root / "README.md"
    readme.write_text(
        "# Repo\n\n<!-- SKILLS_TABLE_START -->\n<!-- SKILLS_TABLE_END -->\n",
        encoding="utf-8",
    )

    # Running check should fail
    proc = subprocess.run(
        [sys.executable, str(scripts_dir / "validate_skills.py")],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "README.md: skill catalog is out of sync" in proc.stderr

    # Running --sync should succeed and update README.md
    proc_sync = subprocess.run(
        [sys.executable, str(scripts_dir / "validate_skills.py"), "--sync"],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    assert proc_sync.returncode == 0
    assert "`dummy-skill`" in readme.read_text(encoding="utf-8")

    # Running check again should succeed
    proc_check = subprocess.run(
        [sys.executable, str(scripts_dir / "validate_skills.py")],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    assert proc_check.returncode == 0
