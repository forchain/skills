#!/usr/bin/env python3
"""Health check and deterministic self-healing repair for Hermes Gateway."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from typing import Any


ALIYUN_PYPI_PACKAGES = "https://mirrors.aliyun.com/pypi/packages/"
FILES_PYTHONHOSTED_PACKAGES = "https://files.pythonhosted.org/packages/"
ALIYUN_PYPI_SIMPLE = "https://mirrors.aliyun.com/pypi/simple/"
NPMMIRROR_REGISTRY = "https://registry.npmmirror.com/"
LAUNCHD_LABEL = "ai.hermes.gateway"
DEFAULT_REQUIRED_PLATFORMS = ("telegram",)
DEFAULT_STUCK_AGE_S = 300


def resolve_hermes_home(hermes_home: str | Path | None = None) -> Path:
    """Resolve the active HERMES_HOME directory."""
    if hermes_home is not None:
        return Path(hermes_home).expanduser()
    env_home = os.environ.get("HERMES_HOME")
    if env_home:
        return Path(env_home).expanduser()
    dot_hermes = Path.home() / ".hermes"
    if dot_hermes.exists():
        return dot_hermes.resolve()
    volumes_hermes = Path("/Volumes/Data/.hermes")
    if volumes_hermes.exists():
        return volumes_hermes
    return dot_hermes


def resolve_hermes_bin(hermes_bin: str | None = None) -> str:
    """Resolve the hermes CLI executable path."""
    if hermes_bin:
        return hermes_bin
    local_bin = Path.home() / ".local" / "bin" / "hermes"
    if local_bin.exists() and os.access(local_bin, os.X_OK):
        return str(local_bin)
    found = shutil.which("hermes")
    return found or "hermes"


def resolve_uv_bin(hermes_home: Path) -> str:
    """Resolve the uv executable path."""
    for candidate in (
        hermes_home / "bin" / "uv",
        Path.home() / ".local" / "bin" / "uv",
    ):
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    found = shutil.which("uv")
    return found or "uv"


def find_state_file(hermes_home: Path) -> Path | None:
    """Locate gateway_state.json (or legacy gateway-state.json)."""
    for name in ("gateway_state.json", "gateway-state.json"):
        candidate = hermes_home / name
        if candidate.exists():
            return candidate
    return None


def read_json_file(path: Path) -> dict[str, Any] | None:
    """Read a JSON object from path, returning None on missing/invalid input."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def read_pid_file(pid_path: Path) -> int | None:
    """Parse gateway.pid supporting both JSON metadata and raw integer text."""
    if not pid_path.exists():
        return None
    try:
        raw = pid_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not raw:
        return None
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        pid = data.get("pid") if isinstance(data, dict) else None
        return int(pid) if isinstance(pid, int) and pid > 0 else None
    try:
        pid = int(raw.splitlines()[0].strip())
        return pid if pid > 0 else None
    except ValueError:
        return None


def is_pid_alive(pid: int | None) -> bool:
    """Check whether a Unix PID currently exists."""
    if pid is None or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def parse_ps_etime(etime: str) -> int:
    """Parse ps etime formats (MM:SS, HH:MM:SS, D-HH:MM:SS) into seconds."""
    text = etime.strip()
    if not text:
        return 0
    days = 0
    if "-" in text:
        day_part, text = text.split("-", 1)
        days = int(day_part)
    parts = [int(p) for p in text.split(":")]
    if len(parts) == 2:
        hours, minutes, seconds = 0, parts[0], parts[1]
    elif len(parts) == 3:
        hours, minutes, seconds = parts
    else:
        raise ValueError(f"Unrecognized ps etime format: {etime!r}")
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def find_stuck_processes(
    hermes_home: Path, min_age_seconds: int = DEFAULT_STUCK_AGE_S
) -> list[dict[str, Any]]:
    """Find long-running uv sync or hermes update/restart processes blocking progress."""
    try:
        proc = subprocess.run(
            ["ps", "-axo", "pid=,etime=,command="],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        return []

    home_str = str(hermes_home)
    current_pid = os.getpid()
    stuck: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        match = re.match(r"^\s*(\d+)\s+(\S+)\s+(.+)$", line)
        if not match:
            continue
        pid = int(match.group(1))
        if pid == current_pid:
            continue
        etime_raw = match.group(2)
        cmd = match.group(3)
        try:
            age_s = parse_ps_etime(etime_raw)
        except ValueError:
            continue
        if age_s <= min_age_seconds:
            continue

        is_uv_sync = "uv sync" in cmd and "--frozen" in cmd and (
            "hermes" in cmd or home_str in cmd or "uv-warm" in cmd
        )
        is_hermes_cmd = ("hermes update" in cmd or "hermes gateway restart" in cmd) and (
            home_str in cmd or "/hermes" in cmd or cmd.lstrip().startswith("hermes ")
        )
        if is_uv_sync or is_hermes_cmd:
            stuck.append({"pid": pid, "elapsed_seconds": age_s, "command": cmd})
    return stuck


def is_launchd_disabled(uid: int | None = None, label: str = LAUNCHD_LABEL) -> bool:
    """Return True on macOS when launchctl marks the gateway service disabled."""
    if sys.platform != "darwin":
        return False
    target_uid = os.getuid() if uid is None else uid
    try:
        proc = subprocess.run(
            ["launchctl", "print-disabled", f"gui/{target_uid}"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    if proc.returncode != 0:
        return False
    pattern = re.compile(rf'"{re.escape(label)}"\s*=>\s*disabled')
    return bool(pattern.search(proc.stdout))


def check_health(
    hermes_home: str | Path | None = None,
    required_platforms: tuple[str, ...] = DEFAULT_REQUIRED_PLATFORMS,
    min_stuck_age_s: int = DEFAULT_STUCK_AGE_S,
) -> dict[str, Any]:
    """Perform read-only health verification of Hermes Gateway and configured channels."""
    home = resolve_hermes_home(hermes_home)
    issues: list[str] = []
    warnings: list[str] = []

    pid_path = home / "gateway.pid"
    pid = read_pid_file(pid_path)
    pid_alive = is_pid_alive(pid)
    if pid is None:
        issues.append("gateway.pid missing or unreadable")
    elif not pid_alive:
        issues.append(f"gateway PID {pid} is not running")

    state_path = find_state_file(home)
    state_data = read_json_file(state_path) if state_path else None
    gateway_state = state_data.get("gateway_state") if state_data else None
    state_pid = state_data.get("pid") if state_data else None
    if state_data is None:
        issues.append("gateway_state.json missing or unreadable")
    else:
        if gateway_state != "running":
            issues.append(f"gateway_state is {gateway_state!r}, expected 'running'")
        if isinstance(state_pid, int) and pid is not None and state_pid != pid:
            issues.append(f"PID mismatch: gateway.pid={pid}, state.pid={state_pid}")

    platforms_raw = (state_data or {}).get("platforms")
    platforms: dict[str, Any] = platforms_raw if isinstance(platforms_raw, dict) else {}
    expected_platforms = sorted(set(required_platforms) | set(platforms.keys()))
    for name in expected_platforms:
        info = platforms.get(name)
        if not isinstance(info, dict):
            issues.append(f"platform {name!r} missing from gateway_state.json")
            continue
        p_state = info.get("state")
        err_code = info.get("error_code")
        if p_state != "connected":
            issues.append(f"platform {name!r} state is {p_state!r}, expected 'connected'")
        if err_code:
            issues.append(f"platform {name!r} reported error_code={err_code!r}")

    stuck = find_stuck_processes(home, min_age_seconds=min_stuck_age_s)
    if stuck:
        pids = ", ".join(str(item["pid"]) for item in stuck)
        issues.append(f"stuck update/uv process(es) running >{min_stuck_age_s}s: {pids}")

    paused_claims = sorted(home.glob(".hermes-update-paused-gateways*"))
    active_paused = [
        p.name for p in paused_claims if p.name != ".hermes-update-paused-gateways.lock"
    ]
    if active_paused:
        warnings.append(
            f"paused gateway state file(s) present: {', '.join(active_paused)}"
        )

    launchd_disabled = is_launchd_disabled()
    if launchd_disabled:
        warnings.append(f"launchd service {LAUNCHD_LABEL} is disabled in gui domain")

    return {
        "healthy": len(issues) == 0,
        "hermes_home": str(home),
        "state_file": str(state_path) if state_path else None,
        "pid": pid,
        "pid_alive": pid_alive,
        "gateway_state": gateway_state,
        "platforms": platforms,
        "stuck_processes": stuck,
        "launchd_disabled": launchd_disabled,
        "issues": issues,
        "warnings": warnings,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def kill_stuck_processes(
    hermes_home: Path,
    min_age_seconds: int = DEFAULT_STUCK_AGE_S,
    dry_run: bool = False,
) -> list[str]:
    """Terminate hung uv sync or hermes update processes blocking cache locks."""
    actions: list[str] = []
    stuck = find_stuck_processes(hermes_home, min_age_seconds=min_age_seconds)
    for item in stuck:
        pid = item["pid"]
        if dry_run:
            actions.append(f"would kill stuck PID {pid} ({item['command']})")
            continue
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
        except OSError as exc:
            actions.append(f"failed SIGTERM on PID {pid}: {exc}")
            continue

        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline and is_pid_alive(pid):
            time.sleep(0.1)
        if is_pid_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
        actions.append(f"killed stuck PID {pid} (elapsed {item['elapsed_seconds']}s)")
    return actions


def sanitize_uv_index_config(
    hermes_home: Path,
    home_dir: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Remove UV_INDEX_URL / pip.conf overrides that invalidate wheels-v7/pypi cache."""
    actions: list[str] = []
    user_home = home_dir or Path.home()

    pip_candidates = (
        user_home / ".pip" / "pip.conf",
        user_home / ".config" / "pip" / "pip.conf",
    )
    for pip_conf in pip_candidates:
        if not pip_conf.exists():
            continue
        try:
            content = pip_conf.read_text(encoding="utf-8")
        except OSError:
            continue
        if not re.search(r"^\s*index-url\s*=", content, flags=re.IGNORECASE | re.MULTILINE):
            continue
        backup = pip_conf.with_name(pip_conf.name + ".bak-hermes")
        if dry_run:
            actions.append(f"would back up and remove {pip_conf} -> {backup}")
            continue
        if backup.exists():
            backup.unlink()
        pip_conf.replace(backup)
        actions.append(f"moved {pip_conf} to {backup} to stop UV_INDEX_URL cache poisoning")

    env_path = hermes_home / ".env"
    if env_path.exists():
        original = env_path.read_text(encoding="utf-8")
    else:
        original = ""

    kept_lines: list[str] = []
    removed_index_url = False
    has_http_timeout = False
    for line in original.splitlines():
        if re.match(r"^\s*(?:export\s+)?UV_INDEX_URL\s*=", line):
            removed_index_url = True
            continue
        if re.match(r"^\s*(?:export\s+)?UV_HTTP_TIMEOUT\s*=", line):
            has_http_timeout = True
        kept_lines.append(line)

    added_timeout = False
    if not has_http_timeout:
        kept_lines.append("UV_HTTP_TIMEOUT=60")
        added_timeout = True

    if removed_index_url or (added_timeout and env_path.exists()):
        updated = "\n".join(kept_lines) + ("\n" if kept_lines else "")
        if dry_run:
            if removed_index_url:
                actions.append(f"would remove UV_INDEX_URL from {env_path}")
            if added_timeout:
                actions.append(f"would add UV_HTTP_TIMEOUT=60 to {env_path}")
        else:
            env_path.parent.mkdir(parents=True, exist_ok=True)
            env_path.write_text(updated, encoding="utf-8")
            if removed_index_url:
                actions.append(f"removed UV_INDEX_URL from {env_path}")
            if added_timeout:
                actions.append(f"added UV_HTTP_TIMEOUT=60 to {env_path}")
    return actions


def rewrite_uv_lock_for_mirror(
    lock_text: str,
    mirror_prefix: str = ALIYUN_PYPI_PACKAGES,
) -> str:
    """Rewrite wheel/sdist download URLs in a temporary uv.lock while keeping registry key intact."""
    return lock_text.replace(FILES_PYTHONHOSTED_PACKAGES, mirror_prefix)


def _clean_uv_env(hermes_home: Path) -> dict[str, str]:
    env = os.environ.copy()
    for key in ("UV_INDEX_URL", "PIP_INDEX_URL", "UV_DEFAULT_INDEX"):
        env.pop(key, None)
    env["UV_HTTP_TIMEOUT"] = "60"
    env.setdefault("HERMES_HOME", str(hermes_home))
    return env


def _resolve_hermes_python_and_venv(hermes_home: Path) -> tuple[str, Path | None]:
    """Locate the active Hermes venv and Python 3.14 interpreter spec."""
    install_dir = hermes_home / "hermes-agent"
    venv_candidates = [
        p
        for p in hermes_home.glob("installs/*/environments/*/venv")
        if (p / "pyvenv.cfg").exists()
    ]
    venv_dir: Path | None = None
    if venv_candidates:
        venv_dir = max(venv_candidates, key=lambda p: p.stat().st_mtime)
    else:
        for fallback in (install_dir / "venv", install_dir / ".venv"):
            if (fallback / "pyvenv.cfg").exists():
                venv_dir = fallback
                break

    python_spec: str | None = None
    for tools_root in (hermes_home / "tools", Path.home() / ".hermes" / "tools"):
        matches = sorted(tools_root.glob("python-3.14*/bin/python3"), reverse=True)
        if matches and os.access(matches[0], os.X_OK):
            python_spec = str(matches[0])
            break

    if python_spec is None and venv_dir is not None:
        venv_py = venv_dir / "bin" / "python"
        if venv_py.exists():
            python_spec = str(venv_py)

    if python_spec is None:
        py_ver_file = install_dir / ".python-version"
        if py_ver_file.exists():
            python_spec = py_ver_file.read_text(encoding="utf-8").strip() or "3.14"
        else:
            python_spec = "3.14"

    return python_spec, venv_dir


def warm_uv_wheel_cache(hermes_home: Path, dry_run: bool = False) -> list[str]:
    """Pre-warm uncached uv.lock wheels from Aliyun into cache/uv/wheels-v7/pypi/."""
    install_dir = hermes_home / "hermes-agent"
    pyproject = install_dir / "pyproject.toml"
    uv_lock = install_dir / "uv.lock"
    if not pyproject.exists() or not uv_lock.exists():
        return []

    uv_bin = resolve_uv_bin(hermes_home)
    cache_dir = hermes_home / "cache" / "uv"
    python_spec, venv_dir = _resolve_hermes_python_and_venv(hermes_home)

    dry_env = _clean_uv_env(hermes_home)
    if venv_dir is not None:
        dry_env["UV_PROJECT_ENVIRONMENT"] = str(venv_dir)

    dry_cmd = [
        uv_bin,
        "sync",
        "--frozen",
        "--dry-run",
        "-v",
        "--no-config",
        "--python",
        python_spec,
        "--cache-dir",
        str(cache_dir),
    ]
    try:
        dry_proc = subprocess.run(
            dry_cmd,
            cwd=install_dir,
            env=dry_env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return [f"uv dry-run failed: {exc}"]

    combined = f"{dry_proc.stdout}\n{dry_proc.stderr}".lower()
    needs_download = (
        "would download" in combined
        or "downloading" in combined
        or dry_proc.returncode != 0
        or venv_dir is None
    )
    if not needs_download:
        return ["uv wheel cache already warm (0 uncached wheels)"]

    if dry_run:
        return ["would pre-warm uncached uv.lock wheels from Aliyun mirror into wheels-v7/pypi"]

    warm_env = _clean_uv_env(hermes_home)
    warm_env.pop("UV_PROJECT_ENVIRONMENT", None)
    with tempfile.TemporaryDirectory(prefix="hermes-uv-warm-") as tmp:
        tmp_path = Path(tmp)
        shutil.copy2(pyproject, tmp_path / "pyproject.toml")
        rewritten = rewrite_uv_lock_for_mirror(uv_lock.read_text(encoding="utf-8"))
        (tmp_path / "uv.lock").write_text(rewritten, encoding="utf-8")

        warm_cmd = [
            uv_bin,
            "sync",
            "--frozen",
            "--no-install-project",
            "--no-build",
            "--no-config",
            "--python",
            python_spec,
            "--cache-dir",
            str(cache_dir),
        ]
        try:
            warm_proc = subprocess.run(
                warm_cmd,
                cwd=tmp_path,
                env=warm_env,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return [f"uv cache warm failed: {exc}"]
        if warm_proc.returncode != 0:
            err_tail = (warm_proc.stderr or warm_proc.stdout).strip().splitlines()[-3:]
            return [f"uv cache warm exited {warm_proc.returncode}: {' | '.join(err_tail)}"]
    return ["pre-warmed missing uv.lock wheels into wheels-v7/pypi via Aliyun mirror"]


def ensure_npmrc_mirror(
    hermes_home: Path,
    registry_url: str = NPMMIRROR_REGISTRY,
    dry_run: bool = False,
) -> list[str]:
    """Ensure <HERMES_HOME>/npmrc configures the fast npmmirror registry."""
    npmrc_path = hermes_home / "npmrc"
    target_line = f"registry={registry_url}"
    existing = npmrc_path.read_text(encoding="utf-8") if npmrc_path.exists() else ""
    lines = existing.splitlines()
    for idx, line in enumerate(lines):
        if re.match(r"^\s*registry\s*=", line):
            if line.strip() == target_line:
                return []
            lines[idx] = target_line
            break
    else:
        lines.append(target_line)

    if dry_run:
        return [f"would set {target_line} in {npmrc_path}"]
    npmrc_path.parent.mkdir(parents=True, exist_ok=True)
    npmrc_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return [f"configured {target_line} in {npmrc_path}"]


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _strip_yaml_comment(value: str) -> str:
    in_single = False
    in_double = False
    for idx, ch in enumerate(value):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            if idx == 0 or value[idx - 1].isspace():
                return value[:idx].strip()
    return value.strip()


def _yaml_scalar_value(line: str) -> str:
    _, raw = line.split(":", 1)
    cleaned = _strip_yaml_comment(raw)
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in ("'", '"'):
        return cleaned[1:-1]
    return cleaned


def _find_section_end(lines: list[str], start: int, parent_indent: int) -> int:
    idx = start
    while idx < len(lines):
        stripped = lines[idx].strip()
        if stripped and not stripped.startswith("#") and _line_indent(lines[idx]) <= parent_indent:
            break
        idx += 1
    return idx


def ensure_uvx_mcp_mirror(
    config_text: str,
    mirror_index: str = ALIYUN_PYPI_SIMPLE,
) -> tuple[str, list[str]]:
    """Inject UV_DEFAULT_INDEX into uvx-based mcp_servers blocks lacking it."""
    if not config_text:
        return config_text, []

    lines = config_text.splitlines()
    mcp_start = next(
        (i for i, line in enumerate(lines) if re.match(r"^mcp_servers\s*:", line)),
        None,
    )
    if mcp_start is None:
        return config_text, []

    mcp_end = _find_section_end(lines, mcp_start + 1, 0)
    changes: list[str] = []
    # Collect edits backwards or rebuild offset cleanly in forward pass
    edits: list[tuple[int, int, list[str]]] = []

    idx = mcp_start + 1
    server_indent: int | None = None
    while idx < mcp_end:
        line = lines[idx]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            idx += 1
            continue
        indent = _line_indent(line)
        if server_indent is None:
            server_indent = indent
        if indent != server_indent or ":" not in stripped:
            idx += 1
            continue

        server_name = stripped.split(":", 1)[0].strip()
        block_end = _find_section_end(lines, idx + 1, server_indent)
        block_lines = lines[idx + 1 : block_end]

        prop_indent: int | None = None
        command_line_idx: int | None = None
        command_val: str | None = None
        env_line_idx: int | None = None
        env_is_empty_braces = False
        env_end_idx: int | None = None
        has_uv_default_index = False

        for rel_i, b_line in enumerate(block_lines):
            b_strip = b_line.strip()
            if not b_strip or b_strip.startswith("#"):
                continue
            b_indent = _line_indent(b_line)
            if prop_indent is None:
                prop_indent = b_indent
            if b_indent == prop_indent and ":" in b_strip:
                key = b_strip.split(":", 1)[0].strip()
                if key == "command":
                    command_line_idx = idx + 1 + rel_i
                    command_val = _yaml_scalar_value(b_line)
                elif key == "env":
                    env_line_idx = idx + 1 + rel_i
                    env_val = _strip_yaml_comment(b_line.split(":", 1)[1])
                    env_is_empty_braces = env_val == "{}"
                    env_end_idx = _find_section_end(lines, env_line_idx + 1, b_indent)

        is_uvx = command_val == "uvx" or (command_val or "").endswith("/uvx")
        if is_uvx and prop_indent is not None:
            if env_line_idx is not None and env_end_idx is not None:
                for e_line in lines[env_line_idx + 1 : env_end_idx]:
                    e_strip = e_line.strip()
                    if e_strip and not e_strip.startswith("#") and e_strip.startswith("UV_DEFAULT_INDEX:"):
                        has_uv_default_index = True
                        break
                if not has_uv_default_index:
                    child_indent = " " * (prop_indent + 2)
                    for e_line in lines[env_line_idx + 1 : env_end_idx]:
                        if e_line.strip() and not e_line.strip().startswith("#"):
                            child_indent = " " * _line_indent(e_line)
                            break
                    if env_is_empty_braces:
                        edits.append(
                            (
                                env_line_idx,
                                env_line_idx + 1,
                                [
                                    f"{' ' * prop_indent}env:",
                                    f"{child_indent}UV_DEFAULT_INDEX: {mirror_index}",
                                ],
                            )
                        )
                    else:
                        edits.append(
                            (
                                env_line_idx + 1,
                                env_line_idx + 1,
                                [f"{child_indent}UV_DEFAULT_INDEX: {mirror_index}"],
                            )
                        )
                    changes.append(server_name)
            elif command_line_idx is not None:
                pad = " " * prop_indent
                edits.append(
                    (
                        command_line_idx + 1,
                        command_line_idx + 1,
                        [
                            f"{pad}env:",
                            f"{pad}  UV_DEFAULT_INDEX: {mirror_index}",
                        ],
                    )
                )
                changes.append(server_name)

        idx = block_end

    if not edits:
        return config_text, []

    updated_lines = list(lines)
    for start_i, end_i, replacement in reversed(edits):
        updated_lines[start_i:end_i] = replacement
    trailing_nl = "\n" if config_text.endswith("\n") else ""
    return "\n".join(updated_lines) + trailing_nl, changes


def apply_uvx_mcp_mirror(hermes_home: Path, dry_run: bool = False) -> list[str]:
    """Ensure uvx MCP servers in <HERMES_HOME>/config.yaml set UV_DEFAULT_INDEX."""
    config_path = hermes_home / "config.yaml"
    if not config_path.exists():
        return []
    original = config_path.read_text(encoding="utf-8")
    updated, servers = ensure_uvx_mcp_mirror(original)
    if not servers:
        return []
    if dry_run:
        return [f"would inject UV_DEFAULT_INDEX into uvx MCP server(s): {', '.join(servers)}"]
    config_path.write_text(updated, encoding="utf-8")
    return [f"injected UV_DEFAULT_INDEX into uvx MCP server(s): {', '.join(servers)}"]


def ensure_launchd_enabled(hermes_home: Path, dry_run: bool = False) -> list[str]:
    """Clear launchctl disabled flag and unsupported marker on macOS."""
    actions: list[str] = []
    if sys.platform != "darwin":
        return actions

    uid = os.getuid()
    if is_launchd_disabled(uid=uid):
        if dry_run:
            actions.append(f"would run launchctl enable gui/{uid}/{LAUNCHD_LABEL}")
        else:
            proc = subprocess.run(
                ["launchctl", "enable", f"gui/{uid}/{LAUNCHD_LABEL}"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if proc.returncode == 0:
                actions.append(f"enabled launchd service gui/{uid}/{LAUNCHD_LABEL}")
            else:
                actions.append(
                    f"launchctl enable exited {proc.returncode}: {proc.stderr.strip()}"
                )

    marker = hermes_home / ".gateway-launchd-unsupported"
    if marker.exists():
        if dry_run:
            actions.append(f"would remove {marker}")
        else:
            marker.unlink()
            actions.append(f"removed {marker}")
    return actions


def _tail_file(path: Path, max_lines: int = 80) -> list[str]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-max_lines:]
    except OSError:
        return []


def collect_diagnostics(
    hermes_home: Path,
    restart_result: dict[str, Any] | None = None,
    max_lines: int = 80,
) -> dict[str, Any]:
    """Collect log tails and state snapshots when deterministic repair fails."""
    logs_dir = hermes_home / "logs"
    log_tails: dict[str, list[str]] = {}
    for name in ("gateway.log", "gateway.error.log", "errors.log"):
        candidate = logs_dir / name
        if candidate.exists():
            log_tails[name] = _tail_file(candidate, max_lines=max_lines)

    state_path = find_state_file(hermes_home)
    return {
        "gateway_state": read_json_file(state_path) if state_path else None,
        "paused_gateway_files": sorted(
            p.name for p in hermes_home.glob(".hermes-update-paused-gateways*")
        ),
        "launchd_disabled": is_launchd_disabled(),
        "restart_result": restart_result,
        "log_tails": log_tails,
    }


def repair_gateway(
    hermes_home: str | Path | None = None,
    required_platforms: tuple[str, ...] = DEFAULT_REQUIRED_PLATFORMS,
    wait_timeout_s: int = 90,
    dry_run: bool = False,
    home_dir: Path | None = None,
    hermes_bin: str | None = None,
) -> dict[str, Any]:
    """Execute deterministic repair steps and wait for a healthy Hermes Gateway."""
    home = resolve_hermes_home(hermes_home)
    actions: list[str] = []

    actions.extend(kill_stuck_processes(home, dry_run=dry_run))
    actions.extend(sanitize_uv_index_config(home, home_dir=home_dir, dry_run=dry_run))
    actions.extend(warm_uv_wheel_cache(home, dry_run=dry_run))
    actions.extend(ensure_npmrc_mirror(home, dry_run=dry_run))
    actions.extend(apply_uvx_mcp_mirror(home, dry_run=dry_run))
    actions.extend(ensure_launchd_enabled(home, dry_run=dry_run))

    if dry_run:
        return {
            "status": "dry_run",
            "healthy": False,
            "hermes_home": str(home),
            "actions": actions,
        }

    cli_bin = resolve_hermes_bin(hermes_bin)
    env = _clean_uv_env(home)
    restart_info: dict[str, Any] = {}
    try:
        proc = subprocess.run(
            [cli_bin, "gateway", "restart"],
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        restart_info = {
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout.splitlines()[-25:],
            "stderr_tail": proc.stderr.splitlines()[-25:],
        }
        actions.append(f"ran '{cli_bin} gateway restart' (rc={proc.returncode})")
    except (OSError, subprocess.SubprocessError) as exc:
        restart_info = {"error": str(exc)}
        actions.append(f"'{cli_bin} gateway restart' failed: {exc}")

    deadline = time.monotonic() + max(0, wait_timeout_s)
    health = check_health(home, required_platforms=required_platforms)
    while not health["healthy"] and time.monotonic() < deadline:
        time.sleep(3.0)
        health = check_health(home, required_platforms=required_platforms)

    if health["healthy"]:
        return {
            "status": "repaired",
            "healthy": True,
            "hermes_home": str(home),
            "actions": actions,
            "health": health,
        }

    return {
        "status": "needs_agent",
        "healthy": False,
        "hermes_home": str(home),
        "actions": actions,
        "health": health,
        "diagnostics": collect_diagnostics(home, restart_result=restart_info),
    }


def append_repair_log(hermes_home: Path, message: str) -> None:
    """Append a single timestamped line to <HERMES_HOME>/logs/hermes-gateway-repair.log."""
    logs_dir = hermes_home / "logs"
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / "hermes-gateway-repair.log"
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with log_file.open("a", encoding="utf-8") as fh:
            fh.write(f"[{ts}] {message}\n")
    except OSError:
        pass


def run_orca_precheck(
    hermes_home: str | Path | None = None,
    required_platforms: tuple[str, ...] = DEFAULT_REQUIRED_PLATFORMS,
    wait_timeout_s: int = 90,
    dry_run: bool = False,
) -> tuple[int, dict[str, Any]]:
    """Run Orca precheck: return exit 1 to skip LLM when healthy/repaired, 0 when needs_agent."""
    home = resolve_hermes_home(hermes_home)
    health = check_health(home, required_platforms=required_platforms)
    if health["healthy"]:
        append_repair_log(home, "precheck=healthy action=skip_llm")
        return 1, {"status": "healthy", "healthy": True, "health": health, "actions": []}

    result = repair_gateway(
        home,
        required_platforms=required_platforms,
        wait_timeout_s=wait_timeout_s,
        dry_run=dry_run,
    )
    if result["status"] == "repaired":
        summary = "; ".join(result.get("actions", []))
        append_repair_log(home, f"precheck=repaired action=skip_llm details={summary}")
        return 1, result

    issues = "; ".join(result.get("health", {}).get("issues", []))
    append_repair_log(home, f"precheck=needs_agent action=wake_llm issues={issues}")
    return 0, result


def _format_human(payload: dict[str, Any]) -> str:
    if "status" in payload:
        lines = [f"status={payload['status']} healthy={payload.get('healthy')}"]
        for act in payload.get("actions", []):
            lines.append(f"  - {act}")
        issues = payload.get("health", {}).get("issues", [])
        for issue in issues:
            lines.append(f"  ! {issue}")
        return "\n".join(lines)

    lines = [
        f"healthy={payload['healthy']} pid={payload.get('pid')} "
        f"state={payload.get('gateway_state')}"
    ]
    for issue in payload.get("issues", []):
        lines.append(f"  ! {issue}")
    for warn in payload.get("warnings", []):
        lines.append(f"  ~ {warn}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check and deterministically repair Hermes Gateway."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Read-only health check")
    mode.add_argument(
        "--repair",
        action="store_true",
        help="Check and apply deterministic repairs if unhealthy (or with --force)",
    )
    mode.add_argument(
        "--orca-precheck",
        action="store_true",
        help="Orca precheck mode: exit 1 when healthy/repaired, exit 0 only when needs_agent",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument("--force", action="store_true", help="Run repair even if healthy")
    parser.add_argument("--dry-run", action="store_true", help="Preview repair actions")
    parser.add_argument("--hermes-home", type=Path, default=None, help="Override HERMES_HOME")
    parser.add_argument(
        "--platform",
        action="append",
        dest="platforms",
        help="Required connected platform (repeatable; defaults to telegram)",
    )
    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=90,
        help="Seconds to wait for gateway health after restart (default: 90)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    required_platforms = tuple(args.platforms) if args.platforms else DEFAULT_REQUIRED_PLATFORMS
    home = resolve_hermes_home(args.hermes_home)

    if args.orca_precheck:
        exit_code, payload = run_orca_precheck(
            home,
            required_platforms=required_platforms,
            wait_timeout_s=args.wait_timeout,
            dry_run=args.dry_run,
        )
        # Emit JSON automatically when waking the Orca agent or when --json is set
        if args.json or exit_code == 0:
            print(json.dumps(payload, indent=2))
        else:
            print(_format_human(payload))
        return exit_code

    if args.repair:
        health = check_health(home, required_platforms=required_platforms)
        if health["healthy"] and not args.force and not args.dry_run:
            payload: dict[str, Any] = {
                "status": "healthy",
                "healthy": True,
                "hermes_home": str(home),
                "actions": [],
                "health": health,
            }
            exit_code = 0
        else:
            payload = repair_gateway(
                home,
                required_platforms=required_platforms,
                wait_timeout_s=args.wait_timeout,
                dry_run=args.dry_run,
            )
            exit_code = 0 if payload["status"] in ("repaired", "dry_run") else 2
        print(json.dumps(payload, indent=2) if args.json else _format_human(payload))
        return exit_code

    # Default to --check
    health = check_health(home, required_platforms=required_platforms)
    print(json.dumps(health, indent=2) if args.json else _format_human(health))
    return 0 if health["healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
