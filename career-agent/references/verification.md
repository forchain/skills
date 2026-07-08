# Verification

Run verification before external-facing text is final and before any long-term memory write.

## Source Grounding

Classify each external-facing sentence:

- Factual claim: must be supported by confirmed evidence.
- Fit interpretation: must be supported by JD requirements plus confirmed evidence.
- Motivation or voice claim: must be supported by `voice.md`, a selected file under `profiles/`, or the current user instruction.

If a claim is unsupported, delete it, weaken it, or ask the user to confirm the fact. Do not show the full grounding table unless there is a problem or the user asks.

## Privacy

Check for:

- contact details not requested for the format
- home address or legal identifiers
- salary or compensation
- confidential company, vendor, pipeline, or unreleased product details
- sensitive metrics that should be generalized

Use `public_resume` and safe `private_context` only. Never use `sensitive` in external text.

## Anti-AI Review

Apply only to external-facing text. Internal briefs and memory files can remain structured.

Reject or rewrite:

- mechanical JD mirroring
- exaggerated enthusiasm
- generic claims like "my background uniquely positions me"
- keyword stuffing
- polished marketing transitions that violate `voice.md`
- claims without concrete evidence

Target: plain, specific, human, and professionally restrained.

## Memory Write Verification

Before saving memory, verify:

- every evidence item has source refs
- confidence is not inflated
- visibility is conservative
- conflicts are not silently resolved
- voice rules are confirmed and not merely observed
- application-specific notes are not written as global rules

Show the exact proposed change summary and wait for explicit confirmation.
