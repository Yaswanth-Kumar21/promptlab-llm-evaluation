/**
 * Prompt Playground — Phase 4
 *
 * Features:
 *  - System prompt + User prompt inputs
 *  - Provider / Model / Temperature / Max Tokens controls
 *  - Run button with loading state
 *  - Response display with latency, token counts, model info
 *  - History of current session runs
 *  - Error display (never crashes on API failure)
 */

import { useState, useRef } from 'react'
import PageHeader from '../components/ui/PageHeader'
import Spinner from '../components/ui/Spinner'
import ErrorAlert from '../components/ui/ErrorAlert'
import StatusBadge from '../components/ui/StatusBadge'
import { useProviders } from '../hooks/useProviders'
import { runPrompt } from '../services/api'
import { formatLatency, formatTokens, formatDateTime, scoreColour } from '../utils/format'

// ── Provider/Model selector ───────────────────────────────────────────────
function ProviderModelSelector({ provider, model, onProviderChange, onModelChange, providers }) {
  const selected = providers.find(p => p.id === provider)
  const models = selected?.models ?? []

  return (
    <div className="flex gap-3">
      <div className="flex-1">
        <label className="label">Provider</label>
        <select
          className="input"
          value={provider}
          onChange={e => { onProviderChange(e.target.value); onModelChange('') }}
        >
          {providers.map(p => (
            <option key={p.id} value={p.id} disabled={!p.configured}>
              {p.name}{!p.configured ? ' (not configured)' : ''}
            </option>
          ))}
        </select>
      </div>
      <div className="flex-1">
        <label className="label">Model</label>
        <select className="input" value={model} onChange={e => onModelChange(e.target.value)}>
          <option value="">Default ({selected?.default_model})</option>
          {models.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>
    </div>
  )
}

// ── Parameter controls ────────────────────────────────────────────────────
function ParameterControls({ temperature, maxTokens, onTemperatureChange, onMaxTokensChange }) {
  return (
    <div className="flex gap-4">
      <div className="flex-1">
        <label className="label">Temperature — {temperature}</label>
        <input
          type="range" min="0" max="2" step="0.05"
          value={temperature}
          onChange={e => onTemperatureChange(parseFloat(e.target.value))}
          className="w-full accent-brand-500"
        />
        <div className="flex justify-between text-xs text-gray-600 mt-0.5">
          <span>0 — deterministic</span><span>1 — creative</span><span>2 — chaotic</span>
        </div>
      </div>
      <div className="w-36">
        <label className="label">Max tokens</label>
        <input
          type="number" min="1" max="16384" step="64"
          value={maxTokens}
          onChange={e => onMaxTokensChange(parseInt(e.target.value) || 1024)}
          className="input"
        />
      </div>
    </div>
  )
}

// ── Response card ─────────────────────────────────────────────────────────
function ResponseCard({ result }) {
  const [copied, setCopied] = useState(false)

  const copy = () => {
    navigator.clipboard.writeText(result.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (result.error) {
    return (
      <div className="card border-red-800/50">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-red-400 font-semibold text-sm">Run failed</span>
          <span className="badge badge-red">{result.error}</span>
        </div>
        <p className="text-sm text-red-300">{result.error_message}</p>
      </div>
    )
  }

  return (
    <div className="card">
      {/* Metadata bar */}
      <div className="flex flex-wrap items-center gap-3 mb-4 pb-3 border-b border-gray-800 text-xs text-gray-500">
        <span className="badge badge-blue">{result.provider}</span>
        <span className="font-mono">{result.model}</span>
        <span>🌡️ {result.temperature}</span>
        <span>⏱ {formatLatency(result.latency_ms)}</span>
        {result.usage?.input_tokens != null && (
          <span>↑ {formatTokens(result.usage.input_tokens)} tokens</span>
        )}
        {result.usage?.output_tokens != null && (
          <span>↓ {formatTokens(result.usage.output_tokens)} tokens</span>
        )}
        {result.json_valid != null && (
          <span className={result.json_valid ? 'text-green-400' : 'text-red-400'}>
            {result.json_valid ? '✓ valid JSON' : '✗ invalid JSON'}
          </span>
        )}
      </div>

      {/* Response content */}
      <div className="relative">
        <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans leading-relaxed max-h-96 overflow-y-auto">
          {result.content}
        </pre>
        <button
          onClick={copy}
          className="absolute top-0 right-0 text-xs text-gray-500 hover:text-gray-300 px-2 py-1 rounded"
        >
          {copied ? '✓ copied' : 'copy'}
        </button>
      </div>

      {/* Parsed JSON preview */}
      {result.parsed && (
        <details className="mt-4">
          <summary className="text-xs text-brand-400 cursor-pointer">Parsed JSON</summary>
          <pre className="mt-2 text-xs text-green-300 bg-gray-950 rounded p-3 overflow-x-auto">
            {JSON.stringify(result.parsed, null, 2)}
          </pre>
        </details>
      )}

      <p className="text-xs text-gray-700 mt-3">{formatDateTime(result.timestamp)} · {result.experiment_id?.slice(0, 8)}</p>
    </div>
  )
}

// ── Run history sidebar ───────────────────────────────────────────────────
function HistoryItem({ result, isSelected, onClick }) {
  const short = result.content?.slice(0, 60) + (result.content?.length > 60 ? '…' : '')
  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-3 rounded-lg border transition-colors ${
        isSelected
          ? 'border-brand-600/50 bg-brand-900/10 text-gray-200'
          : 'border-gray-800 hover:border-gray-700 text-gray-400 hover:text-gray-300'
      }`}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="badge badge-blue text-xs">{result.provider}</span>
        <span className="text-xs text-gray-600">{formatLatency(result.latency_ms)}</span>
        {result.error && <span className="badge badge-red text-xs">error</span>}
      </div>
      <p className="text-xs truncate">{result.error ? result.error_message : short}</p>
    </button>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────
export default function Playground() {
  const { providers, defaultProvider } = useProviders()

  // Form state
  const [systemPrompt, setSystemPrompt] = useState(
    'You are a helpful, accurate assistant.'
  )
  const [userPrompt, setUserPrompt] = useState('')
  const [provider, setProvider] = useState(defaultProvider || 'mock')
  const [model, setModel] = useState('')
  const [temperature, setTemperature] = useState(0.7)
  const [maxTokens, setMaxTokens] = useState(1024)

  // Result state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [results, setResults] = useState([])
  const [selectedIdx, setSelectedIdx] = useState(null)

  const userPromptRef = useRef(null)

  const handleRun = async () => {
    if (!userPrompt.trim()) {
      userPromptRef.current?.focus()
      return
    }

    setLoading(true)
    setError(null)

    try {
      const result = await runPrompt({
        system_prompt: systemPrompt,
        user_prompt: userPrompt,
        provider,
        model,
        temperature,
        max_tokens: maxTokens,
      })
      setResults(prev => [result, ...prev])
      setSelectedIdx(0)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') handleRun()
  }

  const currentResult = selectedIdx !== null ? results[selectedIdx] : null

  return (
    <div className="p-6 max-w-7xl">
      <PageHeader
        title="Prompt Playground"
        subtitle="Design and run prompts against any configured provider. Results are saved automatically."
      />

      <div className="flex gap-6">
        {/* ── Left panel: inputs ── */}
        <div className="flex-1 space-y-4 min-w-0">
          {/* Provider + model */}
          <div className="card">
            <ProviderModelSelector
              provider={provider}
              model={model}
              providers={providers}
              onProviderChange={setProvider}
              onModelChange={setModel}
            />
          </div>

          {/* System prompt */}
          <div className="card">
            <label className="label">System Prompt</label>
            <textarea
              className="input resize-none font-mono text-sm"
              rows={3}
              placeholder="Optional system/instruction prompt…"
              value={systemPrompt}
              onChange={e => setSystemPrompt(e.target.value)}
            />
          </div>

          {/* User prompt */}
          <div className="card">
            <label className="label">User Prompt <span className="text-red-400">*</span></label>
            <textarea
              ref={userPromptRef}
              className="input resize-none font-mono text-sm"
              rows={6}
              placeholder="Enter your prompt here… (Ctrl+Enter to run)"
              value={userPrompt}
              onChange={e => setUserPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
            />
          </div>

          {/* Parameters */}
          <div className="card">
            <ParameterControls
              temperature={temperature}
              maxTokens={maxTokens}
              onTemperatureChange={setTemperature}
              onMaxTokensChange={setMaxTokens}
            />
          </div>

          {/* Run button */}
          {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

          <button
            onClick={handleRun}
            disabled={loading || !userPrompt.trim()}
            className="btn-primary w-full py-3 text-base flex items-center justify-center gap-2"
          >
            {loading ? (
              <><Spinner size="sm" /> Running…</>
            ) : (
              <>⚡ Run Prompt<span className="text-brand-300 text-xs">(Ctrl+Enter)</span></>
            )}
          </button>

          {/* Result */}
          {currentResult && <ResponseCard result={currentResult} />}
        </div>

        {/* ── Right panel: run history ── */}
        <div className="w-64 flex-shrink-0">
          <div className="card">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Run History ({results.length})
            </p>
            {results.length === 0 ? (
              <p className="text-xs text-gray-600 text-center py-4">
                No runs yet.<br />Run a prompt to see results here.
              </p>
            ) : (
              <div className="space-y-2 max-h-[32rem] overflow-y-auto">
                {results.map((r, i) => (
                  <HistoryItem
                    key={r.experiment_id || i}
                    result={r}
                    isSelected={i === selectedIdx}
                    onClick={() => setSelectedIdx(i)}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Quick tips */}
          <div className="card mt-4 text-xs space-y-2 text-gray-500">
            <p className="font-semibold text-gray-400">Tips</p>
            <p>🌡️ Use <strong className="text-gray-300">temp 0</strong> for JSON/classification</p>
            <p>✍️ <strong className="text-gray-300">Role prompt</strong> shapes tone and vocabulary</p>
            <p>📋 Results are saved as <strong className="text-gray-300">experiments</strong></p>
            <p>⚡ <strong className="text-gray-300">Mock</strong> always works — no API key needed</p>
          </div>
        </div>
      </div>
    </div>
  )
}
