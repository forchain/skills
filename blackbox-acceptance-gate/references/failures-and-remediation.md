# Failures And Remediation

Read this file whenever execution produces an error, blocker, bypass, disputed result, or evidence gap. Classify the event before retrying or continuing.

## Runtime Classification

| Classification | Meaning | Required action |
| --- | --- | --- |
| `actionable` | An approved public or operator action can safely restore the prerequisite | Record the original error, remediate in-band, retry once, and record both outcomes |
| `force_majeure` | The run cannot practically resolve an external outage, suspension, billing state, permission, credential, or resource gap | Mark only affected items `skipped_force_majeure`; continue independent safe items |
| `hard_fail` | A required capability failed or actionable remediation did not recover it | Mark failed, stop dependent tests, and reopen system work |

Never continue tests whose failed prerequisite makes their result meaningless. If no approved remediation exists, classify its scope:

- **Reusable system behavior**: create or update the existing development plan.
- **Acceptance-only setup, cleanup, observation, or reporting**: update the checklist, report schema, and harness plan.
- **Unclear scope or changed risk**: ask the User to approve the classification.

Historical blockers with an approved remediation must appear as explicit prerequisites in the next contract and checklist.

Every exception record must contain the gate and test, observed error, classification, remediation, retry result, evidence, and final status.

## Finding Classification

| Finding | Meaning | Required action |
| --- | --- | --- |
| `acceptance_harness_gap` | System behavior may be correct but cannot be observed, cleaned up, or reported sufficiently | Update checklist, report, or harness; create system work only if reuse is expected |
| `system_defect` | The system fails an approved user-visible capability | Reopen the item and create or update development work using black-box evidence |
| `operational_reliability_gap` | A bypass lets this run continue, but the same condition can break normal operation | Keep the gap open in the report and create or update development work |
| `external_dependency_gap` | Third-party state or resources prevent validation | Apply `force_majeure` or `blocked` and request only the missing resource or decision |

For a system defect or operational reliability gap, record observable facts before continuing: criterion, public path and actions, timestamp, scope, observed result, expected result, and evidence artifact. Never include a suspected internal cause in a strict black-box handoff.

Append the smallest development demand to the existing plan for this workflow. Create a plan through the repository's normal planning process only when none exists. Once chosen, that plan remains the single source of truth.

```text
Development demand: [short title]
Source acceptance item: [gate/test ID]
Finding type: system_defect | operational_reliability_gap
Observed evidence: [timestamp, public path, result, artifact]
Expected behavior: [externally visible behavior]
Operational risk: [user/operator impact]
Required behavior: [minimal behavior change]
Safety constraints: [approval and automation limits]
Acceptance criteria: [black-box checks]
Status: proposed | approved | implemented | accepted | deferred
```

The run may continue after a bypass only when remaining tests are still meaningful and the report states that the system gap remains open. Ask for User review when a demand changes behavior, scope, operational risk, or safety policy.
