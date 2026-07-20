# Repository History Repair

This context defines the language used by skills that audit and repair public Git and GitHub history while preserving an explicit safety boundary.

## Language

**Repair Plan**:
The complete, reviewable proposal for changing repository history, identities, messages, versions, tags, releases, and related public metadata.
_Avoid_: Fix script, rewrite commands, migration guess

**Audit**:
A read-only examination that produces a Repair Plan without changing Git objects, references, or GitHub state.
_Avoid_: Dry run, preview mode, scan

**Apply**:
The local execution of an approved Repair Plan in an isolated repository copy, without updating the public remote.
_Avoid_: Rewrite, fix, migration

**Publish**:
The explicit update of remote Git references and GitHub release state after the applied result passes validation.
_Avoid_: Push, deploy, sync

**Canonical Commit Identity**:
The user-confirmed author and committer identity that should represent the repository owner's own commits and associate them with the intended GitHub login.
_Avoid_: GitHub account, active account, correct user

**GitHub Login**:
The authenticated GitHub principal used for GitHub operations; it is distinct from the name and email stored in Git commit objects.
_Avoid_: Commit author, commit identity, Git user
