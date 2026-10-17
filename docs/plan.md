# Plan — sdd-demo

Only unfinished milestones. Delete a milestone's row and block in the commit that finishes it; git
history is the record. Template: `docs/workflow.md`.

**Next milestone number: M20**

## Milestones at a glance

| Milestone | Description | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M18** Sample build script | `scripts/build_sample.py` rebuilds `data/sample/` from the raw TalentCLEF files (DEC-010). | sonnet | medium | open |
| **M19** CI workflow | `.github/workflows/check.yml` on `windows-latest`, action versions pinned when built (DEC-018). | sonnet | medium | open |

## Milestones

### M18 — Sample build script

- **Refs:** DEC-010, spec section 1 (sample).
- **Owner:** `scripts/build_sample.py`.
- **Tests first:** `test_dec_010_builds_selected_jobs_and_cvs_into_output_folder`, `test_dec_010_each_job_has_at_least_three_labeled_cvs`, `test_dec_010_writes_ground_truth_for_selected_pairs`, `test_dec_010_raw_files_are_not_modified`.
- **Build:** a script that takes the raw folder, the output folder and the selected IDs as arguments and writes `job_descriptions/`, `cvs/`, `ground_truth.tsv` and `ATTRIBUTION.txt`. Tests use invented raw data.
- **Gate:** the checks pass; run in a scratch folder with the current sample IDs, it reproduces the files in `data/sample/` (compare, then delete the scratch folder).

### M19 — CI workflow

- **Refs:** DEC-018.
- **Owner:** `.github/workflows/check.yml`.
- **Tests first:** `test_dec_018_workflow_runs_on_windows_and_calls_check_script`, `test_dec_018_workflow_uses_constraints_and_pip_check`, `test_dec_018_workflow_has_no_secrets`.
- **Build:** the workflow in DEC-018, with each action pinned to an exact version looked up when built; confirm the tests run without `config/.env`.
- **Gate:** the checks pass. The first CI run is watched by the user (DEC-018); it is not part of this gate.
