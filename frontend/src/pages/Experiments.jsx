/**
 * Experiments — Phase 6
 *
 * Full experiment history: every prompt run is recorded.
 * Filter by provider, paginate, click to see full details.
 */

import { useState, useEffect, useCallback } from 'react'
import PageHeader from '../components/ui/PageHeader'
import EmptyState from '../components/ui/EmptyState'
import Spinner from '../components/ui/Spinner'
import ErrorAlert from '../components/ui/ErrorAlert'
import { fetchExperiments, fetchExperiment } from '../services/api'
import { formatDateTime, formatLatency, formatTokens, truncate } from '../utils/format'

// ── Detail modal ──────────────────────────────────────────────────────────
function DetailModal({ experimentId, onClose }) {
  const [exp, setExp] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchExperiment(experimentId)
      .then(setExp)
      .finally(() => setLoading(false))
  }, [experimentId])

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-y-auto p-6"
        onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="font-bold text-white">Experiment Detail</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-200 text-xl">×</button>
        </div>

        {loading ? (
          <div className="flex items-center gap-2 text-gray-500"><Spinner /><span>Loading…</span></div>
        ) : exp ? (
          <div className="space-y-4 text-sm">
            <div className="flex flex-wrap gap-2">
              <span className="badge badge-blue">{exp.provider}</span>
              <span className="font-mono text-xs text-gray-400">{exp.model}</span>
              <span className="badge badge-gray">temp {exp.temperature}</span>
              {exp.passed === true && <span className="badge badge-green">passed</span>}
              {exp.passed === false && <span className="badge badge-red">failed</span>}
            </div>

            <Row label="Experiment ID" value={<span className="font-mono text-xs">{exp.id}</span>} />
            <Row label="Latency" value={formatLatency(exp.latency_ms)} />
            <Row label="Tokens" value={`↑${formatTokens(exp.input_tokens)} ↓${formatTokens(exp.output_tokens)}`} />
            <Row label="Timestamp" value={formatDateTime(exp.created_at)} />

            {exp.system_prompt && (
              <div>
                <p className="text-gray-600 text-xs mb-1">System prompt</p>
                <pre className="text-xs text-gray-400 bg-gray-950 rounded p-2 whitespace-pre-wrap max-h-24 overflow-y-auto">{exp.system_prompt}</pre>
              </div>
            )}

            <div>
              <p className="text-gray-600 text-xs mb-1">User prompt</p>
              <pre className="text-xs text-gray-400 bg-gray-950 rounded p-2 whitespace-pre-wrap max-h-32 overflow-y-auto">{exp.user_prompt}</pre>
            </div>

            <div>
              <p className="text-gray-600 text-xs mb-1">Response</p>
              <pre className="text-xs text-gray-300 bg-gray-950 rounded p-2 whitespace-pre-wrap max-h-48 overflow-y-auto">{exp.response || '(empty)'}</pre>
            </div>

            {exp.error && (
              <div className="bg-red-900/30 border border-red-800 rounded p-3">
                <p className="text-red-400 text-xs font-medium">Error: {exp.error}</p>
              </div>
            )}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">Experiment not found.</p>
        )}
      </div>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="text-gray-300">{value}</span>
    </div>
  )
}

// ── Experiment row ────────────────────────────────────────────────────────
function ExperimentRow({ exp, onClick }) {
  return (
    <tr className="border-b border-gray-800 hover:bg-gray-800/40 cursor-pointer" onClick={onClick}>
      <td className="px-4 py-3 text-xs font-mono text-gray-500">{exp.id?.slice(0, 8)}</td>
      <td className="px-4 py-3">
        <span className="badge badge-blue">{exp.provider}</span>
      </td>
      <td className="px-4 py-3 text-xs text-gray-400 font-mono">{exp.model || '—'}</td>
      <td className="px-4 py-3 text-xs text-gray-400 max-w-xs">
        <p className="truncate">{truncate(exp.user_prompt, 80)}</p>
      </td>
      <td className="px-4 py-3 text-xs text-gray-400 max-w-xs">
        <p className="truncate">{exp.error ? `⚠ ${exp.error}` : truncate(exp.response, 80)}</p>
      </td>
      <td className="px-4 py-3 text-xs text-gray-500">{formatLatency(exp.latency_ms)}</td>
      <td className="px-4 py-3 text-xs text-gray-500">{formatDateTime(exp.created_at)}</td>
    </tr>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────
export default function Experiments() {
  const [data, setData] = useState({ experiments: [], total: 0, pages: 1 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [provider, setProvider] = useState('')
  const [selectedId, setSelectedId] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchExperiments({
        page,
        page_size: 20,
        provider: provider || undefined,
      })
      setData(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [page, provider])

  useEffect(() => { load() }, [load])

  return (
    <div className="p-6 max-w-7xl">
      <PageHeader
        title="Experiments"
        subtitle={`${data.total} recorded prompt run${data.total !== 1 ? 's' : ''}`}
        actions={
          <button onClick={load} className="btn-secondary text-xs px-3 py-1.5">↻ Refresh</button>
        }
      />

      {/* Filters */}
      <div className="flex gap-3 mb-5">
        <select className="input w-44 text-sm" value={provider} onChange={e => { setProvider(e.target.value); setPage(1) }}>
          <option value="">All providers</option>
          {['mock','openai','anthropic','gemini','mistral'].map(p => <option key={p} value={p}>{p}</option>)}
        </select>
      </div>

      {error && <ErrorAlert message={error} />}

      {loading ? (
        <div className="flex items-center gap-2 text-gray-500 py-8"><Spinner /><span>Loading…</span></div>
      ) : data.experiments.length === 0 ? (
        <EmptyState
          icon="🧪"
          title="No experiments yet"
          description="Run a prompt from the Playground — each run is automatically saved here."
        />
      ) : (
        <>
          <div className="card p-0 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  {['ID', 'Provider', 'Model', 'User Prompt', 'Response', 'Latency', 'When'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.experiments.map(exp => (
                  <ExperimentRow key={exp.id} exp={exp} onClick={() => setSelectedId(exp.id)} />
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data.pages > 1 && (
            <div className="flex items-center justify-between mt-4 text-sm text-gray-500">
              <span>Page {page} of {data.pages} · {data.total} total</span>
              <div className="flex gap-2">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary text-xs px-3 py-1.5">← Prev</button>
                <button onClick={() => setPage(p => Math.min(data.pages, p + 1))} disabled={page === data.pages} className="btn-secondary text-xs px-3 py-1.5">Next →</button>
              </div>
            </div>
          )}
        </>
      )}

      {selectedId && <DetailModal experimentId={selectedId} onClose={() => setSelectedId(null)} />}
    </div>
  )
}
