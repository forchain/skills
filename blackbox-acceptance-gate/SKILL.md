---
name: blackbox-acceptance-gate
description: "Gate a new or existing implementation through a user-approved acceptance contract, isolated black-box testing, externally verifiable evidence, and a traceable verdict. Use when acceptance must stay independent of development, or when a release or existing build needs user-approved acceptance criteria."
summary: "Gate changes through approved criteria, isolated black-box testing, verifiable evidence, and a traceable verdict."
---

# Black-Box Acceptance

Acceptance runs as a state machine — **contract → probe → approval → isolation → execution → verdict** — and its durable artifacts, not conversation history, are the source of truth.

## Roles and boundary

You are the Acceptance Coordinator: you own the contract, the gates, and routing. The User owns goals, constraints, exceptions, resources, and final scope. The Development Agent changes the system under test; the Testing Agent evaluates it independently.

**Black-box** means the Testing Agent reads only approved public surfaces — documented UI, CLI, API, generated artifacts, public logs, and data access where it is a documented product surface. Source, diffs, implementation notes, private state, mocks that replace user-visible behavior, and Development reasoning stay out of its inputs.

## 1. Bind the contract

Choose the mode:

- **New development**: define acceptance before implementation.
- **Existing implementation**: the current build is the system under test; reconstruct criteria from user intent and public requirements only.

Copy the four artifacts from `templates/` — acceptance contract, precondition report, testing checklist, execution report — and fill their Skill Binding Metadata with `skill_id: blackbox-acceptance-gate`.

Default run root: `docs/acceptance/blackbox-acceptance/<run-id>/`. Keep an established repository location when one exists and record it as `skill_run_root`.

Map every required acceptance gate to at least one checklist item: purpose, setup, public actions, expected observable result, evidence, human verification path, failure handling. Create or reuse a development plan only when system changes are required.

**Complete when:** the four artifacts exist, metadata is valid, every required gate is testable from the outside, and every gate has an evidence path.

## 2. Probe the preconditions

Before showing any contract to the User, prove every external dependency works.

1. **List** each dependency execution or acceptance needs: databases, log access, third-party APIs, test accounts, credentials, environment variables, CLI binaries.
2. **Probe** each one read-only — ping, status check, permission read, version check. No mocks, no assumed passes.
3. **Record** raw output, timestamp, and pass/fail in `precondition-report.md`.
4. **Block** on any `failed` or `unclear` dependency: issue a Precondition Shortage Alert naming the exact gap, resolve it or ask the User for the missing resource, and re-probe until everything passes.

**Complete when:** every required dependency is `passed` with timestamped evidence and the contract's `precheck_status` is `passed`.

## 3. Lock approval

Present the artifacts, precheck report, and checklist to the User, and wait for approval before implementing or testing.

Keep discovery before approval read-only: no external side effects, scarce-resource use, or third-party mutation. Material feedback on scope, evidence, resources, permissions, remediation, or verifiability updates the artifacts and needs approval again; re-probe if dependencies changed. If the User rejects evidence marked passed, set it to `reopened` or `failed` immediately.

**Complete when:** the precheck report is 100% passed, the contract records the approved version and date, and all material feedback appears in the artifact set.

## 4. Enforce isolation

Check for sub-agents before assigning work.

- **Available**: Development and Testing run as separate sub-agents. Do not spawn Development for testing-only work or when Testing finds no system change needed. Close each agent when its assignment ends.
- **Testing's inputs**: the approved checklist, public setup, allowed observation methods, user-visible criteria, and contract metadata — nothing else. Include: `This contract is governed by blackbox-acceptance-gate.` Require it to echo the skill name and run root before executing.
- **Unavailable**: say `Sub-agent isolation unavailable; strict black-box mode cannot be guaranteed in this session.` Then ask the User to enable sub-agents or approve degraded mode; stop if strict isolation is required. In degraded mode, freeze Testing inputs before consulting implementation details and never claim independent validation.

**Complete when:** role assignments and permitted inputs are recorded, or degraded mode has explicit User approval.

## 5. Execute the checklist

Link every action to a checklist item; if none applies, stop and amend the approved artifacts first.

For each item:

1. Set `in_progress` and record the start time.
2. Execute only approved public actions within safety and retry limits.
3. Capture the evidence the checklist requires.
4. Set `passed`, `failed`, `blocked`, `skipped_force_majeure`, or `reopened`, and append the evidence to the report.

Every required item's evidence carries its ID and purpose; timestamp and timezone; system, environment, and account or scope; affected resources; externally visible identifiers; observed versus expected result; exact human verification path and filters; decision; and residual risk. A capability without user-verifiable evidence cannot pass.

On any error, blocker, bypass, disputed result, or evidence gap, apply `references/failures-and-remediation.md` before continuing. When deciding whether to resolve an issue in-contract, request a low-risk resource, or escalate to the User, also apply `references/coordination-and-escalation.md`.

**Complete when:** every required item has a terminal status and evidence, and no test ran behind a failed prerequisite that made its result meaningless.

## 6. Issue the verdict

Accept only when:

- every required item passed; or
- all non-passing required items are `skipped_force_majeure` and the contract permits cycle acceptance with explicit annotation; or
- the User explicitly accepts a documented exception.

Any other failure leaves the run unaccepted; reopen affected items before returning to development. Keep system-specific outcomes, credentials, and decisions in run artifacts, never in this skill.

The final report enumerates passed, failed, blocked, reopened, and force-majeure-skipped items; remediation; open development demands; agent allocation and closure; residual risk; and the acceptance decision.

**Complete when:** the report traces every verdict to an approved gate and externally verifiable evidence, all agents are closed, and the run is accepted or stopped on a specific User-owned decision or resource.
