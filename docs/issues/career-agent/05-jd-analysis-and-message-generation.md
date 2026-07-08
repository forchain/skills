# Issue 5: Generate Grounded Job Messages from JD Analysis

## What to build

Specify the job-description analysis and message-generation branch. The agent should judge JD quality, infer role intent, select core requirements, choose one primary positioning, ask one key question when needed, and generate one short English message by default.

## Acceptance criteria

- [ ] JD analysis distinguishes core requirements, supporting signals, template noise, and risk areas.
- [ ] Poor JD quality lowers confidence but does not block generation.
- [ ] Cross-domain roles use one primary positioning plus supporting signals.
- [ ] Unknown facts trigger one highest-value question at a time.
- [ ] Strategy and style questions include a recommended answer.
- [ ] Personal facts are never invented.
- [ ] Default output is one short English message.

## Blocked by

Issues 2 and 4.
