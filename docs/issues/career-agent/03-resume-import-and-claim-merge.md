# Issue 3: Support Resume Import, Deduplication, and Claim Merge

## What to build

Specify the end-to-end resume import path for pasted text, Markdown, PDF, and DOCX. Normalize sources, register them, detect duplicates and conflicts, extract candidate claims, and propose canonical evidence updates without writing them automatically.

## Acceptance criteria

- [ ] One resume can bootstrap usable candidate memory.
- [ ] Additional resumes can be imported later as source material.
- [ ] Raw normalized source and manifest records are saved as source-ingestion records after an explicit import request.
- [ ] Exact duplicates, near duplicates, new versions, and distinct resumes are classified.
- [ ] Conflicts are saved as unresolved claims and not silently resolved.
- [ ] Only high-value or high-risk extracted facts require immediate confirmation.
- [ ] Resume import does not become full resume optimization.

## Blocked by

Issue 2.
