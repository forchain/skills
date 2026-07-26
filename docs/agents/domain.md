# Domain Docs

Before exploring code, read the relevant root `CONTEXT.md` and ADRs under `docs/adr/`.

This repository uses a single-context layout:

- `CONTEXT.md` contains domain vocabulary only.
- `docs/adr/` contains architectural decisions.
- Create these files lazily when domain terms or decisions are actually resolved.
- Use glossary vocabulary consistently.
- Surface conflicts with existing ADRs instead of silently overriding them.
