// @ts-check
/**
 * @module failures-view
 * Owns the failure panel: a short message and the list of failed LLM calls with their causes
 * (ERR-001, ERR-002). It shows nothing when no call failed. It does not load data (`api.js`) and
 * does not touch the lists or the views, which stay as they are.
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
 * Show the failed LLM calls, or hide the panel when there are none.
 * @param {HTMLElement} panel The failure panel, with `[data-summary]` and `[data-failure-list]`.
 * @param {HTMLTemplateElement} template The failure list item template.
 * @param {import("./api.js").Failure[]} failures The failed calls.
 */
export function showFailures(panel, template, failures) {
  panel.hidden = failures.length === 0;
  part(panel, "[data-summary]").textContent = `Failure list (${failures.length})`;
  const items = failures.map((failure) => {
    const item = /** @type {DocumentFragment} */ (template.content.cloneNode(true));
    part(item, "[data-item]").textContent = failure.item_id;
    part(item, "[data-cause]").textContent = failure.cause;
    return item;
  });
  part(panel, "[data-failure-list]").replaceChildren(...items);
}
