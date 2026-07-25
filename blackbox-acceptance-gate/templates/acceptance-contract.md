# Acceptance Contract

## Skill Binding Metadata
- skill_id: blackbox-acceptance-gate
- skill_version:
- workflow_id:
- skill_run_root: docs/acceptance/blackbox-acceptance/<run-id>/
- source_contract:
- precondition_report: docs/acceptance/blackbox-acceptance/<run-id>/precondition-report.md
- governed_rules:
  - precondition_check_gate
  - document_approval_gate
  - blackbox_boundary
  - exception_force_majeure_policy
  - agent_isolation_and_lifecycle

## Goal
- User-visible outcome:
- Why this matters:
- Required completion date/context:

## Scope
- In scope:
- Out of scope:
- Non-goals:

## Roles
- User:
- Acceptance Coordinator:
- Development Agent:
- Testing Agent:

## Resources And Preconditions
- Environment:
- Accounts / permissions:
- Credentials / config:
- External systems:
- Data access:
- Safety limits:
- Precheck Status: pending | passed | blocked
- Precondition Check Report: [precondition-report.md](precondition-report.md)

## Acceptance Gates
| ID | Capability | Required Evidence | Human-Visible Proof | Status |
| --- | --- | --- | --- | --- |
| AC-001 |  |  |  | pending |

## Failure Classification
| Classification | Definition | Required Action |
| --- | --- | --- |
| actionable | Can be safely handled through approved public interfaces or documented operator actions | Remediate once, record evidence, retry once |
| force_majeure | Cannot be recovered inside the current run | Mark affected objective skipped, continue safe independent objectives |
| hard_fail | Required capability failed after allowed remediation | Reopen affected work and stop acceptance |

## Review
- Reviewed by User:
- Approved version/date:
- Change history:
