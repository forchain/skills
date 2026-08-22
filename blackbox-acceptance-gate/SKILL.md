---
name: blackbox-acceptance-gate
description: Gate acceptance of new or existing implementations through an approved contract, independent black-box testing, externally verifiable evidence, and a traceable verdict. Use when development and acceptance must stay isolated or when a release needs user-approved acceptance criteria.
summary: Gate changes through approved criteria, isolated black-box testing, verifiable evidence, and a traceable verdict.
---

# Black-Box Acceptance Gate

Run acceptance as a gated state machine: **contract -> precheck -> approval -> isolation -> execution -> verdict**. Durable artifacts, not conversation history, are the source of truth.

## Boundary

The Testing Agent may use only approved public interfaces and operator-visible outputs: documented UI, CLI, API, generated artifacts, public logs, and data access only when it is a documented product surface. It must not inspect source, diffs, implementation notes, private state, mocks that replace user-visible behavior, or Development Agent reasoning.

The User owns goals, constraints, exceptions, resources, and final scope decisions. The Acceptance Coordinator owns the contract, gates, and routing. The Development Agent changes the system under test. The Testing Agent independently evaluates it.

## 1. Bind The Contract

Choose the mode:

- **New development**: define acceptance before implementation.
- **Existing implementation**: treat the current build as the system under test and reconstruct criteria only from user intent and public requirements.

Create or update the four artifacts from `templates/`:

- acceptance contract (`acceptance-contract.md`)
- precondition check report (`precondition-report.md`)
- testing checklist (`testing-checklist.md`)
- execution report (`execution-report.md`)

Default run root: `docs/acceptance/blackbox-acceptance/<run-id>/`. Preserve an established repository location when one exists and record it as `skill_run_root`.

The contract header must contain:

```yaml
skill_id: blackbox-acceptance-gate
skill_run_root: <artifact directory>
workflow_id: <stable run id>
source_contract: <path>
```

Map every required acceptance gate to at least one checklist item with a purpose, setup, public actions, expected observable result, evidence, human verification path, and failure handling. Create or reuse a development plan only when system changes are required.

**Complete when:** the four artifacts exist, metadata is valid, every required gate is testable from the outside, and every gate has an evidence path.

## 1.5 Precheck Dependencies

Before presenting any contract or plan to the User for review, perform mandatory read-only diagnostic checks for all required external resources, dependencies, and prerequisites.

1. **Identify dependencies**: Enumerate every external resource required for execution or acceptance (e.g., databases, log directory access, exchange/third-party API endpoints, test account credentials, environment variables, required CLI binaries).
2. **Execute diagnostic probes**: Run read-only, non-mutating operator diagnostic commands (e.g., connection ping, API status check, permission read test, version check). Do NOT use mock objects to fake connectivity or assume prerequisites pass without empirical proof.
3. **Record evidence**: Append raw diagnostic outputs, timestamps, and pass/fail statuses to `precondition-report.md`.
4. **Enforce hard block**: If any required dependency is `failed` or `unclear/missing`, **DO NOT submit the document/contract for User Review**. Issue a `Precondition Shortage Alert` listing the exact missing resources or failed checks, resolve them or prompt the User for missing credentials/info, and re-probe until all dependencies pass.

**Complete when:** `precondition-report.md` exists, 100% of required dependencies have `passed` status with timestamped diagnostic evidence, and `precheck_status` in the contract is set to `passed`.

## 2. Lock Approval

Present the artifacts, precheck report, and checklist to the User ONLY AFTER Section 1.5 (Precheck Dependencies) has 100% passed. Do not implement or execute tests until the User approves the current contract and checklist.

Before approval, limit discovery to read-only work without external side effects, scarce-resource use, or third-party mutation. If feedback changes scope, evidence, resources, permissions, remediation, or verifiability, update the artifacts, re-run prechecks if dependencies changed, and obtain approval again for any material contract change.

If the User rejects evidence previously marked passed, set the item to `reopened` or `failed` immediately.

**Complete when:** `precondition-report.md` is 100% passed, the contract records the approved version and date, and all material feedback appears in the artifact set.

## 3. Enforce Isolation

Check whether independent sub-agents are available before assigning work.

- When available, Development and Testing MUST use separate sub-agents. Do not spawn Development for testing-only work or when Testing finds no system change is needed. Close each agent when its assignment ends.
- Give Testing only the approved checklist, public setup, allowed observation methods, user-visible criteria, and contract metadata. Include: `This contract is governed by blackbox-acceptance-gate.` Require it to echo the skill name and run root before execution.
- When unavailable, say: `Sub-agent isolation unavailable; strict black-box mode cannot be guaranteed in this session.` Ask the User to enable sub-agents or explicitly approve degraded mode. If strict isolation is required, stop. In approved degraded mode, freeze Testing inputs before consulting implementation details and never claim independent validation.

**Complete when:** role assignments and permitted inputs are recorded, or degraded mode has explicit User approval.

## 4. Execute The Checklist

Before each action, link it to a checklist item. If none applies, stop and amend the approved artifacts before proceeding.

For each item:

1. Set `in_progress` and record the start time.
2. Execute only approved public actions within safety and retry limits.
3. Capture the evidence required by the checklist.
4. Set `passed`, `failed`, `blocked`, `skipped_force_majeure`, or `reopened` and append evidence to the report.

Evidence for every required item must include its ID and purpose; timestamp and timezone; system, environment, and account or scope; affected resources; externally visible identifiers; observed versus expected status; exact human verification path and filters; decision; and residual risk. A capability without user-verifiable evidence cannot pass.

On any error, blocker, bypass, disputed result, or evidence gap, read and apply `references/failures-and-remediation.md` before continuing. For escalation or resource decisions, also read `references/coordination-and-escalation.md`.

**Complete when:** every required checklist item has a terminal status and evidence, and no downstream test ran behind a failed prerequisite that made its result meaningless.

## 5. Issue The Verdict

Accept only when:

- every required item passed; or
- all non-passing required items are `skipped_force_majeure` and the contract permits cycle acceptance with explicit annotation; or
- the User explicitly accepts a documented exception.

Any non-force-majeure failure leaves the run unaccepted. Reopen affected items before returning to development. Keep system-specific outcomes, credentials, and decisions in run artifacts, never in this skill.

The final report must enumerate passed, failed, blocked, reopened, and force-majeure-skipped items; remediation; open development demands; agent allocation and closure; residual risk; and the acceptance decision.

**Complete when:** the report traces every verdict to an approved gate and externally verifiable evidence, all agents are closed, and the run is accepted or stopped on a specific User-owned decision or resource.
