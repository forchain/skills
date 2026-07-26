# Career Agent Architecture

## Entrypoint

Use `$career-agent <natural language request>` as the ordinary interface. Subcommands are optional shortcuts for advanced users:

- `import-resume`
- `voice onboard`
- `message`
- `memory status`
- `memory review`

Do not require the user to know temporary modes, internal schemas, or command names.

## Planner, Executor, Verifier

For complex work, separate the work into three artifacts even if true subagents are unavailable:

1. Planner: intent, needed files, risk, success criteria.
2. Executor: extracted claims, brief, draft, or candidate update.
3. Verifier: source-grounding, privacy, voice, and memory-write checks.

When independent subagents are available and the work is large or high risk, use separate contexts for Planner, Executor, and Verifier. Pass only the needed raw artifacts and instructions to each context.

## Storage Roots

Default private data root:

```text
~/.career-agent/
  config.yml
  memory/
  artifacts/
```

The skill directory is not the memory directory. Never store private career memory inside the installed skill folder.

## Artifact Strategy

Save generated application work by default:

```text
~/.career-agent/artifacts/applications/
  YYYY-MM-DD_company_role/
    jd.raw.md
    application-brief.md
    message.md
```

Generate folder names automatically from company, role title, source platform, and date. If metadata is missing, use `unknown-company` or `unknown-role` without interrupting the flow.

Artifacts are not long-term memory. They can inform reruns, but do not become evidence or voice rules without explicit confirmation.

## Operation Classes

- Read-only: run directly. Example: memory status, JD quality check.
- Generate-only: produce artifacts and drafts, but do not write memory.
- Source-ingestion: after an explicit resume import request, save normalized raw source and manifest records.
- Canonical memory-writing: show planned evidence, voice, or profile writes; verify them; wait for confirmation.

Analyzing or importing a JD never updates long-term personal memory by itself.

## First Run

Use the shortest actionable prompt:

```text
I do not have your career memory yet. To write a credible message, send a recent resume path or paste the resume text. I can also make a low-confidence draft if you want to continue without memory.
```

Do not explain the whole system on first run.
