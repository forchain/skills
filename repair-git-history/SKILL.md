---
name: repair-git-history
description: "Audit and safely repair Git and GitHub history across repositories. Use when correcting commit author or committer identities, translating non-English commit messages, rebuilding evidence-backed versions/tags/Releases, preventing use of the wrong GitHub account, or auditing repository professionalism."
---

# Repair Git History

Repair history through Audit, approved Apply, Verify, and separately approved Publish. Never combine these stages.

## Audit

1. Run the deterministic audit without changing the repository:
   ```bash
   python3 <skill-dir>/scripts/git_history_repair.py audit --repo . > /tmp/git-history-audit.json
   ```
2. Read `/tmp/git-history-audit.json`. Treat each `(name, email)` pair as a distinct identity.
3. Read [references/repair-policy.md](references/repair-policy.md) before preparing a Repair Plan.
4. Read [references/professional-audit.md](references/professional-audit.md) when the user asks how to improve the repository's public presentation.
5. Propose, but do not apply, exact identity mappings and one full replacement message per approved old commit SHA. Translate natural language only; preserve code identifiers, paths, trailers, issue references, and Markdown structure.
6. Recover version, tag, and Release history only from evidence. When evidence is insufficient, propose a current baseline release instead of inventing historical releases.

## Identity And Account Rules

- Derive a GitHub login hint only from an explicit username in `remote.origin.url`.
- Distinguish the GitHub login used by `gh` from the name and email stored in commits.
- Use only explicit `(name, email)` mappings. Do not rewrite every non-target identity, match names alone, or change bots, external contributors, or `GitHub <noreply@github.com>` platform committers.
- For GitHub mutations, verify the intended account is authenticated with `gh auth status`, switch with `gh auth switch -h github.com -u <login>` when needed, and restore the prior account afterwards. Stop if the intended account is unavailable.
- After a successful Publish, set the current clone's local `user.name`, `user.email`, and `user.useConfigOnly=true` to the confirmed canonical identity.

## Apply

1. Create a reviewed plan JSON outside the repository. Use the schema in [references/repair-policy.md](references/repair-policy.md).
2. Compute its approval digest:
   ```bash
   python3 -c 'from pathlib import Path; import hashlib; print(hashlib.sha256(Path("/tmp/repair-plan.json").read_bytes()).hexdigest())'
   ```
3. Require a clean worktree and install `git-filter-repo`. Do not substitute `git filter-branch`.
4. Run Apply into a new path, never the source repository:
   ```bash
   python3 <skill-dir>/scripts/git_history_repair.py apply \
     --repo . --plan /tmp/repair-plan.json --approval <digest> \
     --output /tmp/rewritten-repository.git
   ```
5. Apply creates a bare mirror and `before-rewrite.bundle` before rewriting. Keep both until Publish is accepted and collaborators have migrated.

## Verify

Run:
```bash
python3 <skill-dir>/scripts/git_history_repair.py verify \
  --source . --mirror /tmp/rewritten-repository.git --plan /tmp/repair-plan.json
```

Require `git fsck --strict`, a complete commit map, and matching old/new tree IDs. Run the target repository's tests from a temporary worktree at the rewritten default branch when the repository provides a documented test command.

## Publish

Do not publish without a second explicit approval after Verify.

1. Snapshot Releases with read-only `gh api --method GET repos/<owner>/<repo>/releases`.
2. Stop on unexpected remote movement, protected refs, missing permissions, or unresolved open PR/fork migration risk. Never relax branch rules automatically.
3. Push each approved ref with an exact `--force-with-lease=<ref>:<old-oid>` from the repair result. Never use plain `--force` or `--mirror`.
4. Create a missing Release only after its annotated tag exists. Use `gh release create --verify-tag`; do not let GitHub create a tag from the default branch implicitly.
5. Recheck remote refs, tags, Releases, and the GitHub account after publishing. Publish the old-to-new SHA map as a migration artifact when collaborators need it.

## Hard Stops

Stop and surface the reason when the plan digest does not match, the source worktree is dirty, `git-filter-repo` is absent, the audit HEAD changed, the mirror output already exists, verification fails, or the selected GitHub account is unavailable.
