---
name: caddy-cloudflare-deploy
description: "Deploy an app on a remote VPS reached through an SSH jump host and serve it from a Cloudflare-proxied domain on the server's existing Caddy: preflight the box, land a docker-compose stack bound to localhost, add a Caddy site drop-in, let HTTP-01 issue Let's Encrypt through the proxy, and prove the result with a verification ladder. Use when adding a new domain or app to a server that already runs Caddy, when the target is only reachable via a bastion, or when an origin behind Cloudflare needs working HTTPS and WebSockets."
summary: "Deploy a dockerized app behind an existing Caddy + Cloudflare on a jump-host VPS, with staged end-to-end verification."
---

# Caddy + Cloudflare VPS Deploy

## Overview

Scope: a target that already runs Caddy with automatic TLS under a managed config (the 233boy layout is the reference case), a domain on Cloudflare with proxy status on, and an agent driving everything through one bastion hop. The skill's payload is the traps that break each stage and the ladder that proves each stage actually passed.

## Workflow

1. **Preflight the target** (read-only)
   - Bastion route: nested `ssh <jump> "ssh <target> '<cmd>'"`. `-J` requires the target host key in the local `known_hosts` as well; a fresh workstation answers `Host key verification failed`. Nested ssh reuses the key the jump host already trusts.
   - Command transport: ship scripts as files — `ssh <jump> "ssh <target> 'bash -s'" < local.sh`, and land files with `cat f | ssh <jump> "ssh <target> 'cat > /path'"`. Each added quote level invites silent argv mangling; patches go over as files, inline heredocs go over broken.
   - Facts to collect: RAM/swap/disk/CPU; docker presence; `/etc/caddy` layout — which directories the main config imports, whether global `admin off` is set; `dig +short <domain>` answering Cloudflare anycast (104.21.x / 172.67.x) proves the record exists and is proxied.
   - Done when: one round-trip command executes and the Caddy import directory plus admin-API state are known facts.

2. **Lock the Cloudflare preconditions**: A record targets the server IP, proxy status on, SSL mode Full (strict). Verify with the read-only API walkthrough in `references/cloudflare-checks.md`, or take a stated panel reading from the user. Full (strict) is the mode under which origin TLS and WebSockets work.
   - Done when: the record target and the `ssl: strict` value are each backed by a visible artifact.

3. **Prepare the box**: a ≤2GB-RAM host with no swap gets a 2G swapfile before the stack lands: `fallocate -l 2G /swapfile` (dd fallback), `chmod 600`, `mkswap`, `swapon`, an `/etc/fstab` line, `vm.swappiness=10` in a `/etc/sysctl.d/` file. Runtimes come from distro packages first (`apt-get install docker.io docker-compose-v2`) — no external repo needed on Ubuntu 24.04.
   - Done when: `swapon --show` lists the swapfile and `docker compose version` exits 0.

4. **Land the app stack** in `/opt/<app>/`, published as `127.0.0.1:<port>:<port>` only. Three traps decide first-boot reliability:
   - **Exec-form + string command**: `entrypoint: ["/bin/sh", "-c"]` with `command:` as a string passes the command's words on as positional parameters, so `sh -c` executes only the first word and every flag after it vanishes. Carry the full script as the third element of the entrypoint list.
   - **Healthcheck probes with tools the image ships**: read `.State.Health.Log` before accepting red as truth — the Rocket.Chat 8 image contains no curl, and a curl healthcheck reports `unhealthy` while the app's own log prints `SERVER RUNNING`. Prefer a check built on the image's runtime: `node -e "fetch(...)"`.
   - **Oplog-dependent apps (Rocket.Chat ≥6) need a replica-set MongoDB**: use the tested template in `references/compose-recipes.md`.
   - Done when: `curl -sI http://127.0.0.1:<port>/` on the target returns the app's own status line.

5. **Wire the domain into Caddy**: one new file in the import directory, holding exactly one site block:
   ```
   <domain> {
       reverse_proxy 127.0.0.1:<port>
   }
   ```
   The managed main config stays untouched. Validate with `caddy validate --config /etc/caddy/Caddyfile`, then apply. Under global `admin off`, `systemctl reload caddy` dies with `Post "http://localhost:2019/load": ... connection refused`: the admin API is the reload channel and it is disabled by design, so `systemctl restart caddy` is the apply path (≈1-second blip for fronted services). TLS-ALPN dies at the proxy; Caddy falls back to HTTP-01 by itself because the Cloudflare edge passes `/.well-known/acme-challenge` through to the origin.
   - Done when: the journal carries `certificate obtained successfully` for the new identifier.

6. **Prove it on the ladder**, each rung carrying its own artifact into the final report:
   1. origin-local HTTP status;
   2. the certificate-obtained journal line;
   3. external `https://<domain>/` returning 200 plus one data endpoint (e.g. `/api/info` with the app version), and `http://` answering 308;
   4. a WebSocket handshake from a real client — a curl `Connection: Upgrade` probe answers 400 while the socket works fine. For a Node-based app: `docker cp` a twenty-line script into the container (host `/tmp` is invisible to it), run the global `WebSocket` client, and accept `{"msg":"error","reason":"Must connect first"}` as proof of open-plus-message round-trip.
   - Done when: every rung's artifact is quoted in the report.

## References

- `references/cloudflare-checks.md` — Cloudflare token taxonomy, the read-only preflight endpoints, permission-error meanings.
- `references/compose-recipes.md` — single-node MongoDB replica set with init container, the tested shape for oplog-dependent chat apps.
