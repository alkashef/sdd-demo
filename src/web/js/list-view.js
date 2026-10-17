// @ts-check
/**
 * @module list-view
 * Owns the navigation lists and the header counts (LST-001, LST-002, DEC-019). It tells the
 * rest of the page about a selection with a custom event. It does not load data (`api.js`) or
 * show a job or candidate (their own views do).
 */

import { formatCounts } from "./format.js";

/** The name of the event sent when the user selects an item. */
export const SELECTION_EVENT = "item-selected";

/** The two kinds of list item. */
export const ITEM_KINDS = Object.freeze({ job: "job", candidate: "candidate" });

/**
 * @typedef {{ kind: string, id: string }} Selection What the user selected.
 * @typedef {{ id: string, label: string, hint: string }} Entry One list item to show.
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
 * @param {HTMLTemplateElement} template The nav item template.
 * @param {string} kind One of `ITEM_KINDS`.
 * @param {Entry} entry The item to show.
 * @returns {DocumentFragment} A new list item.
 */
function buildItem(template, kind, entry) {
  const item = /** @type {DocumentFragment} */ (template.content.cloneNode(true));
  const button = part(item, ".nav-item");
  part(item, ".nav-item__label").textContent = entry.label;
  part(item, ".nav-item__file").textContent = entry.id;
  button.dataset.kind = kind;
  button.dataset.id = entry.id;
  button.title = entry.hint;
  return item;
}

/**
 * @param {HTMLElement} nav The navigation element.
 * @param {HTMLTemplateElement} template The nav item template.
 * @param {string} listName The `data-list` value to fill.
 * @param {{ kind: string, entries: Entry[] }} content The kind and the items.
 */
function fillList(nav, template, listName, content) {
  const items = content.entries.map((entry) => buildItem(template, content.kind, entry));
  part(nav, `[data-list="${listName}"]`).replaceChildren(...items);
}

/**
 * Fill both lists.
 * @param {HTMLElement} nav The navigation element, with a `data-list` for each kind.
 * @param {HTMLTemplateElement} template The nav item template.
 * @param {import("./api.js").JobSummary[]} jobs The job descriptions.
 * @param {import("./api.js").CandidateSummary[]} candidates The candidates.
 */
export function showLists(nav, template, jobs, candidates) {
  fillList(nav, template, "jobs", {
    kind: ITEM_KINDS.job,
    entries: jobs.map((job) => ({
      id: job.id,
      label: job.title,
      hint: `Show the candidates ranked for ${job.title}`,
    })),
  });
  fillList(nav, template, "candidates", {
    kind: ITEM_KINDS.candidate,
    entries: candidates.map((candidate) => ({
      id: candidate.id,
      label: candidate.name ?? candidate.id,
      hint: `Show the CV of ${candidate.name ?? candidate.id}`,
    })),
  });
}

/**
 * Show how many candidates and job descriptions there are.
 * @param {HTMLElement} element The header counts element.
 * @param {number} candidates How many candidates.
 * @param {number} jobs How many job descriptions.
 */
export function showCounts(element, candidates, jobs) {
  element.textContent = formatCounts(candidates, jobs);
}

/**
 * Mark one item as the selected one.
 * @param {HTMLElement} nav The navigation element.
 * @param {HTMLElement} selected The clicked item.
 */
function markSelected(nav, selected) {
  for (const item of nav.querySelectorAll(".nav-item--selected")) {
    item.classList.remove("nav-item--selected");
    item.removeAttribute("aria-current");
  }
  selected.classList.add("nav-item--selected");
  selected.setAttribute("aria-current", "true");
}

/**
 * Mark the clicked item and announce the selection with a `SELECTION_EVENT` on the navigation.
 * @param {HTMLElement} nav The navigation element.
 */
export function watchSelection(nav) {
  nav.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target.closest(".nav-item") : null;
    if (!(target instanceof HTMLElement)) {
      return;
    }
    markSelected(nav, target);
    /** @type {Selection} */
    const detail = { kind: target.dataset.kind ?? "", id: target.dataset.id ?? "" };
    nav.dispatchEvent(new CustomEvent(SELECTION_EVENT, { bubbles: true, detail }));
  });
}
