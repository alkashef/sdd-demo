// @ts-check
/**
 * @module tests/unit/api.test
 * Tests of the API client in `src/web/js/api.js` with a fake `fetch`.
 */
import assert from "node:assert/strict";
import { test } from "node:test";

import { createApi } from "../../src/web/js/api.js";

const paths = {
  jobs: "/api/jobs",
  candidates: "/api/candidates",
  rankedCandidates: "ranked-candidates",
};

/**
 * @param {number} status The HTTP status to answer.
 * @param {unknown} body The JSON body to answer.
 * @returns {typeof fetch} A fake `fetch` that answers one response.
 */
function fakeFetch(status, body) {
  return async () => new Response(JSON.stringify(body), { status });
}

test("lst_001 listJobs returns the parsed job list", async () => {
  const jobs = [{ id: "j1.txt", title: "Data Analyst" }];
  assert.deepEqual(await createApi(paths, fakeFetch(200, jobs)).listJobs(), jobs);
});

test("lst_002 listCandidates asks for the candidate path and returns the list", async () => {
  /** @type {string[]} */
  const asked = [];
  /** @type {typeof fetch} */
  const recording = async (input) => {
    asked.push(String(input));
    return new Response("[]");
  };
  assert.deepEqual(await createApi(paths, recording).listCandidates(), []);
  assert.deepEqual(asked, ["/api/candidates"]);
});

test("an error status becomes an error that names the path and keeps its cause", async () => {
  await assert.rejects(createApi(paths, fakeFetch(500, {})).listJobs(), (error) => {
    assert.ok(error instanceof Error);
    assert.equal(error.message, "Could not load /api/jobs");
    assert.match(String(error.cause), /GET \/api\/jobs answered 500/);
    return true;
  });
});

test("job_003 getJob asks for the job path and returns the document", async () => {
  /** @type {string[]} */
  const asked = [];
  /** @type {typeof fetch} */
  const recording = async (input) => {
    asked.push(String(input));
    return new Response(JSON.stringify({ id: "a b.txt", title: "T", text: "X" }));
  };
  assert.deepEqual(await createApi(paths, recording).getJob("a b.txt"), {
    id: "a b.txt",
    title: "T",
    text: "X",
  });
  assert.deepEqual(asked, ["/api/jobs/a%20b.txt"]);
});

test("job_002 listRankedCandidates asks for the ranking path and returns the list", async () => {
  /** @type {string[]} */
  const asked = [];
  /** @type {typeof fetch} */
  const recording = async (input) => {
    asked.push(String(input));
    return new Response("[]");
  };
  assert.deepEqual(await createApi(paths, recording).listRankedCandidates("j1.txt"), []);
  assert.deepEqual(asked, ["/api/jobs/j1.txt/ranked-candidates"]);
});
