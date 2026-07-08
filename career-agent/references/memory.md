# Career Memory

## Contents

- Root Layout
- Canonical Evidence
- Confidence
- Visibility
- Source Registry
- Conflicts
- Memory Status
- Memory Review

## Root Layout

```text
~/.career-agent/memory/
  base/
    identity.md
    voice.md
  sources/
    manifest.yml
    resumes/
  evidence/
    evidence.yml
    unresolved-claims.yml
  profiles/
```

V1 uses one global personal memory store. Target direction profiles are created on demand and only after user confirmation.

## Canonical Evidence

Store facts as source-grounded reusable career material, not generated prose:

```yaml
- id: exp_2026_ai_workflow_ops
  type: project
  canonical:
    title: Built an internal AI workflow for operations
    summary: "Built and iterated an AI-assisted workflow used by an operations team."
    context: "..."
    responsibilities:
      - "..."
    actions:
      - "..."
    results:
      - "..."
    metrics:
      - "..."
  tags:
    domains: [ai]
    functions: [backend, automation]
    skills: [llm, api_design]
    seniority_signals: [ownership, ambiguous_problem_solving]
  source_refs:
    - source_id: resume_2026_ai_en
  visibility: public_resume
  confidence: confirmed
  evidence_strength:
    level: strong
    reason: "Confirmed production or real-user usage with concrete ownership."
```

Keep generated resume bullets, platform text, and job messages under artifacts, not canonical evidence.

## Confidence

- `confirmed`: user-confirmed or directly supported by a trusted resume source and verified.
- `tentative`: extracted from sources but not yet confirmed.
- `inferred`: agent hypothesis only.

External-facing factual claims should use `confirmed` evidence. Tentative and inferred material can guide questions and positioning, but not strong claims.

## Visibility

- `public_resume`: safe for resumes and HR messages.
- `private_context`: useful for agent reasoning; do not publish without review.
- `sensitive`: internal details, private contact data, salary, confidential vendor names, unreleased company data, or legal identifiers.

Default to conservative privacy. Rewrite sensitive facts into safe summaries instead of exposing them.

## Source Registry

Record each source in `sources/manifest.yml`:

```yaml
- source_id: resume_2026_ai_en
  kind: resume
  path: sources/resumes/resume_2026_ai_en.raw.md
  original_path: /path/to/resume.pdf
  language: en
  imported_at: "2026-07-08"
  fingerprint: "..."
  status: active
```

Every evidence item needs source refs or a user-confirmed conversation source with date.

Source registry records are ingestion metadata. An explicit resume import request authorizes saving the raw normalized source and manifest entry. It does not authorize writing extracted claims into canonical evidence, voice rules, or profiles.

## Conflicts

When sources disagree on dates, titles, metrics, responsibilities, or scope:

1. Save the conflict to `evidence/unresolved-claims.yml`.
2. Do not update canonical evidence.
3. Ask the user to resolve it only when the conflict matters for a current task or memory review.

Never assume the newest resume is correct.

## Memory Status

Report:

- memory root existence
- source count and recent imports
- confirmed, tentative, and inferred evidence counts
- unresolved conflict count
- unconfirmed voice signal count
- target profile count

Keep the status concise and actionable.

## Memory Review

Review high-value and high-risk items first:

- unresolved conflicts
- sensitive candidates
- strong evidence candidates
- frequently relevant tentative evidence
- unconfirmed voice rules

After confirmed writes, show a short change summary:

```text
Saved:
- Added evidence exp_...
- Updated voice.md: ...
- No sensitive details included.
```
