# Repair Plan Policy

Use this policy to create an approved Repair Plan after Audit. Keep the plan outside the target repository so Apply can require a clean worktree.

```json
{
  "schema_version": 1,
  "audit": {"head": "<exact audited HEAD SHA>"},
  "refs": ["refs/heads/main", "refs/tags/v1.2.3"],
  "canonical_identity": {
    "name": "<confirmed name>",
    "email": "<confirmed email>",
    "github_login": "<confirmed GitHub login>"
  },
  "identity_mappings": [
    {"from": {"name": "<old name>", "email": "<old email>"}}
  ],
  "message_mappings": [
    {"commit": "<old SHA>", "message": "<complete replacement message>"}
  ]
}
```

Map identities by the exact pair only. The Apply callback changes author and committer fields independently when either exactly equals an approved source pair.

`refs` is the complete approved rewrite boundary. Use full branch and tag ref names from Audit; do not include pull-request, remote-tracking, notes, or replace refs.

Message replacements are full UTF-8 commit messages, not subjects. Preserve bodies and trailers unless the plan explicitly changes them. Keep the message map limited to reviewed commits; do not run a global language transform.

Record intended branches, tags, Releases, and their supporting evidence in the review narrative. Existing signed commits and signed tags lose cryptographic validity when their objects are rewritten; recreate signatures only with the owner's available signing key.

Evidence ranking for a version or Release is: existing tag/Release, changelog, version-file history, build artifact, then a documented product milestone. Do not create a historical version when no evidence reaches that threshold.
