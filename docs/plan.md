# Plan — sdd-demo

Only unfinished milestones. Delete a milestone's row and block in the commit that finishes it; git
history is the record. Template: `docs/workflow.md`.

**Next milestone number: M20**

## Milestones at a glance

| Milestone | Description | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M9** Pipeline | `pipeline.py` per DEC-007: extract once per CV, calculate, embed, rank both ways, recommend per pair; `LlmError` recorded per item (DEC-008). | opus | high | open |
| **M10** Workspace views | `workspace_views.py`: lists, job detail, ranked candidates, candidate detail, ranked jobs, failure list. | sonnet | high | open |
| **M11** HTTP API | The `src/api/` package: app factory, routers, response models, 404s, static mount; end-to-end API tests. Installs `fastapi`, `uvicorn`, `httpx`. | sonnet | high | open |
| **M12** Entry point | `main.py` wiring, logging, `127.0.0.1` binding; end-to-end test from fake files and a fake LLM to the API; README setup and run. | sonnet | high | open |
| **M13** Front end shell and lists | `index.html`, theme, `api.js`, list view, sticky header, file names (DEC-019); first headless-browser tests. Installs `playwright`. | sonnet | high | open |
| **M14** Job view | Job text panel and foldable ranked candidate cards with recommendation and attributes (DEC-020). | sonnet | medium | open |
| **M15** Candidate view | Raw CV, attributes and ranked job descriptions. | sonnet | medium | open |
| **M16** Failure and unavailable states | Failure panel, "Not available" values, and "Present" against unknown end (DEC-015). | sonnet | medium | open |
| **M17** Evaluation | `evaluation.py` and `main.py --evaluate` for NFR-004 and NFR-005; `.gitignore` exception so `gold_jobs.json` is committed (DEC-017). | sonnet | high | open |
| **M18** Sample build script | `scripts/build_sample.py` rebuilds `data/sample/` from the raw TalentCLEF files (DEC-010). | sonnet | medium | open |
| **M19** CI workflow | `.github/workflows/check.yml` on `windows-latest`, action versions pinned when built (DEC-018). | sonnet | medium | open |

## Milestones

### M9 — Pipeline

- **Refs:** EXT-001, JOB-001, PRG-003, MIS-002, ERR-001, ERR-002, RNK-001, RNK-002, REC-001, NFR-001, DEC-007, DEC-008.
- **Owner:** `src/pipeline.py`.
- **Tests first:** `test_ext_001_every_cv_is_read_and_extracted`, `test_job_001_every_job_description_is_read`, `test_prg_003_one_extraction_per_cv`, `test_rnk_001_both_rankings_come_from_the_vector_store`, `test_rnk_002_rank_unchanged_by_calculated_attributes`, `test_rec_001_one_recommendation_per_job_cv_pair`, `test_mis_002_failed_extraction_keeps_candidate_in_every_ranking`, `test_err_002_failed_call_recorded_and_other_results_kept`, `test_err_001_failure_cause_names_the_step`, `test_dec_008_non_llm_error_still_stops_the_run`, `test_dec_007_concurrency_stays_within_the_limit`, `test_nfr_001_job_text_and_cv_text_go_only_to_the_llm_client`.
- **Build:** run the start-up steps of DEC-007 with the file reader, LLM client and two vector stores passed in; catch only `LlmError` per item; return the in-memory `Workspace`.
- **Gate:** the checks pass; the only `except` for continuing is the `LlmError` one named in DEC-008.

### M10 — Workspace views

- **Refs:** LST-001, LST-002, JOB-002, JOB-003, CND-001, CND-002, CND-003, RNK-003, REC-001, MIS-001, MIS-002, ERR-001, DEC-015, DEC-020.
- **Owner:** `src/workspace_views.py`.
- **Tests first:** `test_lst_001_job_list_has_id_and_title`, `test_lst_002_candidate_list_has_id_and_name`, `test_job_003_job_detail_has_raw_text`, `test_dec_020_job_detail_unknown_id_raises_not_found`, `test_job_002_ranked_candidates_best_first_with_score`, `test_rnk_003_ranked_candidate_has_extracted_and_calculated_attributes`, `test_rec_001_ranked_candidate_has_recommendation`, `test_cnd_001_candidate_detail_has_raw_text`, `test_cnd_002_candidate_detail_has_attributes`, `test_cnd_003_ranked_jobs_best_first_without_recommendation`, `test_mis_001_missing_value_is_none`, `test_mis_002_candidate_without_facts_stays_in_lists`, `test_dec_015_last_job_has_is_current`, `test_err_001_failure_list_has_item_and_cause`.
- **Build:** one pure function per read, using only `records` and the pure functions of `attributes`.
- **Gate:** the checks pass; the module imports nothing from the API, gateways or pipeline.

### M11 — HTTP API

- **Refs:** LST-001, LST-002, JOB-002, JOB-003, CND-001, CND-002, CND-003, ERR-001, MIS-001, DEC-002, DEC-012, DEC-013, DEC-015, DEC-020.
- **Owner:** `src/api/app.py`, `src/api/jobs.py`, `src/api/candidates.py`, `src/api/status.py`, `src/api/schemas.py`.
- **Tests first:** `test_lst_001_api_lists_job_descriptions`, `test_lst_002_api_lists_candidates`, `test_job_003_api_returns_job_text`, `test_dec_020_api_unknown_job_returns_404_with_detail`, `test_job_002_api_returns_ranked_candidates`, `test_cnd_001_api_returns_raw_cv`, `test_cnd_002_api_returns_attributes`, `test_cnd_003_api_returns_ranked_jobs`, `test_err_001_api_returns_failure_list`, `test_mis_001_api_missing_value_is_null`, `test_dec_015_api_last_job_has_end_and_is_current`, `test_dec_002_health_and_static_front_end_served`.
- **Build:** the app factory over a finished workspace and a web root; one router per domain, each handler calling one `workspace_views` function; response models. Install `fastapi`, `uvicorn`, `httpx`, pin them, run `python scripts/lock.py`.
- **Gate:** the checks pass; end-to-end tests use the framework's test client with a fake workspace; no handler imports a gateway, the pipeline or the domain directly.

### M12 — Entry point

- **Refs:** EXT-001, JOB-001, EXT-002, EXT-003, EXT-004, EXT-006, EXT-007, EXT-008, EXT-009, EXT-010, CAL-001, CAL-002, CAL-003, CAL-004, CAL-005, CAL-007, PRG-003, NFR-002, DEC-007, DEC-013.
- **Owner:** `main.py`.
- **Tests first:** `test_ext_001_start_reads_cvs_and_api_lists_them_end_to_end`, `test_job_001_start_reads_job_descriptions_end_to_end`, `test_ext_002_to_ext_010_candidate_response_has_extracted_attributes_end_to_end`, `test_cal_001_to_cal_007_candidate_response_matches_ex_001_end_to_end`, `test_prg_003_start_extracts_each_cv_once_end_to_end`, `test_dec_013_server_started_with_host_from_settings`, `test_nfr_002_log_file_has_no_api_key`.
- **Build:** load settings, set up logging, create the file reader, LLM client, vector stores and pipeline, run it with today's date, create the app and start the server; no logic in `main.py`. Update `README.md`: What it does, Stack, File structure, Setup (conda environment, `pip install -r requirements.txt`, `config/.env`, the OpenAI key), How to run, How to test.
- **Gate:** the checks pass; the end-to-end tests use a fake file reader and a fake LLM; `README.md` has all six sections.

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
