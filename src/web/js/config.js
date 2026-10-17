// @ts-check
/**
 * @module config
 * The behavior-affecting values of the front end: the API paths (the ranking segment follows a job path) and the log level.
 * It holds no logic. `main.js` passes these values to the modules that need them.
 */

export const config = Object.freeze({
  logLevel: "info",
  api: Object.freeze({
    jobs: "/api/jobs",
    candidates: "/api/candidates",
    rankedCandidates: "ranked-candidates",
  }),
});
