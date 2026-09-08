/**
 * StatusBadge — coloured badge for statuses like healthy/degraded/error.
 */
export default function StatusBadge({ status }) {
  const map = {
    healthy:       'badge-green',
    available:     'badge-green',
    ok:            'badge-green',
    degraded:      'badge-yellow',
    not_configured:'badge-gray',
    error:         'badge-red',
    pending:       'badge-yellow',
    processing:    'badge-blue',
    ready:         'badge-green',
    failed:        'badge-red',
  }
  const cls = map[status] ?? 'badge-gray'
  return <span className={cls}>{status}</span>
}
