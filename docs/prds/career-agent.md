# PRD: Career Agent Skill

## Problem Statement

Job-search writing requires repeatedly translating a person's career history into materials that fit a specific role, company, platform, and communication style. A raw resume is too compressed to serve as the only source of truth, and job descriptions are often noisy, templated, or overloaded. The user wants an agent skill that can build a durable, source-grounded career memory, ask interview-like follow-up questions, preserve the user's professional voice, and generate credible job messages without sounding like generic AI text.

The user also wants the system to stay simple enough to use after long gaps. The ordinary interface should accept natural-language requests instead of forcing the user to remember many subcommands.

## Solution

Build a `career-agent` skill. The skill acts as a natural-language router over a private career memory stored outside the skill directory. V1 focuses on the core loop: resume import, source-grounded canonical evidence, voice onboarding, JD analysis, application brief generation, one short English job message, artifact saving, and verified memory updates.

The skill uses a thin `SKILL.md` and progressively disclosed references so future modules can grow without making the entrypoint hard to maintain. It separates Planner, Executor, and Verifier artifacts to reduce hallucination and context contamination. It defaults to safe behavior: JD analysis does not update memory, tentative facts are not used as strong external claims, and long-term memory writes require explicit confirmation.

## User Stories

1. As a job seeker, I want to import my latest resume, so that the agent can start from my real career history.
2. As a job seeker, I want to import more resumes later, so that older or differently targeted versions can fill missing history.
3. As a job seeker, I want duplicate resumes detected, so that repeated imports do not pollute memory.
4. As a job seeker, I want conflicts between resume versions surfaced, so that wrong dates or inflated claims do not become canonical.
5. As a job seeker, I want resumes treated as source material, so that long-term memory is cleaner than any single resume.
6. As a job seeker, I want candidate career evidence generated for me, so that I do not have to structure every fact manually.
7. As a job seeker, I want high-risk and high-value extracted facts confirmed first, so that onboarding does not become a long form.
8. As a job seeker, I want each evidence item to keep its source, so that future outputs can be audited.
9. As a job seeker, I want tentative facts kept separate from confirmed facts, so that drafts do not overstate my experience.
10. As a job seeker, I want sensitive details marked conservatively, so that private or confidential information is not exposed to HR.
11. As a job seeker, I want a professional voice profile, so that generated messages sound like me.
12. As a job seeker, I want the voice profile created through guided choices, so that I do not need to write it from a blank page.
13. As a job seeker, I want English and Chinese voice rules separated, so that Chinese messages are not awkward translations of English style.
14. As a job seeker, I want my critique of a draft converted into candidate voice rules, so that the agent learns from feedback.
15. As a job seeker, I want JD quality judged, so that templated or overloaded job descriptions are handled realistically.
16. As a job seeker, I want the agent to infer the employer's role intent, so that the message responds to what matters most.
17. As a job seeker, I want one primary positioning for cross-domain roles, so that I do not sound unfocused.
18. As a job seeker, I want supporting signals selected carefully, so that the message has focus instead of a checklist.
19. As a job seeker, I want the agent to ask one key follow-up question at a time, so that I can provide useful missing facts.
20. As a job seeker, I want recommended answers for strategy and style questions, so that I am not forced to invent wording from scratch.
21. As a job seeker, I want the agent not to invent personal facts, so that messages remain truthful.
22. As a job seeker, I want a short English message by default, so that the output fits real HR, recruiter, LinkedIn, or referral contexts.
23. As a job seeker, I want formal cover letters to be optional, so that the default remains lightweight.
24. As a job seeker, I want only one best version by default, so that I can critique and improve rather than choose between many drafts.
25. As a job seeker, I want an anti-AI review for external text, so that the final message avoids generic corporate phrasing.
26. As a job seeker, I want source-grounding checks, so that every factual claim in the message has support.
27. As a job seeker, I want application artifacts saved, so that I can review or regenerate a prior application later.
28. As a job seeker, I want JD artifacts separated from career memory, so that external job requirements do not become facts about me.
29. As a job seeker, I want memory status, so that I can see unresolved conflicts, tentative facts, and voice signals.
30. As a job seeker, I want memory review, so that I can safely confirm or reject accumulated candidate facts.
31. As a job seeker, I want target direction profiles created only when needed, so that setup stays light.
32. As a job seeker, I want profile blends for overlapping roles, so that Web3 AI or AI quant roles do not force rigid folders.
33. As a job seeker, I want first-run guidance to be short, so that I can use the agent even if I forgot how it works.
34. As a skill maintainer, I want the skill entrypoint to stay thin, so that future modules do not create context sprawl.
35. As a skill maintainer, I want detailed rules in references, so that each branch loads only the context it needs.
36. As a skill maintainer, I want a local PRD and issue breakdown, so that future implementation can proceed in clear vertical slices.

## Implementation Decisions

- Build one `career-agent` skill rather than a collection of separate skills in V1. The modules share the same career memory, evidence schema, voice rules, privacy rules, and verifier contract.
- Keep `SKILL.md` as a thin router. Put branch-specific detail in one-level reference files to protect predictability and avoid context sprawl.
- Use `message` as the user-facing term for job-search communications.
- Store private personal data under a user home data root, not inside the installed skill directory.
- Store generated JDs, briefs, and messages as artifacts by default. Artifacts are not long-term personal memory.
- Treat raw resume files and source manifest entries as source-ingestion records authorized by an explicit import request; extracted facts still require confirmation before becoming canonical memory.
- Treat resumes as source material. Generate canonical evidence candidates from one or more resumes, but preserve sources and conflicts.
- Support PDF, DOCX, Markdown, text, and pasted resume import by using available local conversion tools; fall back to asking for pasted text when extraction is unreliable.
- Use confidence levels for evidence: confirmed, tentative, inferred.
- Use visibility levels for facts: public resume, private context, sensitive.
- Use source refs for every canonical evidence item.
- Create target direction profiles on demand, not during first-run onboarding.
- For overlapping career directions, use tag-based evidence plus one primary positioning and supporting signals.
- Default message output is one short English draft. Chinese output is available but V1 does not deeply adapt to Boss, Liepin, or other domestic platform templates.
- Do not implement recruitment website automation in V1.
- Do not implement application outcome tracking in V1.
- Do not implement explicit temporary mode in V1; safe defaults make it unnecessary.
- Use a Planner, Executor, Verifier artifact split. Use independent contexts when available; otherwise keep the artifacts separate in one run.

## Testing Decisions

- The highest test seam is skill behavior over sample local artifacts: a sample resume, a second conflicting resume, a sample JD, and a sample voice feedback phrase.
- Good tests assert external behavior: expected files, summaries, candidate updates, and verifier warnings. Avoid testing internal wording unless the wording is part of a safety rule.
- Validate skill structure with the repository validator and Codex skill validator.
- Manually smoke-test the reference loading model by checking that each branch has a clear pointer from `SKILL.md`.
- Verify that no memory write path exists without explicit confirmation in the skill instructions.
- Verify that external-facing text generation requires verification references.

## Out of Scope

- Automatic LinkedIn, Boss, Liepin, or recruiter-site form filling.
- Full resume optimization and platform-specific profile generation.
- Application outcome tracking.
- Vector databases or semantic search infrastructure.
- Company research or web lookup by default.
- Multiple personal memory stores.
- A standalone CLI or app separate from the skill.

## Further Notes

V1 success means one recent resume can bootstrap memory and one JD can produce a grounded short English message. Multiple resume import is supported as an incremental enhancement path, not a prerequisite before use.
