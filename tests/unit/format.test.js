// @ts-check
/**
 * @module tests/unit/format.test
 * Tests of the display formatting in `src/web/js/format.js`: scores, counts and "Not available".
 */
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  NOT_AVAILABLE,
  formatCounts,
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
