/**
 * Evaluation Page — Phase 7
 *
 * Three tabs:
 *  1. Direct Eval   — paste a prompt + response and evaluate immediately
 *  2. Dataset Eval  — pick a dataset + test case, run LLM then evaluate
 *  3. History       — browse stored evaluation results
 */

import { useState, useEffect } from 'react'
import PageHeader from '../components/ui/PageHeader'
import Spinner from '../components/ui/Spinner'
import ErrorAlert from '../components/ui/ErrorAlert'
import ScoreBar from '../components/ui/ScoreBar'
import MetricResultCard from '../components/ui/MetricResultCard'
import { runEvaluation, runDatasetEval, fetchDatasets, fetchEvaluations } from '../services/evaluationApi'
import { formatDateTime, formatLatency } from '../utils/format'

const ALL_METRICS = ['accuracy', 'relevance', 'tone', 'json_validity', 'groundedness', 'safety']

// ── Overall score display ─────────────────────────────────────────────────
function OverallScore({ report }) {
  return (
    <div className={`card mb-4 ${report.overall_passed ? 'border-green-700/40' : 'border-red-700/40'}`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider">Overall Score</p>
          <p className={`text-3xl font-bold mt-1 ${
            report.overall_score >= 80 ? 'text-green-400' :
            report.overall_score >= 60 ? 'text-yellow-400' : 'text-red-400'
          }`}>{report.overall_score}%</p>
        </div>
        <span className={`text-lg ${report.overall_passed ? 'text-green-400' : 'text-red-400'}`}>
          {report.overall_passed ? '✓ PASSED' : '✗ FAILED'}
        </span>
      </div>
      <ScoreBar score={report.overall_score} />
    </div>
  )
}

// ── Direct evaluation tab ─────────────────────────────────────────────────
function DirectEvalTab() {
  const [userPrompt, setUserPrompt]   = useState('What is the capital of France?')
  const [response, setResponse]       = useState('The capital of France is Paris.')
  const [expected, setExpected]       = useState('Paris')
  const [metrics, setMetrics]         = useState(['accuracy', 'relevance', 'safety'])
  const [loading, setLoading]         = useState(false)
  const [result, setResult]           = useState(null)
  const [error, setError]             = useState(null)

  const toggleMetric = (m) =>
    setMetrics(prev => prev.includes(m) ? prev.filter(x => x !== m) : [...prev, m])

  const handleRun = async () => {
    setLoading(true); setError(null); setResult(null)
    try {
      const out = await runEvaluation({
        user_prompt: userPrompt,
        response,
        expected_output: expected || undefined,
        metrics,
      })
      setResult(out)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="card space-y-3">
        <div>
          <label className="label">User Prompt</label>
          <textarea className="input resize-none text-sm" rows={2} value={userPrompt}
            onChange={e => setUserPrompt(e.target.value)} />
        </div>
        <div>
          <label className="label">LLM Response to Evaluate</label>
          <textarea className="input resize-none text-sm font-mono" rows={4} value={response}
            onChange={e => setResponse(e.target.value)} />
        </div>
        <div>
          <label className="label">Expected Output <span className="text-gray-600">(required for accuracy)</span></label>
          <input className="input text-sm" placeholder="e.g. Paris" value={expected}
            onChange={e => setExpected(e.target.value)} />
        </div>
        <div>
          <label className="label">Metrics to run</label>
          <div className="flex flex-wrap gap-2 mt-1">
            {ALL_METRICS.map(m => (
              <button key={m}
                onClick={() => toggleMetric(m)}
                className={`badge cursor-pointer transition-colors ${
                  metrics.includes(m) ? 'badge-blue' : 'badge-gray opacity-50'
                }`}
              >
                {m.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </div>

        {error && <ErrorAlert message={error} />}

        <button onClick={handleRun} disabled={loading || !userPrompt.trim() || !response.trim()}
          className="btn-primary flex items-center gap-2">
          {loading ? <><Spinner size="sm" />Evaluating…</> : '📊 Run Evaluation'}
        </button>
      </div>

      {result && (
        <div>
          <OverallScore report={result.evaluation} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {result.evaluation.results.map(r => <MetricResultCard key={r.metric} result={r} />)}
          </div>
          <p className="text-xs text-gray-600 mt-3">
            Evaluation ID: {result.experiment_id?.slice(0, 8)} · All checks are deterministic (no LLM judge).
          </p>
        </div>
      )}
    </div>
  )
}

// ── Dataset evaluation tab ────────────────────────────────────────────────
function DatasetEvalTab() {
  const [datasets, setDatasets]   = useState([])
  const [dataset, setDataset]     = useState('classification')
  const [caseId, setCaseId]       = useState('')
  const [provider, setProvider]   = useState('mock')
  const [loading, setLoading]     = useState(false)
  const [result, setResult]       = useState(null)
  const [error, setError]         = useState(null)

  useEffect(() => {
    fetchDatasets().then(d => setDatasets(d.datasets || [])).catch(() => {})
  }, [])

  const selectedDataset = datasets.find(d => d.name === dataset)
  const caseIds = selectedDataset?.case_ids ?? []

  const handleRun = async () => {
    if (!caseId) return
    setLoading(true); setError(null); setResult(null)
    try {
      const out = await runDatasetEval({ dataset, test_case_id: caseId, provider, temperature: 0.0 })
      setResult(out)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="card space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Dataset</label>
            <select className="input text-sm" value={dataset}
              onChange={e => { setDataset(e.target.value); setCaseId('') }}>
              {['classification','summarization','extraction','rag','safety'].map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Test Case</label>
            <select className="input text-sm" value={caseId} onChange={e => setCaseId(e.target.value)}>
              <option value="">— select a case —</option>
              {caseIds.map(id => <option key={id} value={id}>{id}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className="label">Provider</label>
          <select className="input text-sm w-44" value={provider} onChange={e => setProvider(e.target.value)}>
            {['mock','openai','anthropic','gemini','mistral'].map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>

        {selectedDataset && (
          <p className="text-xs text-gray-500">
            {selectedDataset.description} · {selectedDataset.case_count} cases
          </p>
        )}

        {error && <ErrorAlert message={error} />}

        <button onClick={handleRun} disabled={loading || !caseId}
          className="btn-primary flex items-center gap-2">
          {loading ? <><Spinner size="sm" />Running…</> : '▶ Run Test Case'}
        </button>
      </div>

      {result && (
        <div>
          <div className="card mb-4 space-y-2 text-sm">
            <p className="text-xs text-gray-500 uppercase tracking-wider">Test Input</p>
            <pre className="text-xs text-gray-400 whitespace-pre-wrap bg-gray-950 rounded p-2 max-h-24 overflow-y-auto">
              {result.user_prompt}
            </pre>
            <p className="text-xs text-gray-500 uppercase tracking-wider mt-2">Response ({formatLatency(result.latency_ms)})</p>
            <pre className="text-xs text-gray-300 whitespace-pre-wrap bg-gray-950 rounded p-2 max-h-32 overflow-y-auto">
              {result.response}
            </pre>
          </div>
          <OverallScore report={result.evaluation} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {result.evaluation.results.map(r => <MetricResultCard key={r.metric} result={r} />)}
          </div>
        </div>
      )}
    </div>
  )
}

// ── History tab ───────────────────────────────────────────────────────────
function HistoryTab() {
  const [data, setData]     = useState({ evaluations: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [metric, setMetric] = useState('')
  const [passed, setPassed] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const d = await fetchEvaluations({
        metric: metric || undefined,
        passed: passed === '' ? undefined : passed === 'true',
      })
      setData(d)
    } catch {
      setData({ evaluations: [], total: 0 })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [metric, passed])

  return (
    <div className="space-y-4">
      <div className="flex gap-3 mb-2">
        <select className="input text-sm w-44" value={metric} onChange={e => setMetric(e.target.value)}>
          <option value="">All metrics</option>
          {ALL_METRICS.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
        <select className="input text-sm w-36" value={passed} onChange={e => setPassed(e.target.value)}>
          <option value="">All results</option>
          <option value="true">Passed only</option>
          <option value="false">Failed only</option>
        </select>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-gray-500"><Spinner /><span>Loading…</span></div>
      ) : data.evaluations.length === 0 ? (
        <p className="text-gray-500 text-sm py-8 text-center">No evaluation results yet. Run an evaluation to see results here.</p>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800">
                {['Metric', 'Score', 'Pass/Fail', 'Method', 'Reason', 'When'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.evaluations.map(e => (
                <tr key={e.id} className="border-b border-gray-800 hover:bg-gray-800/30">
                  <td className="px-4 py-2 text-xs font-medium text-gray-300">{e.metric}</td>
                  <td className="px-4 py-2">
                    <div className="w-24"><ScoreBar score={e.score} /></div>
                  </td>
                  <td className="px-4 py-2">
                    <span className={`badge ${e.passed ? 'badge-green' : 'badge-red'}`}>
                      {e.passed ? 'pass' : 'fail'}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-xs text-gray-500">{e.evaluation_method}</td>
                  <td className="px-4 py-2 text-xs text-gray-400 max-w-xs truncate">{e.reason}</td>
                  <td className="px-4 py-2 text-xs text-gray-600">{formatDateTime(e.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="px-4 py-2 text-xs text-gray-600">{data.total} total results</p>
        </div>
      )}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────
const TABS = [
  { id: 'direct',  label: '⚡ Direct Eval' },
  { id: 'dataset', label: '📋 Dataset Eval' },
  { id: 'history', label: '📜 History' },
]

export default function Evaluation() {
  const [tab, setTab] = useState('direct')

  return (
    <div className="p-6 max-w-4xl">
      <PageHeader
        title="Evaluation Engine"
        subtitle="Measure accuracy, relevance, tone, JSON validity, groundedness, and safety. All checks are deterministic — no LLM judge."
      />

      <div className="flex gap-1 mb-6 bg-gray-900 rounded-lg p-1 w-fit border border-gray-800">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              tab === t.id ? 'bg-brand-600 text-white' : 'text-gray-400 hover:text-gray-200'
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'direct'  && <DirectEvalTab />}
      {tab === 'dataset' && <DatasetEvalTab />}
      {tab === 'history' && <HistoryTab />}
    </div>
  )
}
