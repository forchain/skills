# Issue 6: Verify External Text and Memory Writes

## What to build

Define the verifier pass for external-facing text and memory updates. The verifier checks source grounding, privacy, anti-AI writing, confidence handling, and confirmed write boundaries.

## Acceptance criteria

- [ ] Every factual claim in external text must map to confirmed evidence.
- [ ] Fit claims must be supported by JD requirements and confirmed evidence.
- [ ] Sensitive information is not used in external text.
- [ ] Anti-AI checks apply to external-facing text, not internal artifacts.
- [ ] Memory updates are shown exactly before saving.
- [ ] Verifier details are hidden unless there is a problem or the user asks to expand.

## Blocked by

Issues 2, 4, and 5.
