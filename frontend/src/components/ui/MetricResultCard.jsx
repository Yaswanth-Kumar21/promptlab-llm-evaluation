/**
 * MetricResultCard — displays one evaluation metric result.
 */
import ScoreBar from './ScoreBar'

const METHOD_LABELS = {
  deterministic: { label: 'deterministic', cls: 'badge-green' },
  schema_check:  { label: 'schema check',  cls: 'badge-blue' },
  semantic:      { label: 'semantic',      cls: 'badge-yellow' },
  llm_judge:     { label: 'LLM judge ⚠',  cls: 'badge-yellow' },
}

export default function MetricResultCard({ result }) {
  const method = METHOD_LABELS[result.evaluation_method] ?? { label: result.evaluation_method, cls: 'badge-gray' }

  return (
    <div className={`rounded-lg border p-4 ${result.passed ? 'border-gray-800' : 'border-red-800/50 bg-red-900/5'}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`text-sm font-semibold ${result.passed ? 'text-gray-200' : 'text-red-300'}`}>
            {result.passed ? '✓' : '✗'} {result.metric.replace(/_/g, ' ')}
          </span>
          <span className={`badge ${method.cls} text-xs`}>{method.label}</span>
        </div>
        <span className={`text-sm font-mono font-bold ${
          result.score >= 80 ? 'text-green-400' :
          result.score >= 60 ? 'text-yellow-400' : 'text-red-400'
        }`}>
          {Math.round(result.score)}
        </span>
      </div>
      <ScoreBar score={result.score} showLabel={false} />
      <p className="text-xs text-gray-400 mt-2">{result.reason}</p>
      {result.evidence && (
        <p className="text-xs text-gray-600 mt-1 font-mono truncate">{result.evidence}</p>
      )}
    </div>
  )
}
