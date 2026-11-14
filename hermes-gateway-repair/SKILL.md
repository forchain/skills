---
name: hermes-gateway-repair
description: "Repair unresponsive or failing Hermes Agent gateways (Telegram/Feishu/Weixin), hung updates, uv/npm mirror stalls, and launchd errors. Use when Hermes stops replying, hangs during hermes update or hermes gateway restart, needs a watchdog check, or uncovers a new startup failure requiring script-first repair and self-upgrade via PR."
summary: "Script-first watchdog, repair tool, and self-upgrading workflow for Hermes Agent gateway startup, mirror, and launchd failures."
---

# Hermes Gateway Repair

Recover failing Hermes Agent gateways deterministically before spending LLM tokens, and codify every newly encountered failure mode back into this skill.

## Workflow

### Step 1: Run the repair script first

Run the deterministic repair script before inspecting logs or editing config by hand:

```bash
python3 ~/.agents/skills/hermes-gateway-repair/scripts/hermes_gateway_repair.py --repair --json
```

Read the exit code:
- **Exit `0` (`healthy` or `repaired`)**: `gateway_state.json` reports `"gateway_state": "running"`, the PID in `gateway.pid` is alive, all configured platforms (including `telegram`) report `"state": "connected"`, and no stuck update/`uv sync` process exceeds 300s. Stop here.
- **Exit `2` (`needs_agent`)**: Deterministic repair failed after restarting and waiting up to 90s. Proceed to Step 2 with the emitted `diagnostics` JSON payload.

### Step 2: Diagnose and fix novel failures

When `--repair --json` exits `2`:
1. Inspect `diagnostics.log_tails` (`gateway.log`, `gateway.error.log`, `errors.log`), `diagnostics.gateway_state`, `diagnostics.paused_gateway_files`, `diagnostics.launchd_disabled`, and `diagnostics.restart_result`.
2. Inspect live sockets and child processes if a boot step hangs (`lsof -nP -p <pid>`, `ps -ef | grep -E "hermes|uv"`).
3. Fix the live issue (config, environment, supervisor state, or workaround) and restart via `hermes gateway restart`.

**Completion criterion:** `python3 ~/.agents/skills/hermes-gateway-repair/scripts/hermes_gateway_repair.py --check --json` returns `"healthy": true` and exits `0`.

### Step 3: Self-upgrade this skill and submit a PR

Whenever Step 2 fixed a failure mode that `hermes_gateway_repair.py` did not handle automatically, codify the new knowledge so future runs spend zero LLM tokens:

1. Locate the `forchain/skills` repo (current worktree or `/Volumes/Data/github.com/forchain/skills`).
2. Add a pure detector and deterministic fixer for the new root cause to [hermes_gateway_repair.py](scripts/hermes_gateway_repair.py) and wire it into `repair_gateway()`.
3. Add unit tests covering the detector and fixer in [test_hermes_gateway_repair.py](tests/test_hermes_gateway_repair.py).
4. Document the new failure mode in the reference table below.
5. Validate, test, and sync to the canonical skill hub:
   ```bash
   python3 scripts/validate_skills.py --sync
   python3 scripts/validate_skills.py
   pytest tests/test_validate_skills.py hermes-gateway-repair/tests/test_hermes_gateway_repair.py
   rm -rf ~/.agents/skills/hermes-gateway-repair
   cp -R hermes-gateway-repair ~/.agents/skills/hermes-gateway-repair
   ```
6. Check `git config remote.origin.url` to align Git author and `gh` identity (`forchain`), switch to a descriptive branch `forchain/hermes-gateway-repair-<issue-slug>`, commit, push, and open a PR with `gh pr create`.

**Completion criterion:** `validate_skills.py` exits `0`, `pytest` passes, the updated skill is synced to `~/.agents/skills/hermes-gateway-repair`, and the PR URL is reported.

## Known failure modes (script-handled)

| # | Symptom | Non-obvious trap | Deterministic script fix |
| --- | --- | --- | --- |
| 1 | Interrupted `hermes update` & gateway deadlock | Interrupted updates leave `.hermes-update-paused-gateways*.json` and hung `uv sync` holding cache locks; `_deps_hold_resume()` refuses to reload the gateway until `uv sync` succeeds. | Kill `uv sync --frozen` / `hermes update` / `hermes gateway restart` processes running >300s (`SIGTERM` -> `SIGKILL`). |
| 2 | `files.pythonhosted.org` IPv6 stall & `uv` cache-key poison | `uv.lock` hardcodes `https://files.pythonhosted.org/packages/` which stalls on Fastly IPv6. Setting `UV_INDEX_URL` or `~/.pip/pip.conf` (`index-url`) switches `uv`'s cache namespace from `wheels-v7/pypi/` to `wheels-v7/index/<hash>/`, invalidating 100+ cached wheels while still hitting `files.pythonhosted.org`. | Remove `UV_INDEX_URL` from `.env` and move active `pip.conf` (`index-url`) to `*.bak-hermes`; rewrite locked URLs in a temp `/tmp/hermes-uv-warm-*` `uv.lock` copy to `https://mirrors.aliyun.com/pypi/packages/` (keeping `registry = "https://pypi.org/simple"`) and run `uv sync --frozen --no-install-project --no-build --no-config --cache-dir ~/.hermes/cache/uv`. |
| 3 | `source_completion.py` Web UI `npm` hang | After `uv sync` finishes, `source_completion.py` installs/builds Node assets reading `NPM_CONFIG_USERCONFIG=~/.hermes/npmrc`, stalling on `registry.npmjs.org`. | Ensure `~/.hermes/npmrc` sets `registry=https://registry.npmmirror.com/`. |
| 4 | `uvx` MCP server blocks gateway boot for 120s | Before connecting to Telegram/Feishu, gateway starts every `mcp_servers:` entry in `config.yaml`. Any server with `command: uvx` stalls up to `connect_timeout: 120` querying IPv6 `pypi.org`. | Inject `UV_DEFAULT_INDEX: https://mirrors.aliyun.com/pypi/simple/` into every `command: uvx` server `env:` block in `config.yaml`. |
| 5 | macOS `launchd` `Bootstrap failed: 5: Input/output error` | When `launchctl print-disabled gui/<uid>` marks `"ai.hermes.gateway" => disabled`, `launchctl bootstrap` fails EIO 5 and falls back to an unsupervised detached process, writing `.gateway-launchd-unsupported`. | Run `launchctl enable gui/<uid>/ai.hermes.gateway` and remove `~/.hermes/.gateway-launchd-unsupported` before `hermes gateway restart`. |

## Orca automated watchdog (`--orca-precheck`)

Use `--orca-precheck` for scheduled Orca automations (`orca automations create --precheck ...`):
- Orca skips the LLM run on non-zero exit (`skipped_precheck`) and wakes the LLM only on exit `0`.
- `--orca-precheck` logs to `~/.hermes/logs/hermes-gateway-repair.log` and **exits `1`** (0 LLM tokens) when the gateway is already healthy **or** repaired purely by the script.
- `--orca-precheck` **exits `0`** and prints diagnostics JSON only on `needs_agent`, waking the agent to execute Steps 2–3.
