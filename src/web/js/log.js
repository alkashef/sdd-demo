// @ts-check
/**
 * @module log
 * The only module that uses `console`. It writes a message only if its level reaches the
 * configured level. It does not decide what to log (the callers do).
 */

/** The log levels, least to most severe. */
export const LOG_LEVELS = Object.freeze({ debug: 0, info: 1, warn: 2, error: 3 });

/**
 * @typedef {keyof typeof LOG_LEVELS} LogLevel
 * @typedef {Record<LogLevel, (...parts: unknown[]) => void>} Logger
 * @typedef {Pick<Console, LogLevel>} LogSink
 */

/**
 * Create a logger that drops messages below `level`.
 * @param {LogLevel} level The least severe level to write.
 * @param {LogSink} sink Where messages go.
 * @returns {Logger} One function per level.
 */
export function createLogger(level, sink = console) {
  /** @type {Logger} */
  const logger = { debug: () => {}, info: () => {}, warn: () => {}, error: () => {} };
  for (const name of /** @type {LogLevel[]} */ (Object.keys(LOG_LEVELS))) {
    if (LOG_LEVELS[name] >= LOG_LEVELS[level]) {
      logger[name] = (...parts) => sink[name](...parts);
    }
  }
  return logger;
}
