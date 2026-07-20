# Professional Repository Audit

Report findings separately from history repair. Do not silently add or change these files during Audit.

- Repository description, homepage, topics, and social preview.
- License, README, contribution guide, code of conduct, security policy, and issue/PR templates.
- CI coverage, required checks, dependency update automation, branch/ruleset protection, and CODEOWNERS where appropriate.
- Release process, changelog, package version source, annotated tags, release notes, and signed release policy.
- Commit message consistency, stale branches, large binaries, LFS, submodules, and leaked-secret scanning. Use a dedicated secret scanner when available; report an unavailable scanner as an unperformed check, not a clean result.

For each finding, state the evidence, impact, recommended action, and whether it is independent of history rewriting.
