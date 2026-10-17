// @ts-check
/**
 * @module main
 * The entry point of the page: it connects the modules and shows any unexpected error with its
 * stack trace. It holds no other logic. Implements LST-001, LST-002, JOB-002, JOB-003, CND-001 to CND-003, DEC-002 and DEC-019.
 */

import { createApi } from "./api.js";
import { config } from "./config.js";
import { showCandidate } from "./candidate-view.js";
import { showJob, showJobLoading } from "./job-view.js";
import { ITEM_KINDS, SELECTION_EVENT, showCounts, showLists, watchSelection } from "./list-view.js";
import { createLogger } from "./log.js";

const log = createLogger(/** @type {import("./log.js").LogLevel} */ (config.logLevel));

/**
 * Show an unexpected error and its stack trace on the page, and log it.
 * @param {unknown} error The error or the rejection reason.
 */
function showError(error) {
  const text = error instanceof Error ? `${error.stack}` : String(error);
  log.error(text);
  const panel = document.querySelector("[data-error-panel]");
  if (panel instanceof HTMLElement) {
    panel.textContent = text;
    panel.hidden = false;
  }
}

/**
 * @param {string} id The ID of a template in index.html.
 * @returns {HTMLTemplateElement} The template.
 */
function templateById(id) {
  return /** @type {HTMLTemplateElement} */ (document.querySelector(`#${id}`));
}

/**
 * Load a job and its ranked candidates, and show them unless the user has selected another job.
 * @param {import("./api.js").Api} api The API client.
 * @param {string} id The file name of the selected job description.
 */
async function loadJob(api, id) {
  const view = /** @type {HTMLElement} */ (document.querySelector("[data-view]"));
  view.dataset.selected = id;
  showJobLoading(view);
  const [job, ranked] = await Promise.all([api.getJob(id), api.listRankedCandidates(id)]);
  if (view.dataset.selected === id) {
    const templates = {
      view: templateById("job-view-template"),
      card: templateById("candidate-card-template"),
      fact: templateById("fact-template"),
      stat: templateById("stat-template"),
    };
    showJob(view, templates, { job, ranked });
  }
}

/**
 * Load a candidate and the ranked job descriptions, and show them unless the user has selected
 * another item.
 * @param {import("./api.js").Api} api The API client.
 * @param {string} id The file name of the selected candidate.
 */
async function loadCandidate(api, id) {
  const view = /** @type {HTMLElement} */ (document.querySelector("[data-view]"));
  view.dataset.selected = id;
  showJobLoading(view);
  const [candidate, ranked] = await Promise.all([api.getCandidate(id), api.listRankedJobs(id)]);
  if (view.dataset.selected === id) {
    const templates = {
      view: templateById("candidate-view-template"),
      row: templateById("job-row-template"),
      fact: templateById("fact-template"),
      stat: templateById("stat-template"),
    };
    showCandidate(view, templates, { candidate, ranked });
  }
}

/**
 * Show a job or a candidate when the user selects it.
 * @param {import("./api.js").Api} api The API client.
 * @param {HTMLElement} nav The navigation element, which announces selections.
 */
function watchSelections(api, nav) {
  nav.addEventListener(SELECTION_EVENT, (event) => {
    const { kind, id } = /** @type {CustomEvent<import("./list-view.js").Selection>} */ (event)
      .detail;
    if (kind === ITEM_KINDS.job) {
      loadJob(api, id).catch(showError);
    } else if (kind === ITEM_KINDS.candidate) {
      loadCandidate(api, id).catch(showError);
    }
  });
}

/** Load both lists and show them. */
async function start() {
  const api = createApi(config.api);
  const nav = /** @type {HTMLElement} */ (document.querySelector("[data-nav]"));
  const template = /** @type {HTMLTemplateElement} */ (
    document.querySelector("#nav-item-template")
  );
  const counts = /** @type {HTMLElement} */ (document.querySelector("[data-counts]"));
  const [jobs, candidates] = await Promise.all([api.listJobs(), api.listCandidates()]);
  showLists(nav, template, jobs, candidates);
  showCounts(counts, candidates.length, jobs.length);
  watchSelection(nav);
  watchSelections(api, nav);
  log.info(`Loaded ${jobs.length} job descriptions and ${candidates.length} candidates`);
}

window.addEventListener("error", (event) => showError(event.error ?? event.message));
window.addEventListener("unhandledrejection", (event) => showError(event.reason));
start().catch(showError);
