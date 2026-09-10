/**
 * ScoreBar — horizontal coloured bar showing a 0–100 score.
 */
export default function ScoreBar({ score, showLabel = true }) {
  const pct = Math.max(0, Math.min(100, score ?? 0))
  const colour =
    pct >= 80 ? 'bg-green-500' :
    pct >= 60 ? 'bg-yellow-500' :
    'bg-red-500'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-800 rounded-full h-2 overflow-hidden">
        <div className={`h-2 rounded-full transition-all ${colour}`} style={{ width: `${pct}%` }} />
      </div>
      {showLabel && (
        <span className={`text-xs font-mono w-10 text-right ${
          pct >= 80 ? 'text-green-400' : pct >= 60 ? 'text-yellow-400' : 'text-red-400'
        }`}>
          {Math.round(pct)}%
        </span>
      )}
    </div>
  )
}
