# Single-node MongoDB replica set for oplog-dependent apps

Rocket.Chat ≥6 requires MongoDB with an oplog: `MONGO_OPLOG_URL` only exists against a replica set. One member satisfies it. This shape booted clean on a 1 vCPU / 2GB box.

## Compose template

Pair the MongoDB major with the app's support matrix (Rocket.Chat 8.x ↔ MongoDB 8.x). Rocket.Chat image: `registry.rocket.chat/rocketchat/rocket.chat`, pin the release tag; upgrades are a deliberate tag change.

```yaml
services:
  mongodb:
    image: docker.io/mongo:8.2
    restart: unless-stopped
    command: --replSet rs0 --oplogSize 128 --wiredTigerCacheSizeGB 0.5
    volumes:
      - db_data:/data/db
    networks: [rocketchat]
    healthcheck:
      test: ["CMD-SHELL", "mongosh --quiet --eval \"db.adminCommand('ping').ok\" > /dev/null || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 12
      start_period: 20s

  mongodb-init:
    image: docker.io/mongo:8.2
    restart: "no"
    depends_on:
      mongodb:
        condition: service_healthy
    networks: [rocketchat]
    entrypoint:
      - /bin/sh
      - -c
      - "mongosh --host mongodb:27017 --quiet --eval 'try { rs.status().ok } catch (e) { rs.initiate({_id:\"rs0\",members:[{_id:0,host:\"mongodb:27017\"}]}).ok }'"

  rocketchat:
    image: registry.rocket.chat/rocketchat/rocket.chat:8.9.0
    restart: unless-stopped
    env_file: [.env]
    ports: ["127.0.0.1:3000:3000"]
    volumes:
      - rc_data:/app/uploads
    networks: [rocketchat]
    depends_on:
      mongodb:
        condition: service_healthy
      mongodb-init:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "node", "-e", "fetch('http://127.0.0.1:3000/').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"]
      interval: 30s
      timeout: 15s
      retries: 5
      start_period: 90s

networks:
  rocketchat:
    driver: bridge

volumes:
  db_data:
  rc_data:
```

## .env

```
ROOT_URL=https://chat.example.com
PORT=3000
MONGO_URL=mongodb://mongodb:27017/rocketchat?replicaSet=rs0
MONGO_OPLOG_URL=mongodb://mongodb:27017/local?replicaSet=rs0
DEPLOY_METHOD=docker
NODE_OPTIONS=--max-old-space-size=1024
```

## Design notes

- **Ping gate, not rs.status**: making the mongodb healthcheck run `rs.status()` deadlocks the stack — the gate demands the replica set that only the init container creates. `db.adminCommand('ping')` says "mongod answers" and nothing more.
- **Replica host by service name**: `host:"mongodb:27017"` resolves through the compose network's DNS on every container restart, so the set re-elects after reboot without a stale IP baked into config.
- **No auth, no published mongo port**: the compose network stays unreachable from outside the host while mongo has zero exposed surface; the only ingress is `127.0.0.1:3000` behind Caddy.
- **`service_completed_successfully`** chains first-boot migrations onto a writable primary, avoiding the `notPrimary` restart loop.
- **First boot is migration-heavy**: minutes of `starting` on a 1 vCPU box is normal; read `docker logs rocketchat` for progress markers (`SERVER RUNNING`) before touching timeouts.
