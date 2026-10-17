// @ts-check
/**
 * @module api
 * The only module that calls `fetch`. It reads the JSON API (design section 4) and adds context
 * to a failure. It does not show anything (the view modules do) and keeps no data.
 */

/**
 * @typedef {{ id: string, title: string }} JobSummary A job description in the list (LST-001).
 * @typedef {{ id: string, name: string | null }} CandidateSummary A candidate in the list (LST-002).
 * @typedef {{ id: string, title: string, text: string }} JobDetail A job description with its raw
 *   text (JOB-003).
 * @typedef {import("./format.js").LastJob} LastJob The last job of a candidate (DEC-015).
 * @typedef {{
 *   name: string | null,
 *   current_title: string | null,
 *   skills: string[],
 *   city: string | null,
 *   country: string | null,
 *   highest_degree: string | null,
 *   countries: string[],
 *   employers: string[],
 *   last_job: LastJob | null,
 * }} ExtractedAttributes The extracted attributes of a candidate (RNK-003).
 * @typedef {{
 *   total_months: number | null,
 *   job_count: number | null,
 *   average_job_months: number | null,
 *   gaps: number[] | null,
 *   months_since_graduation: number | null,
 *   currently_employed: boolean | null,
 * }} CalculatedAttributes The calculated attributes of a candidate (RNK-003).
 * @typedef {{ interview: boolean, reason: string }} Recommendation The LLM advice (REC-001).
 * @typedef {{
 *   id: string,
 *   name: string | null,
 *   score: number | null,
 *   recommendation: Recommendation | null,
 *   extracted: ExtractedAttributes | null,
 *   calculated: CalculatedAttributes | null,
 * }} RankedCandidate A candidate in the ranking of one job description (JOB-002).
 * @typedef {{
 *   id: string,
 *   name: string | null,
 *   text: string,
 *   extracted: ExtractedAttributes | null,
 *   calculated: CalculatedAttributes | null,
 * }} CandidateDetail A candidate with the raw CV and the attributes (CND-001, CND-002).
 * @typedef {{ item_id: string, cause: string }} Failure A failed LLM call (ERR-001).
 * @typedef {{ id: string, title: string, score: number | null }} RankedJob A job description in
 *   the ranking of one candidate, without a recommendation (CND-003).
 * @typedef {{ jobs: string, candidates: string, rankedCandidates: string, rankedJobs: string,
 *   failures: string }}
 *   ApiPaths The paths of the endpoints. `rankedCandidates` is the segment that follows a job
 *   path, `rankedJobs` the one that follows a candidate path.
 * @typedef {{
 *   listJobs: () => Promise<JobSummary[]>,
 *   listCandidates: () => Promise<CandidateSummary[]>,
 *   getJob: (jobId: string) => Promise<JobDetail>,
 *   listRankedCandidates: (jobId: string) => Promise<RankedCandidate[]>,
 *   getCandidate: (candidateId: string) => Promise<CandidateDetail>,
 *   listRankedJobs: (candidateId: string) => Promise<RankedJob[]>,
 *   listFailures: () => Promise<Failure[]>,
 * }} Api
 */

/**
 * @param {string} base The path of a collection.
 * @param {string} id The file name of one item.
 * @returns {string} The path of that item.
 */
function itemPath(base, id) {
  return `${base}/${encodeURIComponent(id)}`;
}

/**
 * Get one JSON document.
 * @template T
 * @param {typeof fetch} fetchFn The function that sends a request.
 * @param {string} path The endpoint path.
 * @returns {Promise<T>} The parsed body.
 */
async function getJson(fetchFn, path) {
  try {
    const response = await fetchFn(path);
    if (!response.ok) {
      throw new Error(`GET ${path} answered ${response.status}`);
    }
    return /** @type {T} */ (await response.json());
  } catch (error) {
    throw new Error(`Could not load ${path}`, { cause: error });
  }
}

/**
 * Create the API client.
 * @param {ApiPaths} paths The path of each endpoint.
 * @param {typeof fetch} fetchFn The function that sends a request.
 * @returns {Api} One function per endpoint.
 */
export function createApi(paths, fetchFn = fetch) {
  /**
   * @template T
   * @param {string} path The endpoint path.
   * @returns {Promise<T>} The parsed body.
   */
  const get = (path) => getJson(fetchFn, path);
  /** @type {(id: string) => string} */
  const job = (id) => itemPath(paths.jobs, id);
  /** @type {(id: string) => string} */
  const candidate = (id) => itemPath(paths.candidates, id);
  return {
    listJobs: () => get(paths.jobs),
    listCandidates: () => get(paths.candidates),
    getJob: (jobId) => get(job(jobId)),
    listRankedCandidates: (jobId) => get(`${job(jobId)}/${paths.rankedCandidates}`),
    getCandidate: (candidateId) => get(candidate(candidateId)),
    listRankedJobs: (candidateId) => get(`${candidate(candidateId)}/${paths.rankedJobs}`),
    listFailures: () => get(paths.failures),
  };
}
