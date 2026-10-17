// @ts-check
/**
 * @module tests/unit/format.test
 * Tests of the display formatting in `src/web/js/format.js`: scores, counts and "Not available".
 */
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  NOT_AVAILABLE,
  formatAverageMonths,
  formatCounts,
  formatGaps,
  formatLastJob,
  formatLocation,
  formatMonths,
  formatYesNo,
  formatScore,
  formatValue,
  scorePercent,
} from "../../src/web/js/format.js";

test("formatScore shows two decimals", () => {
  assert.equal(formatScore(0.8), "0.80");
  assert.equal(formatScore(0.8249), "0.82");
});

test("formatScore shows Not available for a missing score", () => {
  assert.equal(formatScore(null), NOT_AVAILABLE);
});

test("scorePercent turns a score into a percentage for the bar", () => {
  assert.equal(scorePercent(0.826), "83%");
  assert.equal(scorePercent(null), "0%");
});

test("formatValue shows Not available for null, undefined and blank text", () => {
  assert.deepEqual(formatValue(null), { text: NOT_AVAILABLE, missing: true });
  assert.deepEqual(formatValue(undefined), { text: NOT_AVAILABLE, missing: true });
  assert.deepEqual(formatValue("  "), { text: NOT_AVAILABLE, missing: true });
});

test("formatValue keeps a present value, including zero", () => {
  assert.deepEqual(formatValue("Cairo"), { text: "Cairo", missing: false });
  assert.deepEqual(formatValue(0), { text: "0", missing: false });
});

test("formatCounts names both lists and uses the singular for one", () => {
  assert.equal(formatCounts(10, 3), "10 candidates · 3 job descriptions");
  assert.equal(formatCounts(1, 1), "1 candidate · 1 job description");
});

test("formatMonths and formatAverageMonths show months or nothing", () => {
  assert.equal(formatMonths(106), "106 mo");
  assert.equal(formatMonths(null), null);
  assert.equal(formatAverageMonths(35.33), "35.3 mo");
  assert.equal(formatAverageMonths(null), null);
});

test("formatGaps shows none, the gaps, or nothing", () => {
  assert.equal(formatGaps([]), "None (0 mo)");
  assert.equal(formatGaps([6, 3]), "6 mo, 3 mo");
  assert.equal(formatGaps(null), null);
});

test("formatYesNo maps a boolean and keeps unknown missing", () => {
  assert.equal(formatYesNo(true), "Yes");
  assert.equal(formatYesNo(false), "No");
  assert.equal(formatYesNo(null), null);
});

test("formatLocation joins the parts that exist", () => {
  assert.equal(formatLocation("Cairo", "Egypt"), "Cairo, Egypt");
  assert.equal(formatLocation(null, "Egypt"), "Egypt");
  assert.equal(formatLocation(null, null), null);
});

test("formatLastJob shows Present only for a current job and Not available for unknown end", () => {
  const start = { year: 2019, month: 6 };
  const base = { title: "Analyst", employer: "Acme", start, end: null };
  assert.equal(formatLastJob({ ...base, is_current: true }), "Acme · Analyst · Jun 2019 – Present");
  assert.equal(
    formatLastJob({ ...base, is_current: false }),
    "Acme · Analyst · Jun 2019 – Not available",
  );
  assert.equal(
    formatLastJob({ ...base, is_current: false, end: { year: 2021, month: 12 } }),
    "Acme · Analyst · Jun 2019 – Dec 2021",
  );
  assert.equal(formatLastJob(null), null);
});
