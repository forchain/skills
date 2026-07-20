# Coordination And Escalation

Read this file when the Acceptance Coordinator must decide whether to resolve an issue within the approved contract, request a low-risk resource, or escalate to the User. Keep every decision grounded in the current acceptance gates and black-box evidence.

## Escalation Matrix

| Situation | Acceptance Coordinator action |
| --- | --- |
| Acceptance criteria are missing, contradictory, or materially ambiguous | Ask the User to clarify before implementation or acceptance continues. |
| A change would alter user-visible scope, cost, schedule, risk, policy, data handling, or compatibility | Escalate to the User with options and tradeoffs. |
| The Testing Agent reports a required criterion failed | Reopen to the Development Agent with a black-box failure report; escalate only if the fix requires a scope or policy decision. |
| The Testing Agent uses a test-only bypass for a condition that could affect normal operation | Continue only if downstream acceptance remains meaningful, and create or update a development demand for the operational reliability gap. |
| The Testing Agent reports an observable weakness outside the current gate that could make operation unsafe, unverifiable, or silently degraded | Record a proposed development demand and ask the User to approve, defer, or reject it if it changes scope or behavior. |
| Development disputes a Testing failure using implementation details | Keep the black-box result as controlling; request externally observable evidence or reopen. |
| Testing cannot validate because an external account, credential, environment, data source, paid resource, or manual permission is missing | Escalate to the User unless a low-risk resource request applies. |
| A requested test would expose secrets, mutate protected data, violate policy, or create meaningful operational risk | Stop and escalate to the User. |
| A non-critical criterion is infeasible or too expensive to test black-box in the current environment | Ask the User whether to waive, defer, or provide resources. |
| All required criteria pass and no unresolved User-owned decisions remain | Accept and report the evidence. |

## Internal Resolution

The Acceptance Coordinator may resolve these without interrupting the User:

- Reorder work without changing scope.
- Ask either agent to clarify its own output.
- Request a rerun when it cannot hide a real system issue.
- Reduce a failure report to observable facts before handoff.
- Split broad criteria into smaller black-box checks without changing meaning.
- Choose among equivalent documented public interfaces.
- Drop duplicate checks when another check proves the same observable behavior.

## Low-Risk Resource Request

Use this concise request when a missing resource is clearly required and low-risk:

```text
Acceptance is blocked by missing [resource].
Needed for: [criterion or workflow].
Risk level: low because [no secrets / no protected-system mutation / disposable scope].
Please provide [specific item] or approve [specific alternative].
```

Low-risk resources can include a disposable test account, sample input files, limited non-production credentials, a temporary preview URL, or approval to run a local command. Credentials with broad access, protected-system access, billing changes, destructive actions, private user data, and policy exceptions are not low-risk.

## Reopen Report

Send only black-box facts when reopening work:

```text
Failed criterion: [criterion]
Steps taken: [public actions or commands]
Observed: [actual externally visible behavior]
Expected: [required externally visible behavior]
Evidence: [public logs, screenshots, files, responses, or artifacts]
```

Do not include suspected internal causes, blame, private reasoning, or implementation recommendations unless the User explicitly asks for diagnostic work outside strict black-box acceptance.

## Development Demand

Keep development demands separate from acceptance-harness fixes. A harness fix makes the test runnable or verifiable; a development demand changes the system under test.

```text
Development demand: [short title]
Source acceptance item: [criterion/test ID]
Finding type: system_defect | operational_reliability_gap
Observed: [actual externally visible behavior]
Expected behavior: [required externally visible behavior]
Operational risk: [operator/user impact if not fixed]
Evidence: [logs, reports, screenshots, response IDs, or artifacts]
Acceptance criteria: [black-box checks required before closure]
Decision needed: [approve / defer / reject / needs scope decision]
```

Append the demand to an active development document for the same workflow. If none exists, use the repository's normal planning process to create one. Keep later requirements for the same workflow in that document.
