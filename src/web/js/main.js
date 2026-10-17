// @ts-check
/**
 * @module main
 * The entry point of the page: it connects the modules and shows any unexpected error with its
 * stack trace. It holds no other logic. Implements LST-001, LST-002, DEC-002 and DEC-019.
 */

import { createApi } from "./api.js";
import { config } from "./config.js";
import { showCounts, showLists, watchSelection } from "./list-view.js";
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
  log.info(`Loaded ${jobs.length} job descriptions and ${candidates.length} candidates`);
}

window.addEventListener("error", (event) => showError(event.error ?? event.message));
window.addEventListener("unhandledrejection", (event) => showError(event.reason));
start().catch(showError);
