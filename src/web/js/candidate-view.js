// @ts-check
/**
 * @module candidate-view
 * Owns the candidate view: the heading, the raw CV beside the attribute cards, and the ranked job
 * descriptions without a recommendation (CND-001, CND-002, CND-003, DEC-019). It does not load data
 * (`api.js`) and fills the attribute parts with `attribute-fill.js`.
 */

import { fillAttributes } from "./attribute-fill.js";
import { formatScore, scorePercent } from "./format.js";

/**
 * @typedef {{
 *   view: HTMLTemplateElement,
 *   row: HTMLTemplateElement,
 *   fact: HTMLTemplateElement,
 *   stat: HTMLTemplateElement,
 * }} CandidateViewTemplates The templates the candidate view clones.
 */

/**
 * @param {ParentNode} parent Where to look.
 * @param {string} selector What to find.
 * @returns {HTMLElement} The first match.
 */
function part(parent, selector) {
  const found = parent.querySelector(selector);
  if (!(found instanceof HTMLElement)) {
    throw new Error(`Missing ${selector} in index.html`);
  }
  return found;
}

/**
 * @param {HTMLTemplateElement} template The job row template.
 * @param {import("./api.js").RankedJob} job The job description to show.
 * @param {number} rank The place in the ranking, from 1.
 * @returns {DocumentFragment} A new row.
 */
function buildRow(template, job, rank) {
  const fragment = /** @type {DocumentFragment} */ (template.content.cloneNode(true));
  part(fragment, "[data-rank]").textContent = String(rank);
  part(fragment, "[data-title]").textContent = job.title;
  part(fragment, "[data-file]").textContent = job.id;
  part(fragment, "[data-score]").textContent = formatScore(job.score);
  part(fragment, "[data-bar]").style.setProperty("--score", scorePercent(job.score));
  return fragment;
}

/**
 * Show a candidate and the ranked job descriptions in the view.
 * @param {HTMLElement} view The element to fill.
 * @param {CandidateViewTemplates} templates The templates.
 * @param {{ candidate: import("./api.js").CandidateDetail, ranked: import("./api.js").RankedJob[] }} data
 *   The candidate and the job descriptions, best match first.
 */
export function showCandidate(view, templates, data) {
  const { candidate, ranked } = data;
  const fragment = /** @type {DocumentFragment} */ (templates.view.content.cloneNode(true));
  part(fragment, "[data-title]").textContent = candidate.name ?? candidate.id;
  part(fragment, "[data-file]").textContent = candidate.id;
  part(fragment, "[data-meta]").textContent = candidate.extracted?.current_title ?? "";
  part(fragment, "[data-cv-text]").textContent = candidate.text;
  fillAttributes(fragment, templates, candidate.extracted, candidate.calculated);
  part(fragment, "[data-jobs]").replaceChildren(
    ...ranked.map((job, index) => buildRow(templates.row, job, index + 1)),
  );
  view.replaceChildren(fragment);
  view.removeAttribute("aria-busy");
}
