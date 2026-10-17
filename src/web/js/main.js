// @ts-check
/**
 * @module main
 * The entry point of the page: it connects the modules and shows any unexpected error with its
 * stack trace. It holds no other logic. Implements LST-001, LST-002, JOB-002, JOB-003, DEC-002 and DEC-019.
 */

import { createApi } from "./api.js";
import { config } from "./config.js";
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
 * Show a job and its ranked candidates when the user selects a job description.
 * @param {import("./api.js").Api} api The API client.
 * @param {HTMLElement} nav The navigation element, which announces selections.
 */
function watchJobs(api, nav) {
  nav.addEventListener(SELECTION_EVENT, (event) => {
    const { kind, id } = /** @type {CustomEvent<import("./list-view.js").Selection>} */ (event)
      .detail;
    if (kind === ITEM_KINDS.job) {
      loadJob(api, id).catch(showError);
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
  watchJobs(api, nav);
  log.info(`Loaded ${jobs.length} job descriptions and ${candidates.length} candidates`);
}

window.addEventListener("error", (event) => showError(event.error ?? event.message));
window.addEventListener("unhandledrejection", (event) => showError(event.reason));
start().catch(showError);
