# Resume Import

## Supported Inputs

Support pasted text and common resume files:

- Markdown or text: read directly.
- PDF: extract text with available local tools such as `pdftotext`; if extraction is unreliable, ask for DOCX, text, or pasted content.
- DOCX: convert with available local tools such as `pandoc` or macOS `textutil`; if conversion is unreliable, ask for pasted content.

Save normalized text as:

```text
~/.career-agent/memory/sources/resumes/<source_id>.raw.md
```

An explicit resume import request authorizes this source-ingestion write and the matching manifest entry. It does not confirm extracted facts as canonical memory.

## Import Flow

1. Normalize the source into raw Markdown while preserving source metadata.
2. Compute a fingerprint from normalized text.
3. Classify the source as exact duplicate, near duplicate, new version, or distinct resume.
4. Extract claims: roles, projects, skills, metrics, domains, dates, education, voice signals, and narrative signals.
5. Compare claims with canonical evidence.
6. Save raw source and manifest records.
7. Produce an import summary and candidate updates.

## Import Summary

Show:

```text
Import Summary:
- New source: resume_2026_ai_en.pdf
- Detected language: English
- Likely resume type: AI/backend oriented
- New candidate evidence: 12
- Possible updates to existing evidence: 5
- Conflicts: 1
- Voice signals observed: 4
```

Do not ask the user to confirm every extracted claim. Only ask for high-value or high-risk items:

- conflicts
- sensitive information
- low-confidence extraction
- strong evidence that will likely be reused

Other extracted claims can remain tentative candidates.

## Multiple Resumes

Treat multiple resumes as complementary source material. Different resumes may emphasize different directions or languages. Merge into canonical evidence only after conflict checks.

English resume phrasing can inform `voice.md` as observed signals, but does not become confirmed voice preference without user confirmation.

## Resume Review Boundary

Only flag resume issues that affect later job-message generation or memory quality, such as missing metrics or unclear project scope. Do not perform full resume optimization in V1.
