// @ts-check
/**
 * @module job-view
 * Owns the job view: the heading, the "Job description text" panel and one foldable card per
 * ranked candidate (JOB-002, JOB-003, RNK-003, REC-001, ERR-002, DEC-019, DEC-020). It does not load data
 * (`api.js`) and fills the attribute parts with `attribute-fill.js`.
 */

import { fillAttributes } from "./attribute-fill.js";
import { NOT_AVAILABLE, formatScore, scorePercent } from "./format.js";

/**
 * @typedef {{
 *   view: HTMLTemplateElement,
 *   card: HTMLTemplateElement,
 *   fact: HTMLTemplateElement,
 *   stat: HTMLTemplateElement,
 * }} JobViewTemplates The templates the job view clones.
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
 * @param {HTMLElement} row The recommendation row.
 */
function showUnavailableRecommendation(row) {
  const pill = part(row, "[data-pill]");
  pill.classList.add("pill--unavailable");
  part(pill, "[data-pill-label]").textContent = NOT_AVAILABLE;
  pill.querySelectorAll("svg").forEach((icon) => icon.remove());
  part(row, "[data-reason]").textContent = "The recommendation could not be generated.";
}

/**
 * Show the recommendation row: the pill and the reason (REC-001). A missing recommendation shows
 * the grey "Not available" pill (ERR-002).
 * @param {HTMLElement} card The card element.
 * @param {import("./api.js").Recommendation | null} recommendation The advice, or none.
 */
function fillRecommendation(card, recommendation) {
  const row = part(card, "[data-recommendation]");
  if (recommendation === null) {
    showUnavailableRecommendation(row);
    return;
  }
  const kind = recommendation.interview ? "interview" : "skip";
  const pill = part(row, "[data-pill]");
  pill.classList.add(`pill--${kind}`);
  part(pill, "[data-pill-label]").textContent = recommendation.interview ? "Interview" : "Skip";
  pill.querySelector(`[data-icon='${recommendation.interview ? "skip" : "interview"}']`)?.remove();
  part(row, "[data-reason]").textContent = recommendation.reason;
}

/**
 * @param {JobViewTemplates} templates The templates.
 * @param {import("./api.js").RankedCandidate} candidate The candidate to show.
 * @param {number} rank The place in the ranking, from 1.
 * @returns {DocumentFragment} A new card.
 */
function buildCard(templates, candidate, rank) {
  const fragment = /** @type {DocumentFragment} */ (templates.card.content.cloneNode(true));
  part(fragment, "[data-rank]").textContent = String(rank);
  part(fragment, "[data-name]").textContent = candidate.name ?? candidate.id;
  part(fragment, "[data-file]").textContent = candidate.id;
  part(fragment, "[data-score]").textContent = formatScore(candidate.score);
  part(fragment, "[data-bar]").style.setProperty("--score", scorePercent(candidate.score));
  fillRecommendation(part(fragment, ".candidate-card"), candidate.recommendation);
  fillAttributes(fragment, templates, candidate.extracted, candidate.calculated);
  return fragment;
}

/**
 * Show a job and its ranked candidates in the view.
 * @param {HTMLElement} view The element to fill.
 * @param {JobViewTemplates} templates The templates.
 * @param {{ job: import("./api.js").JobDetail, ranked: import("./api.js").RankedCandidate[] }} data
 *   The job and its candidates, best match first.
 */
export function showJob(view, templates, data) {
  const fragment = /** @type {DocumentFragment} */ (templates.view.content.cloneNode(true));
  part(fragment, "[data-title]").textContent = data.job.title;
  part(fragment, "[data-file]").textContent = data.job.id;
  part(fragment, "[data-meta]").textContent =
    `All ${data.ranked.length} candidates, best match first.`;
  part(fragment, "[data-text]").textContent = data.job.text;
  part(fragment, "[data-cards]").replaceChildren(
    ...data.ranked.map((candidate, index) => buildCard(templates, candidate, index + 1)),
  );
  view.replaceChildren(fragment);
  view.removeAttribute("aria-busy");
}

/**
 * Show that a job is loading.
 * @param {HTMLElement} view The element to fill.
 */
export function showJobLoading(view) {
  const note = document.createElement("p");
  note.className = "main__hint";
  note.textContent = "Loading…";
  view.replaceChildren(note);
  view.setAttribute("aria-busy", "true");
}
