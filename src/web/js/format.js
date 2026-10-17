// @ts-check
/**
 * @module format
 * Pure display formatting: scores, list counts and the "Not available" text (MIS-001). It builds
 * no DOM (the view modules do).
 */

export const NOT_AVAILABLE = "Not available";

/**
 * Show a score with two decimals.
 * @param {number | null | undefined} score A similarity score, or a missing one.
 * @returns {string} For example "0.82", or "Not available".
 */
export function formatScore(score) {
  return score === null || score === undefined ? NOT_AVAILABLE : score.toFixed(2);
}

/**
 * Turn a score into the width of its bar.
 * @param {number | null | undefined} score A similarity score, or a missing one.
 * @returns {string} A percentage such as "83%". A missing score gives "0%".
 */
export function scorePercent(score) {
  return `${Math.round((score ?? 0) * 100)}%`;
}

/**
 * Show a value, or "Not available" when it is missing.
 * @param {string | number | null | undefined} value The value from the API.
 * @returns {{ text: string, missing: boolean }} The text, and whether it stands for a missing value.
 */
export function formatValue(value) {
  const missing = value === null || value === undefined || String(value).trim() === "";
  return { text: missing ? NOT_AVAILABLE : String(value), missing };
}

/**
 * @param {number} count How many.
 * @param {string} noun The singular noun.
 * @returns {string} For example "1 candidate" or "3 candidates".
 */
function counted(count, noun) {
  return `${count} ${noun}${count === 1 ? "" : "s"}`;
}

/**
 * Describe the size of both lists for the header.
 * @param {number} candidates How many candidates.
 * @param {number} jobs How many job descriptions.
 * @returns {string} For example "10 candidates · 3 job descriptions".
 */
export function formatCounts(candidates, jobs) {
  return `${counted(candidates, "candidate")} · ${counted(jobs, "job description")}`;
}
