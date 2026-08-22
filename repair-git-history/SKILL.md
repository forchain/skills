---
name: repair-git-history
description: "Repair Git history across repositories. Use for incorrect commit identities, non-English commit messages, evidence-backed tags or Releases, wrong GitHub accounts, and repository professionalism audits."
summary: "Audit and safely repair Git identities, messages, tags, and release history."
---

# Repair Git History

Use one Repair Plan through four gates: Audit, Apply, Verify, and Publish. A gate is complete only when its criterion is met.

## Audit

1. Run:
   ```bash
   python3 <skill-dir>/scripts/git_history_repair.py audit --repo . > /tmp/git-history-audit.json
   ```
2. Read [references/repair-policy.md](references/repair-policy.md), then create a Repair Plan outside the target repository. Each identity mapping is an exact `(name, email)` pair; each message mapping is a complete replacement keyed by old SHA. Preserve identifiers, trailers, and issue references.
3. When versions, tags, Releases, or public presentation matter, read [references/professional-audit.md](references/professional-audit.md) and collect evidence before proposing action.

Completion criterion: the user has reviewed the Repair Plan, including its ref boundary and every proposed public mutation.

## Apply

1. Compute the reviewed plan's digest:
   ```bash
   python3 -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("/tmp/repair-plan.json").read_bytes()).hexdigest())'
   ```
2. Run Apply into a new mirror:
   ```bash
   python3 <skill-dir>/scripts/git_history_repair.py apply \
     --repo . --plan /tmp/repair-plan.json --approval <digest> \
     --output /tmp/rewritten-repository.git
   ```
Completion criterion: the mirror and its `before-rewrite.bundle` exist; the source repository is unchanged.

## Verify

Run:
```bash
python3 <skill-dir>/scripts/git_history_repair.py verify \
  --source . --mirror /tmp/rewritten-repository.git --plan /tmp/repair-plan.json
```

Run the target repository's documented tests from a temporary worktree when available.

Completion criterion: `verify` accepts the complete commit map, unchanged trees, parent topology, dates, approved identities, and approved messages.

## Publish

1. Obtain a second explicit approval after Verify.
2. Derive a login hint only from an explicit `remote.origin.url` username. Before every GitHub mutation, verify it with `gh auth status`, switch with `gh auth switch -h github.com -u <login>`, and restore the prior account afterwards. Treat GitHub login and commit identity as separate values.
3. Snapshot Releases. Push each approved ref using the exact old OID in `repair-result.json` with `--force-with-lease`; create a missing Release only after its annotated tag exists, using `gh release create --verify-tag`.
4. Recheck remote refs, tags, Releases, and the active GitHub account. Set local `user.name`, `user.email`, and `user.useConfigOnly=true` to the canonical identity.

Completion criterion: every approved remote mutation is visible, and collaborators have the old-to-new SHA map.
