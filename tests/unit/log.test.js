// @ts-check
/**
 * @module tests/unit/log.test
 * Tests of the logger in `src/web/js/log.js` with a fake console.
 */
import assert from "node:assert/strict";
import { test } from "node:test";

import { createLogger } from "../../src/web/js/log.js";

/**
 * @param {string} level The level a fake console function records.
 * @param {string[]} seen Where the records go.
 * @returns {(...parts: unknown[]) => void} A fake console function.
 */
function recorder(level, seen) {
  return (...parts) => {
    seen.push(`${level}:${parts.join(" ")}`);
  };
}

test("a logger writes messages at its level and above", () => {
  /** @type {string[]} */
  const seen = [];
  const sink = {
    debug: recorder("debug", seen),
    info: recorder("info", seen),
    warn: recorder("warn", seen),
    error: recorder("error", seen),
  };
  const log = createLogger("warn", sink);

  log.debug("a");
  log.info("b");
  log.warn("c");
  log.error("d");

  assert.deepEqual(seen, ["warn:c", "error:d"]);
});
