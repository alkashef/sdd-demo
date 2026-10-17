// @ts-check
/**
 * @module attribute-fill
 * Fills the attribute parts of a candidate card: the six extracted facts, the skill chips and the
 * six calculated attributes (RNK-003, MIS-001). The job view and the candidate view share it. It
 * loads no data and decides nothing about the rest of the card.
 */

import {
  formatAverageMonths,
  formatGaps,
  formatLastJob,
  formatLocation,
  formatMonths,
  formatValue,
  formatYesNo,
} from "./format.js";

/** @typedef {{ label: string, value: string | number | null }} Row One label and its value. */

/**
 * @param {string[] | undefined} items A list from the API, or none.
 * @returns {string | null} The items joined by commas, or `null` for an empty list.
 */
function joined(items) {
  return items && items.length > 0 ? items.join(", ") : null;
}

/**
 * @param {import("./api.js").ExtractedAttributes | null} extracted The facts, or none.
 * @returns {import("./api.js").ExtractedAttributes} The facts, or an empty set of them.
 */
function orEmpty(extracted) {
  return (
    extracted ?? {
      name: null,
      current_title: null,
      skills: [],
      city: null,
      country: null,
      highest_degree: null,
      countries: [],
      employers: [],
      last_job: null,
    }
  );
}

/**
 * @param {import("./api.js").ExtractedAttributes | null} extracted The facts, or none.
 * @returns {Row[]} The six extracted facts in display order.
 */
export function factRows(extracted) {
  const facts = orEmpty(extracted);
  return [
    { label: "Current title", value: facts.current_title },
    { label: "Location", value: formatLocation(facts.city, facts.country) },
    { label: "Highest degree", value: facts.highest_degree },
    { label: "Last job", value: formatLastJob(facts.last_job) },
    { label: "Countries worked", value: joined(facts.countries) },
    { label: "Companies", value: joined(facts.employers) },
  ];
}

/**
 * @param {import("./api.js").CalculatedAttributes | null} calculated The attributes, or none.
 * @returns {Row[]} The six calculated attributes in display order.
 */
export function statRows(calculated) {
  return [
    { label: "Total employment", value: formatMonths(calculated?.total_months) },
    { label: "Jobs held", value: calculated?.job_count ?? null },
    { label: "Average per job", value: formatAverageMonths(calculated?.average_job_months) },
    { label: "Employment gaps", value: formatGaps(calculated?.gaps) },
    { label: "Since graduation", value: formatMonths(calculated?.months_since_graduation) },
    { label: "Employed now", value: formatYesNo(calculated?.currently_employed) },
  ];
}

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
 * Show one row from a template with a `[data-label]` and a `[data-value]`.
 * @param {HTMLTemplateElement} template The fact or stat template.
 * @param {Row} row The label and the value.
 * @returns {DocumentFragment} The filled row.
 */
function buildRow(template, row) {
  const fragment = /** @type {DocumentFragment} */ (template.content.cloneNode(true));
  const { text, missing } = formatValue(row.value);
  part(fragment, "[data-label]").textContent = row.label;
  const value = part(fragment, "[data-value]");
  value.textContent = text;
  value.classList.toggle("not-available", missing);
  return fragment;
}

/**
 * Fill a card's facts, chips and stats.
 * @param {ParentNode} card The card element.
 * @param {{ fact: HTMLTemplateElement, stat: HTMLTemplateElement }} templates The row templates.
 * @param {import("./api.js").ExtractedAttributes | null} extracted The extracted attributes.
 * @param {import("./api.js").CalculatedAttributes | null} calculated The calculated attributes.
 */
export function fillAttributes(card, templates, extracted, calculated) {
  part(card, "[data-facts]").replaceChildren(
    ...factRows(extracted).map((row) => buildRow(templates.fact, row)),
  );
  part(card, "[data-stats]").replaceChildren(
    ...statRows(calculated).map((row) => buildRow(templates.stat, row)),
  );
  const chips = orEmpty(extracted).skills.map((skill) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = skill;
    return chip;
  });
  part(card, "[data-chips]").replaceChildren(...chips);
}
