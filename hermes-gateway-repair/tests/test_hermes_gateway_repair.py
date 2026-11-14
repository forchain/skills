from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from unittest import mock

import pytest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import hermes_gateway_repair as hgr  # noqa: E402


def _write_state(
    home: Path,
    *,
    pid: int | str,
    gateway_state: str = "running",
    telegram_state: str = "connected",
    error_code: str | None = None,
    json_pid_file: bool = True,
) -> None:
    if json_pid_file:
        (home / "gateway.pid").write_text(json.dumps({"pid": pid}), encoding="utf-8")
    else:
        (home / "gateway.pid").write_text(str(pid), encoding="utf-8")
    state = {
        "pid": pid,
        "gateway_state": gateway_state,
        "platforms": {
            "telegram": {
                "state": telegram_state,
                "error_code": error_code,
            }
        },
    }
    (home / "gateway_state.json").write_text(json.dumps(state), encoding="utf-8")


def test_check_health_returns_true_when_pid_and_telegram_connected(tmp_path: Path) -> None:
    _write_state(tmp_path, pid=os.getpid(), gateway_state="running", telegram_state="connected")
    with (
        mock.patch.object(hgr, "find_stuck_processes", return_value=[]),
        mock.patch.object(hgr, "is_launchd_disabled", return_value=False),
    ):
        health = hgr.check_health(tmp_path)

    assert health["healthy"] is True
    assert health["issues"] == []
    assert health["pid"] == os.getpid()
    assert health["gateway_state"] == "running"


def test_check_health_detects_dead_pid_bad_state_and_disconnected_platform(
    tmp_path: Path,
) -> None:
    _write_state(
        tmp_path,
        pid=999999,
        gateway_state="starting",
        telegram_state="retrying",
        error_code="ETIMEDOUT",
        json_pid_file=False,
    )
    with (
        mock.patch.object(hgr, "is_pid_alive", return_value=False),
        mock.patch.object(hgr, "find_stuck_processes", return_value=[]),
        mock.patch.object(hgr, "is_launchd_disabled", return_value=False),
    ):
        health = hgr.check_health(tmp_path)

    assert health["healthy"] is False
    joined = "\n".join(health["issues"])
    assert "not running" in joined
    assert "gateway_state is 'starting'" in joined
    assert "telegram" in joined
    assert "ETIMEDOUT" in joined


def test_rewrite_uv_lock_for_mirror_keeps_registry_and_hashes() -> None:
    sample_lock = """\
version = 1
requires-python = ">=3.11"

[[package]]
name = "nemo-relay"
version = "0.10.0"
source = { registry = "https://pypi.org/simple" }
wheels = [
    { url = "https://files.pythonhosted.org/packages/aa/bb/nemo_relay-0.10.0-py3-none-any.whl", hash = "sha256:deadbeef" },
]
"""
    rewritten = hgr.rewrite_uv_lock_for_mirror(sample_lock)

    assert 'source = { registry = "https://pypi.org/simple" }' in rewritten
    assert 'hash = "sha256:deadbeef"' in rewritten
    assert (
        'url = "https://mirrors.aliyun.com/pypi/packages/aa/bb/nemo_relay-0.10.0-py3-none-any.whl"'
        in rewritten
    )
    assert "files.pythonhosted.org" not in rewritten


def test_sanitize_uv_index_config_removes_pip_conf_and_uv_index_url(tmp_path: Path) -> None:
    fake_home = tmp_path / "userhome"
    hermes_home = tmp_path / "hermes"
    (fake_home / ".pip").mkdir(parents=True)
    hermes_home.mkdir(parents=True)

    pip_conf = fake_home / ".pip" / "pip.conf"
    pip_conf.write_text("[global]\nindex-url = https://mirrors.aliyun.com/pypi/simple/\n", encoding="utf-8")

    env_file = hermes_home / ".env"
    env_file.write_text(
        "OPENAI_API_KEY=keep\nUV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/\nFOO=bar\n",
        encoding="utf-8",
    )

    actions = hgr.sanitize_uv_index_config(hermes_home, home_dir=fake_home)

    assert not pip_conf.exists()
    assert (fake_home / ".pip" / "pip.conf.bak-hermes").exists()
    updated_env = env_file.read_text(encoding="utf-8")
    assert "UV_INDEX_URL=" not in updated_env
    assert "OPENAI_API_KEY=keep" in updated_env
    assert "FOO=bar" in updated_env
    assert "UV_HTTP_TIMEOUT=60" in updated_env
    assert any("pip.conf" in a for a in actions)
    assert any("UV_INDEX_URL" in a for a in actions)


def test_ensure_uvx_mcp_mirror_injects_and_is_idempotent() -> None:
    sample_cfg = """\
model: gpt-5
mcp_servers:
  claude-mem:
    command: "/usr/local/bin/node"
    enabled: true
  minimax:
    command: uvx
    args:
      - --with
      - fastmcp
      - minimax-coding-plan-mcp
    env:
      MINIMAX_API_KEY: secret
    timeout: 300
  bare_uvx:
    command: "uvx"
    timeout: 60
  empty_env_uvx:
    command: uvx
    env: {}
"""
    updated, changed = hgr.ensure_uvx_mcp_mirror(sample_cfg)

    assert changed == ["minimax", "bare_uvx", "empty_env_uvx"]
    assert "claude-mem" not in changed
    assert updated.count("UV_DEFAULT_INDEX: https://mirrors.aliyun.com/pypi/simple/") == 3
    assert "      MINIMAX_API_KEY: secret" in updated

    # Running a second time must be a complete no-op
    updated_again, changed_again = hgr.ensure_uvx_mcp_mirror(updated)
    assert changed_again == []
    assert updated_again == updated


@pytest.mark.parametrize(
    ("healthy_first", "repair_status", "expected_exit"),
    [
        (True, None, 1),
        (False, "repaired", 1),
        (False, "needs_agent", 0),
    ],
)
def test_orca_precheck_exit_code_contract(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    healthy_first: bool,
    repair_status: str | None,
    expected_exit: int,
) -> None:
    (tmp_path / "logs").mkdir(parents=True)
    health_payload = {
        "healthy": healthy_first,
        "pid": 123,
        "gateway_state": "running" if healthy_first else "stopped",
        "issues": [] if healthy_first else ["gateway_state is 'stopped'"],
        "warnings": [],
    }
    repair_payload = (
        {
            "status": repair_status,
            "healthy": repair_status == "repaired",
            "actions": ["restarted gateway"],
            "health": health_payload,
        }
        if repair_status
        else None
    )

    with (
        mock.patch.object(hgr, "check_health", return_value=health_payload),
        mock.patch.object(hgr, "repair_gateway", return_value=repair_payload) as mock_repair,
    ):
        rc = hgr.main(["--orca-precheck", "--hermes-home", str(tmp_path)])

    assert rc == expected_exit
    if healthy_first:
        mock_repair.assert_not_called()
    else:
        mock_repair.assert_called_once()

    log_text = (tmp_path / "logs" / "hermes-gateway-repair.log").read_text(encoding="utf-8")
    assert len(log_text.strip().splitlines()) == 1
    if expected_exit == 0:
        out = json.loads(capsys.readouterr().out)
        assert out["status"] == "needs_agent"


def test_parse_ps_etime() -> None:
    assert hgr.parse_ps_etime("04:59") == 299
    assert hgr.parse_ps_etime("01:02:03") == 3723
    assert hgr.parse_ps_etime("2-00:01:00") == 172860


def test_repair_gateway_returns_needs_agent_with_diagnostics_when_still_unhealthy(
    tmp_path: Path,
) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True)
    (logs_dir / "gateway.log").write_text("line1\nbootstrap failed\n", encoding="utf-8")
    (logs_dir / "errors.log").write_text("fatal error\n", encoding="utf-8")
    (tmp_path / ".env").write_text("FOO=bar\n", encoding="utf-8")
    (tmp_path / "config.yaml").write_text("mcp_servers:\n  minimax:\n    command: uvx\n", encoding="utf-8")
    _write_state(tmp_path, pid=1234, gateway_state="stopped", telegram_state="disconnected")

    unhealthy = {
        "healthy": False,
        "hermes_home": str(tmp_path),
        "pid": 1234,
        "gateway_state": "stopped",
        "issues": ["gateway_state is 'stopped'"],
        "warnings": [],
    }
    fake_proc = mock.MagicMock(returncode=1, stdout="out", stderr="err")
    with (
        mock.patch.object(hgr, "find_stuck_processes", return_value=[]),
        mock.patch.object(hgr, "is_launchd_disabled", return_value=False),
        mock.patch.object(hgr, "check_health", return_value=unhealthy),
        mock.patch("subprocess.run", return_value=fake_proc),
    ):
        result = hgr.repair_gateway(
            tmp_path, wait_timeout_s=0, home_dir=tmp_path / "userhome", hermes_bin="hermes"
        )

    assert result["status"] == "needs_agent"
    assert result["healthy"] is False
    assert (tmp_path / "npmrc").read_text(encoding="utf-8").strip() == f"registry={hgr.NPMMIRROR_REGISTRY}"
    assert "UV_DEFAULT_INDEX" in (tmp_path / "config.yaml").read_text(encoding="utf-8")
    assert result["diagnostics"]["log_tails"]["gateway.log"] == ["line1", "bootstrap failed"]
    assert result["diagnostics"]["log_tails"]["errors.log"] == ["fatal error"]


def test_repair_gateway_returns_repaired_when_restart_recovers(tmp_path: Path) -> None:
    (tmp_path / "logs").mkdir(parents=True)
    healthy = {
        "healthy": True,
        "hermes_home": str(tmp_path),
        "pid": os.getpid(),
        "gateway_state": "running",
        "issues": [],
        "warnings": [],
    }
    fake_proc = mock.MagicMock(returncode=0, stdout="restarted", stderr="")
    with (
        mock.patch.object(hgr, "find_stuck_processes", return_value=[]),
        mock.patch.object(hgr, "is_launchd_disabled", return_value=False),
        mock.patch.object(hgr, "check_health", return_value=healthy),
        mock.patch("subprocess.run", return_value=fake_proc),
    ):
        result = hgr.repair_gateway(
            tmp_path, wait_timeout_s=0, home_dir=tmp_path / "userhome", hermes_bin="hermes"
        )

    assert result["status"] == "repaired"
    assert result["healthy"] is True
    assert "diagnostics" not in result
