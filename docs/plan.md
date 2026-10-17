# Plan — sdd-demo

Only unfinished milestones. Delete a milestone's row and block in the commit that finishes it; git
history is the record. Template: `docs/workflow.md`.

**Next milestone number: M20**

## Milestones at a glance

| Milestone | Description | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M13** Front end shell and lists | `index.html`, theme, `api.js`, list view, sticky header, file names (DEC-019); first headless-browser tests. Installs `playwright`. | sonnet | high | open |
| **M14** Job view | Job text panel and foldable ranked candidate cards with recommendation and attributes (DEC-020). | sonnet | medium | open |
| **M15** Candidate view | Raw CV, attributes and ranked job descriptions. | sonnet | medium | open |
| **M16** Failure and unavailable states | Failure panel, "Not available" values, and "Present" against unknown end (DEC-015). | sonnet | medium | open |
| **M17** Evaluation | `evaluation.py` and `main.py --evaluate` for NFR-004 and NFR-005; `.gitignore` exception so `gold_jobs.json` is committed (DEC-017). | sonnet | high | open |
| **M18** Sample build script | `scripts/build_sample.py` rebuilds `data/sample/` from the raw TalentCLEF files (DEC-010). | sonnet | medium | open |
| **M19** CI workflow | `.github/workflows/check.yml` on `windows-latest`, action versions pinned when built (DEC-018). | sonnet | medium | open |

## Milestones

### M13 — Front end shell and lists

- **Refs:** LST-001, LST-002, DEC-002, DEC-012, DEC-019.
- **Owner:** `src/web/` (`index.html`, `css/theme.css`, `css/base.css`, `css/layout.css`, `js/main.js`, `js/config.js`, `js/log.js`, `js/api.js`, `js/format.js`, `js/list-view.js`) and `tests/e2e/ui/`.
- **Tests first:** `test_lst_001_ui_lists_job_descriptions`, `test_lst_002_ui_lists_candidates`, `test_dec_019_ui_header_stays_at_top_when_page_scrolls`, `test_dec_019_ui_file_name_sits_below_name_in_smaller_size`, `format.test.js` for the score and "Not available" formatting.
- **Build:** the page structure and tokens from `docs/frontend/README.md`, the navigation with both lists, the sticky header, data only through `api.js`. Install `playwright` (uses the installed Edge or Chrome), pin it, run `python scripts/lock.py`.
- **Gate:** the checks pass, including ESLint, tsc, Prettier, Stylelint and `node --test`. If no Edge or Chrome is found, set Status to `blocked`.

### M14 — Job view

- **Refs:** JOB-002, JOB-003, RNK-003, REC-001, MIS-001, DEC-019, DEC-020.
- **Owner:** `src/web/js/job-view.js`, `src/web/js/attribute-fill.js`, `src/web/css/detail.css`.
- **Tests first:** `test_job_002_ui_selecting_job_shows_ranked_candidates_best_first`, `test_job_003_ui_job_text_panel_sits_above_the_cards`, `test_rnk_003_ui_card_shows_extracted_and_calculated_attributes`, `test_rec_001_ui_card_shows_recommendation_pill_and_reason`, `test_dec_019_ui_card_folds_to_its_summary_line`.
- **Build:** the job view per `docs/frontend/README.md`: heading, the "Job description text" `<details open>` panel, one foldable card per candidate.
- **Gate:** the checks pass; the page matches the approved mockups in `docs/frontend/`.

### M15 — Candidate view

- **Refs:** CND-001, CND-002, CND-003, DEC-019.
- **Owner:** `src/web/js/candidate-view.js` (and `src/web/css/detail.css`).
- **Tests first:** `test_cnd_001_ui_selecting_candidate_shows_raw_cv`, `test_cnd_002_ui_shows_extracted_and_calculated_attributes`, `test_cnd_003_ui_shows_ranked_jobs_best_first_without_recommendation`.
- **Build:** the candidate view per `docs/frontend/README.md`: raw CV beside the attributes card, then the ranked job descriptions.
- **Gate:** the checks pass; the page matches the approved mockups in `docs/frontend/`.

### M16 — Failure and unavailable states

- **Refs:** ERR-001, ERR-002, MIS-001, MIS-002, DEC-015.
- **Owner:** `src/web/js/failures-view.js` (and the job and candidate views).
- **Tests first:** `test_err_001_ui_failure_panel_names_the_cause`, `test_err_002_ui_keeps_lists_and_raw_texts_when_calls_failed`, `test_mis_001_ui_shows_not_available_for_missing_value`, `test_mis_002_ui_candidate_without_name_stays_listed_by_file_name`, `test_dec_015_ui_unknown_end_shows_not_available_not_present`, `test_dec_015_ui_current_job_shows_present`.
- **Build:** the amber failure panel and the failure list, the grey "Not available" recommendation pill, and the end-date rule for the last job.
- **Gate:** the checks pass; the page matches `docs/frontend/job-view-service-unavailable.dc.html`.

### M17 — Evaluation

- **Refs:** NFR-004, NFR-005, RNK-001, EXT-009, DEC-017, design section 3 (evaluation files).
- **Owner:** `src/evaluation.py`, `main.py` (`--evaluate`), `.gitignore`, `data/sample/gold_jobs.json`.
- **Tests first:** `test_nfr_004_passes_when_two_of_top_three_are_labeled_relevant`, `test_nfr_004_fails_when_only_one_is_relevant`, `test_nfr_004_fails_with_no_labeled_job_description`, `test_nfr_005_match_needs_same_start_end_and_is_current`, `test_nfr_005_failed_extraction_counts_as_misses`, `test_nfr_005_extra_extracted_jobs_not_penalized`, `test_nfr_005_fails_with_no_gold_jobs`, `test_dec_017_ground_truth_parser_adds_txt_suffix`, `test_dec_017_report_has_counts_never_cv_content`, `test_dec_017_bad_file_stops_before_any_llm_call`, `test_dec_017_evaluate_exits_1_when_a_check_fails`.
- **Build:** the pure parsing and checks; `main.py --evaluate` builds the same workspace, prints the report and exits 1 on a failed check; add the `.gitignore` exception for `data/sample/gold_jobs.json` and commit the file as drafted; document `--evaluate` in `README.md`.
- **Gate:** the checks pass. The manual run with the live service is the user's, after the user reviews the gold file (spec section 7); the numbers are recorded later in the Check columns of DEC-003 and DEC-004.

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
