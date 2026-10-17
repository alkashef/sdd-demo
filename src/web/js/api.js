// @ts-check
/**
 * @module api
 * The only module that calls `fetch`. It reads the JSON API (design section 4) and adds context
 * to a failure. It does not show anything (the view modules do) and keeps no data.
 */

/**
 * @typedef {{ id: string, title: string }} JobSummary A job description in the list (LST-001).
 * @typedef {{ id: string, name: string | null }} CandidateSummary A candidate in the list (LST-002).
 * @typedef {{ jobs: string, candidates: string }} ApiPaths The paths of the list endpoints.
 * @typedef {{
 *   listJobs: () => Promise<JobSummary[]>,
 *   listCandidates: () => Promise<CandidateSummary[]>,
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

  return {
    listJobs: () => getJson(paths.jobs),
    listCandidates: () => getJson(paths.candidates),
  };
}
