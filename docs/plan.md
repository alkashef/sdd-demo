# Plan — sdd-demo

Only unfinished milestones. Delete a milestone's row and block in the commit that finishes it; git
history is the record. Template: `docs/workflow.md`.

**Next milestone number: M20**

## Milestones at a glance

| Milestone | Description | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| **M1** Lock script and lock check | `scripts/lock.py` writes `constraints.txt`; `check.py` fails if a `requirements.txt` pin is missing from it or differs (DEC-018). | sonnet | medium | open |
| **M2** Records and attribute calculations | `records.py` and `attributes.py`: every CAL rule and the EXT-007 to EXT-009 derivations, proved with EX-001 to EX-004. | sonnet | high | open |
| **M3** Ports, ranking and vector store | `ports.py`, `ranking.py` and the Chroma `vector_store.py`: similarity order, unscored items last. Installs `chromadb`. | sonnet | high | open |
| **M4** File reader | `file_reader.py` reads CVs, job descriptions, prompt files and evaluation files; a missing folder or file stops with a clear message. | sonnet | medium | open |
| **M5** Prompt data and CV extraction | `prompt_data.py`, the CV-facts schema, `extraction.py` and `prompts/extract_cv.md`. Installs `pydantic`. | sonnet | high | open |
| **M6** Recommendation | `recommendation.py`, the recommendation schema and `prompts/match_cv_to_job.md`; the request carries no name or address. | sonnet | medium | open |
| **M7** Settings | `config.py`, `config/.env.example` and `config/.env` with every key in design 2.3; a missing value fails at start-up. | sonnet | medium | open |
| **M8** LLM client | `llm_client.py`: structured completion and embedding through the OpenAI SDK; failures become `LlmError`. Installs `openai`. | sonnet | high | open |
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

### M1 — Lock script and lock check

- **Refs:** DEC-018, DEC-001.
- **Owner:** `scripts/lock.py` and `scripts/check.py`.
- **Tests first:** `test_dec_018_lock_check_passes_when_pins_match`, `test_dec_018_lock_check_fails_when_pin_missing`, `test_dec_018_lock_check_fails_when_version_differs`, `test_dec_018_lock_writes_freeze_output_to_constraints` (fake freeze runner).
- **Build:** `lock.py` wraps `pip freeze` and writes `constraints.txt`; `check.py` gains the check that every `requirements.txt` pin appears in `constraints.txt` with the same version. Run `lock.py` once in the `sdd-demo` environment and commit `constraints.txt`.
- **Gate:** the checks in `CLAUDE.md` pass; `constraints.txt` exists and matches `requirements.txt`.

### M2 — Records and attribute calculations

- **Refs:** CAL-001, CAL-002, CAL-003, CAL-004, CAL-005, CAL-007, CAL-008, CAL-009, CAL-010, EXT-007, EXT-008, EXT-009, MIS-001, EX-001 to EX-004, DEC-005, DEC-015, design section 3.
- **Owner:** `src/records.py`, `src/attributes.py` (and `src/__init__.py`).
- **Tests first:** `test_cal_001_total_employment_period_ex_001`, `test_cal_002_job_count_ex_001`, `test_cal_003_average_time_per_job_ex_001`, `test_cal_004_no_gap_ex_001`, `test_cal_004_gap_between_jobs`, `test_cal_005_months_since_graduation_ex_002`, `test_cal_007_currently_employed_ex_001`, `test_cal_008_present_is_current_month_and_both_months_counted`, `test_cal_009_unknown_end_gives_not_available_ex_003`, `test_cal_010_bad_job_dates_ex_004`, `test_cal_010_future_graduation_ex_004`, `test_ext_007_distinct_job_countries`, `test_ext_008_distinct_employers`, `test_ext_009_last_job_is_latest_start`, `test_mis_001_missing_values_stay_none`.
- **Build:** the frozen records in design section 3, and the pure calculations and list derivations, with the date passed in.
- **Gate:** all examples EX-001 to EX-004 pass as tests; the checks in `CLAUDE.md` pass.

### M3 — Ports, ranking and vector store

- **Refs:** RNK-001, JOB-002, CND-003, MIS-002, DEC-004, DEC-011, design section 4 (ports).
- **Owner:** `src/ports.py`, `src/ranking.py`, `src/vector_store.py`.
- **Tests first:** `test_rnk_001_nearest_returns_items_by_cosine_similarity`, `test_job_002_all_cvs_returned_best_first_ties_by_file_name`, `test_cnd_003_all_jobs_returned_best_first`, `test_mis_002_item_without_vector_ranked_last_by_id`, `test_dec_004_chroma_telemetry_off`.
- **Build:** the three protocols and the `LlmError` types; `ranking` appends unscored items by ID; `vector_store` adds vectors by ID and returns every item as (ID, similarity) with in-memory Chroma. Install `chromadb` into `sdd-demo`, pin it in `requirements.txt`, run `python scripts/lock.py`.
- **Gate:** the checks pass with `chromadb` installed. If the install or the checks fail, set Status to `blocked` (DEC-011, design section 5).

### M4 — File reader

- **Refs:** EXT-001, JOB-001, DEC-009, DEC-017 (reading only).
- **Owner:** `src/file_reader.py`.
- **Tests first:** `test_ext_001_reads_each_cv_file_in_folder`, `test_job_001_reads_each_job_description_file_in_folder`, `test_ext_001_missing_folder_stops_with_clear_message`, `test_dec_017_reads_prompt_and_evaluation_files_as_text`.
- **Build:** read plain-text files from a folder into `Document` records (ID = file name, sorted by name); read one prompt file or evaluation file as text; fail clearly on a missing path.
- **Gate:** the tests use temporary folders and invented data only; the checks pass.

### M5 — Prompt data and CV extraction

- **Refs:** EXT-002, EXT-003, EXT-004, EXT-006, EXT-009, EXT-010, MIS-001, NFR-001, DEC-005, DEC-011, DEC-015, DEC-016.
- **Owner:** `src/prompt_data.py`, `src/llm_schemas.py` (CV facts), `src/extraction.py`, `prompts/extract_cv.md`.
- **Tests first:** `test_ext_002_name_extracted`, `test_ext_003_current_title_extracted`, `test_ext_004_skills_extracted`, `test_ext_006_city_and_country_extracted`, `test_ext_009_last_job_fields_extracted`, `test_ext_010_highest_degree_extracted`, `test_mis_001_null_fields_become_none`, `test_dec_015_current_job_with_end_refused_as_output_error`, `test_dec_016_system_text_is_prompt_and_user_text_is_tagged_cv`, `test_dec_016_injected_closing_tag_is_escaped`, `test_dec_016_placeholder_marker_in_cv_stays_unchanged`.
- **Build:** tag-wrap with escaping (tag names an enum); the `pydantic` reply model with `YYYY-MM` dates and `is_current` per job; the extraction user text and the reply-to-`CvFacts` mapping; the system prompt file (year-only end is `null`, tagged content is untrusted data). Install `pydantic`, pin it, run `python scripts/lock.py`.
- **Gate:** the checks pass; the prompt file has no placeholders.

### M6 — Recommendation

- **Refs:** REC-001, NFR-001, DEC-006, DEC-016.
- **Owner:** `src/recommendation.py`, `src/llm_schemas.py` (recommendation), `prompts/match_cv_to_job.md`.
- **Tests first:** `test_rec_001_reply_becomes_interview_flag_and_reason`, `test_rec_001_facts_carry_is_current_beside_end`, `test_dec_006_request_has_no_name_or_address`, `test_dec_016_user_text_has_tagged_job_description_and_json_facts`, `test_dec_016_injected_closing_tag_is_escaped_in_job_description`.
- **Build:** build the user text from the job description and the candidate facts without name or address; map the validated reply to a `Recommendation`; write the system prompt file.
- **Gate:** the checks pass; no CV name or address appears in any recommendation request in the tests.

### M7 — Settings

- **Refs:** NFR-002, DEC-013, DEC-003, design section 2.3.
- **Owner:** `src/config.py`, `config/.env.example`, `config/.env`.
- **Tests first:** `test_nfr_002_api_key_not_in_settings_repr`, `test_design_2_3_missing_value_fails_clearly`, `test_design_2_3_invalid_number_fails_clearly`, `test_design_2_3_environment_overrides_env_file`, `test_design_2_3_env_example_lists_every_setting`, `test_dec_013_env_example_host_is_127_0_0_1`.
- **Build:** frozen typed settings objects grouped per component, loaded with `python-dotenv` from a path passed in; no defaults in code; add every key of design section 2.3 to `.env.example` with its default (secret empty) and to the local `config/.env`.
- **Gate:** the checks pass; `config/.env` is not committed; the settings table in `docs/design.md` matches the keys.

### M8 — LLM client

- **Refs:** NFR-001, NFR-002, ERR-001, DEC-003, DEC-011.
- **Owner:** `src/llm_client.py`.
- **Tests first:** `test_err_001_provider_failure_raises_llm_error_naming_cause`, `test_err_001_rejected_request_raises_llm_error`, `test_dec_011_refusal_raises_llm_output_error_with_raw_output`, `test_nfr_002_api_key_not_in_error_or_log`, `test_nfr_001_complete_sends_only_given_system_and_user_text`, `test_dec_003_embed_returns_vector`, `test_dec_003_model_timeout_and_token_limit_come_from_settings`.
- **Build:** implement `StructuredCompleter` and `Embedder` over the async OpenAI SDK, with a fake SDK client in tests; map every provider failure to `LlmError`. Install `openai`, pin it, run `python scripts/lock.py`.
- **Gate:** the checks pass; no test calls the real service. The model IDs stay untested until the user's first manual run (DEC-003).

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
