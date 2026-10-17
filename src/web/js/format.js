// @ts-check
/**
 * @module format
 * Pure display formatting: scores, list counts, attribute values and the "Not available" text
 * (MIS-001, DEC-015). A formatter returns `null` for a missing value, which `formatValue` turns
 * into "Not available". It builds no DOM (the view modules do).
 */

const MONTH_NAMES = Object.freeze([
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
]);

/**
 * @typedef {{ year: number, month: number }} YearMonth A calendar month from the API.
 * @typedef {{
 *   title: string | null,
 *   employer: string | null,
 *   start: YearMonth | null,
 *   end: YearMonth | null,
 *   is_current: boolean,
 * }} LastJob The part of a job that the display needs.
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

/**
 * @param {number | null | undefined} months A number of months, or a missing one.
 * @returns {string | null} For example "106 mo", or `null` when missing.
 */
export function formatMonths(months) {
  return months === null || months === undefined ? null : `${months} mo`;
}

/**
 * @param {number | null | undefined} months An average in months, or a missing one.
 * @returns {string | null} For example "35.3 mo", or `null` when missing.
 */
export function formatAverageMonths(months) {
  return months === null || months === undefined ? null : `${months.toFixed(1)} mo`;
}

/**
 * @param {number[] | null | undefined} gaps The length in months of each gap, or a missing list.
 * @returns {string | null} "None (0 mo)", "6 mo, 3 mo", or `null` when the gaps are unknown.
 */
export function formatGaps(gaps) {
  if (gaps === null || gaps === undefined) {
    return null;
  }
  return gaps.length === 0 ? "None (0 mo)" : gaps.map((gap) => `${gap} mo`).join(", ");
}

/**
 * @param {boolean | null | undefined} flag A yes or no value, or a missing one.
 * @returns {string | null} "Yes", "No", or `null` when unknown.
 */
export function formatYesNo(flag) {
  if (flag === null || flag === undefined) {
    return null;
  }
  return flag ? "Yes" : "No";
}

/**
 * @param {string | null | undefined} city The city, or a missing one.
 * @param {string | null | undefined} country The country, or a missing one.
 * @returns {string | null} For example "Cairo, Egypt", or `null` when both are missing.
 */
export function formatLocation(city, country) {
  const parts = [city, country].filter(
    (part) => part !== null && part !== undefined && part !== "",
  );
  return parts.length === 0 ? null : parts.join(", ");
}

/**
 * @param {YearMonth | null} month A calendar month, or a missing one.
 * @returns {string} For example "Jun 2019", or "Not available".
 */
function formatMonth(month) {
  return month ? `${MONTH_NAMES[month.month - 1]} ${month.year}` : NOT_AVAILABLE;
}

/**
 * @param {LastJob} job The job.
 * @returns {string} The end month, "Present" for a current job, or "Not available" (DEC-015).
 */
function formatEnd(job) {
  if (job.end) {
    return formatMonth(job.end);
  }
  return job.is_current ? "Present" : NOT_AVAILABLE;
}

/**
 * Describe the last job on one line.
 * @param {LastJob | null | undefined} job The last job, or a missing one.
 * @returns {string | null} For example "Acme · Analyst · Jun 2019 – Present", or `null`.
 */
export function formatLastJob(job) {
  if (!job) {
    return null;
  }
  const range = `${formatMonth(job.start)} – ${formatEnd(job)}`;
  return [job.employer, job.title, range].filter((part) => part).join(" · ");
}
