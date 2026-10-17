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
 * @typedef {{ jobs: string, candidates: string, rankedCandidates: string }} ApiPaths The paths of
 *   the endpoints. `rankedCandidates` is the segment that follows a job path.
 * @typedef {{
 *   listJobs: () => Promise<JobSummary[]>,
 *   listCandidates: () => Promise<CandidateSummary[]>,
 *   getJob: (jobId: string) => Promise<JobDetail>,
 *   listRankedCandidates: (jobId: string) => Promise<RankedCandidate[]>,
 * }} Api
 */

/**
 * Create the API client.
 * @param {ApiPaths} paths The path of each endpoint.
 * @param {typeof fetch} fetchFn The function that sends a request.
 * @returns {Api} One function per endpoint.
 */
export function createApi(paths, fetchFn = fetch) {
  /**
   * Get one JSON document.
   * @template T
   * @param {string} path The endpoint path.
   * @returns {Promise<T>} The parsed body.
   */
  async function getJson(path) {
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
   * @param {string} jobId The file name of the job description.
   * @returns {string} The path of that job.
   */
  const jobPath = (jobId) => `${paths.jobs}/${encodeURIComponent(jobId)}`;

  return {
    listJobs: () => getJson(paths.jobs),
    listCandidates: () => getJson(paths.candidates),
    getJob: (jobId) => getJson(jobPath(jobId)),
    listRankedCandidates: (jobId) => getJson(`${jobPath(jobId)}/${paths.rankedCandidates}`),
  };
}
