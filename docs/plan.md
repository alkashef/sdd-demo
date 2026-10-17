# Plan — sdd-demo

Only unfinished milestones. Delete a milestone's row and block in the commit that finishes it; git
history is the record. Template: `docs/workflow.md`.

**Next milestone number: M20**

## Milestones at a glance

| Milestone | Description | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M19** CI workflow | `.github/workflows/check.yml` on `windows-latest`, action versions pinned when built (DEC-018). | sonnet | medium | open |

## Milestones

### M19 — CI workflow

- **Refs:** DEC-018.
- **Owner:** `.github/workflows/check.yml`.
- **Tests first:** `test_dec_018_workflow_runs_on_windows_and_calls_check_script`, `test_dec_018_workflow_uses_constraints_and_pip_check`, `test_dec_018_workflow_has_no_secrets`.
- **Build:** the workflow in DEC-018, with each action pinned to an exact version looked up when built; confirm the tests run without `config/.env`.
- **Gate:** the checks pass. The first CI run is watched by the user (DEC-018); it is not part of this gate.
