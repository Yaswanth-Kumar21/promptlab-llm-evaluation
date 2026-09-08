/**
 * Formatting utilities used across the UI.
 */

/** Format milliseconds as a readable latency string. */
export function formatLatency(ms) {
  if (ms == null) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

/** Format a score (0–100) as a percentage string. */
export function formatScore(score) {
  if (score == null) return '—'
  return `${Math.round(score)}%`
}

/** Format an ISO timestamp as a local date+time string. */
export function formatDateTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

/** Truncate text to maxLen characters, appending '…' if cut. */
export function truncate(text, maxLen = 120) {
  if (!text) return ''
  return text.length > maxLen ? text.slice(0, maxLen) + '…' : text
}

/** Return a colour class based on a 0–100 score. */
export function scoreColour(score) {
  if (score == null) return 'text-gray-500'
  if (score >= 80) return 'text-green-400'
  if (score >= 50) return 'text-yellow-400'
  return 'text-red-400'
}

/** Format token count with thousands separator. */
export function formatTokens(n) {
  if (n == null) return '—'
  return n.toLocaleString()
}
