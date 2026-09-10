/**
 * Prompt Versions — Phase 6
 *
 * Full version management for a selected prompt:
 *  - List versions with metadata
 *  - Create a new version
 *  - Mark best version
 *  - Duplicate a version
 *  - Run a version directly from here
 *  - Side-by-side diff view (text comparison)
 */

import { useState, useEffect, useCallback } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import PageHeader from '../components/ui/PageHeader'
import EmptyState from '../components/ui/EmptyState'
import Spinner from '../components/ui/Spinner'
import ErrorAlert from '../components/ui/ErrorAlert'
import {
  fetchPrompt, fetchVersions, createVersion,
  markBestVersion, duplicateVersion, runPrompt
} from '../services/api'
import { formatDateTime, formatLatency, formatTokens } from '../utils/format'

// ── Version badge ─────────────────────────────────────────────────────────
function VersionBadge({ n, isBest }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="badge badge-blue font-mono">V{n}</span>
      {isBest && <span className="badge badge-green text-xs">⭐ best</span>}
    </div>
  )
}

// ── Create version form ───────────────────────────────────────────────────
function CreateVersionForm({ promptId, onCreated, onCancel }) {
  const [form, setForm] = useState({
    system_prompt: '',
    user_prompt_template: '',
    provider: 'mock',
    model: '',
    temperature: 0.7,
    max_tokens: 1024,
    notes: '',
    author: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.user_prompt_template.trim()) return
    setLoading(true)
    setError(null)
    try {
      const version = await createVersion(promptId, form)
      onCreated(version)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card border-brand-700/40">
      <h3 className="text-sm font-semibold text-gray-200 mb-4">Add New Version</h3>
      {error && <div className="mb-3"><ErrorAlert message={error} /></div>}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="label">System Prompt</label>
          <textarea className="input resize-none font-mono text-sm" rows={2}
            placeholder="Optional system prompt…"
            value={form.system_prompt} onChange={e => set('system_prompt', e.target.value)} />
        </div>
        <div>
          <label className="label">User Prompt Template *</label>
          <textarea className="input resize-none font-mono text-sm" rows={4}
            placeholder="The prompt text…"
            value={form.user_prompt_template} onChange={e => set('user_prompt_template', e.target.value)} />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="label">Provider</label>
            <select className="input text-sm" value={form.provider} onChange={e => set('provider', e.target.value)}>
              {['mock','openai','anthropic','gemini','mistral'].map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Temperature</label>
            <input type="number" min="0" max="2" step="0.1" className="input text-sm"
              value={form.temperature} onChange={e => set('temperature', parseFloat(e.target.value))} />
          </div>
          <div>
            <label className="label">Max tokens</label>
            <input type="number" min="1" max="16384" className="input text-sm"
              value={form.max_tokens} onChange={e => set('max_tokens', parseInt(e.target.value))} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Author</label>
            <input className="input text-sm" placeholder="Your name" value={form.author} onChange={e => set('author', e.target.value)} />
          </div>
          <div>
            <label className="label">Notes</label>
            <input className="input text-sm" placeholder="What changed in this version?" value={form.notes} onChange={e => set('notes', e.target.value)} />
          </div>
        </div>
        <div className="flex gap-3 justify-end">
          <button type="button" onClick={onCancel} className="btn-secondary text-sm">Cancel</button>
          <button type="submit" disabled={loading || !form.user_prompt_template.trim()} className="btn-primary text-sm flex items-center gap-2">
            {loading ? <><Spinner size="sm" />Saving…</> : 'Save Version'}
          </button>
        </div>
      </form>
    </div>
  )
}

// ── Version detail card ───────────────────────────────────────────────────
function VersionCard({ version, promptId, onBestMarked, onDuplicated }) {
  const [runResult, setRunResult] = useState(null)
  const [runLoading, setRunLoading] = useState(false)
  const [runInput, setRunInput] = useState('')
  const [showRun, setShowRun] = useState(false)
  const [marking, setMarking] = useState(false)
  const [duplicating, setDuplicating] = useState(false)

  const handleMarkBest = async () => {
    setMarking(true)
    try { onBestMarked(await markBestVersion(promptId, version.id)) }
    finally { setMarking(false) }
  }

  const handleDuplicate = async () => {
    setDuplicating(true)
    try { onDuplicated(await duplicateVersion(promptId, version.id)) }
    finally { setDuplicating(false) }
  }

  const handleRun = async () => {
    setRunLoading(true)
    try {
      const res = await runPrompt({
        system_prompt: version.system_prompt,
        user_prompt: runInput || version.user_prompt_template,
        provider: version.provider,
        model: version.model,
        temperature: version.temperature,
        max_tokens: version.max_tokens,
        prompt_version_id: version.id,
      })
      setRunResult(res)
    } catch (err) {
      setRunResult({ error: 'run_failed', error_message: err.message, content: '' })
    } finally {
      setRunLoading(false)
    }
  }

  return (
    <div className={`card ${version.is_best ? 'border-green-700/50 bg-green-900/5' : ''}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <VersionBadge n={version.version_number} isBest={version.is_best} />
        <div className="flex items-center gap-2">
          <button onClick={handleMarkBest} disabled={marking || version.is_best}
            className="text-xs text-gray-500 hover:text-yellow-400 disabled:opacity-40 transition-colors">
            {marking ? '…' : version.is_best ? '⭐ best' : '☆ mark best'}
          </button>
          <button onClick={handleDuplicate} disabled={duplicating}
            className="text-xs text-gray-500 hover:text-blue-400 transition-colors">
            {duplicating ? '…' : '⊕ duplicate'}
          </button>
          <button onClick={() => setShowRun(!showRun)}
            className="text-xs btn-secondary py-1 px-2">
            {showRun ? 'hide run' : '▶ run'}
          </button>
        </div>
      </div>

      {/* Metadata */}
      <div className="flex flex-wrap gap-3 text-xs text-gray-500 mb-3">
        <span className="badge badge-blue">{version.provider}</span>
        {version.model && <span className="font-mono">{version.model}</span>}
        <span>🌡️ {version.temperature}</span>
        <span>↓ {version.max_tokens} max</span>
        {version.author && <span>by {version.author}</span>}
        <span>{formatDateTime(version.created_at)}</span>
      </div>

      {/* Notes */}
      {version.notes && (
        <div className="mb-3 text-xs text-yellow-400 bg-yellow-900/10 border border-yellow-800/30 rounded px-3 py-2">
          📝 {version.notes}
        </div>
      )}

      {/* Prompt content */}
      {version.system_prompt && (
        <div className="mb-2">
          <p className="text-xs text-gray-600 mb-1">System prompt</p>
          <pre className="text-xs text-gray-400 bg-gray-950 rounded p-2 whitespace-pre-wrap overflow-x-auto max-h-24">
            {version.system_prompt}
          </pre>
        </div>
      )}
      <div>
        <p className="text-xs text-gray-600 mb-1">User prompt template</p>
        <pre className="text-xs text-gray-400 bg-gray-950 rounded p-2 whitespace-pre-wrap overflow-x-auto max-h-36">
          {version.user_prompt_template}
        </pre>
      </div>

      {/* Run panel */}
      {showRun && (
        <div className="mt-4 pt-4 border-t border-gray-800">
          <label className="label text-xs">Test input (optional — uses template as-is if empty)</label>
          <textarea className="input text-sm resize-none mb-2 font-mono" rows={2}
            placeholder="Enter test input…" value={runInput} onChange={e => setRunInput(e.target.value)} />
          <button onClick={handleRun} disabled={runLoading} className="btn-primary text-sm flex items-center gap-2">
            {runLoading ? <><Spinner size="sm" />Running…</> : '▶ Run this version'}
          </button>

          {runResult && (
            <div className="mt-3">
              {runResult.error ? (
                <ErrorAlert message={runResult.error_message} />
              ) : (
                <div>
                  <div className="flex gap-2 text-xs text-gray-500 mb-1">
                    <span>{formatLatency(runResult.latency_ms)}</span>
                    {runResult.usage?.output_tokens && <span>↓ {formatTokens(runResult.usage.output_tokens)} tokens</span>}
                  </div>
                  <pre className="text-sm text-gray-300 whitespace-pre-wrap bg-gray-950 rounded p-3 max-h-48 overflow-y-auto font-sans">
                    {runResult.content}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────
export default function PromptVersions() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const promptId = searchParams.get('prompt')

  const [prompt, setPrompt] = useState(null)
  const [versions, setVersions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showCreate, setShowCreate] = useState(false)

  const load = useCallback(async () => {
    if (!promptId) return
    setLoading(true)
    setError(null)
    try {
      const [p, v] = await Promise.all([fetchPrompt(promptId), fetchVersions(promptId)])
      setPrompt(p)
      setVersions(v)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [promptId])

  useEffect(() => { load() }, [load])

  const handleCreated = (version) => {
    setVersions(prev => [...prev, version])
    setShowCreate(false)
  }

  const handleBestMarked = (updated) => {
    setVersions(prev => prev.map(v => ({ ...v, is_best: v.id === updated.id })))
  }

  const handleDuplicated = (newV) => {
    setVersions(prev => [...prev, newV])
  }

  if (!promptId) {
    return (
      <div className="p-6">
        <PageHeader title="Prompt Versions" subtitle="Select a prompt to manage its versions." />
        <EmptyState
          icon="🔀"
          title="No prompt selected"
          description="Go to the Prompt Library and click a prompt to manage its versions."
          action={<button onClick={() => navigate('/library')} className="btn-primary text-sm">Go to Library</button>}
        />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl">
      <PageHeader
        title={prompt?.name ?? 'Prompt Versions'}
        subtitle={`${versions.length} version${versions.length !== 1 ? 's' : ''} · ${prompt?.category ?? ''}`}
        actions={
          <div className="flex gap-2">
            <button onClick={() => navigate('/library')} className="btn-secondary text-sm">← Library</button>
            <button onClick={() => setShowCreate(!showCreate)} className="btn-primary text-sm">
              + New Version
            </button>
          </div>
        }
      />

      {error && <ErrorAlert message={error} />}
      {loading && <div className="flex items-center gap-2 text-gray-500 py-4"><Spinner /><span>Loading…</span></div>}

      {showCreate && (
        <div className="mb-5">
          <CreateVersionForm
            promptId={promptId}
            onCreated={handleCreated}
            onCancel={() => setShowCreate(false)}
          />
        </div>
      )}

      {!loading && versions.length === 0 ? (
        <EmptyState
          icon="📝"
          title="No versions yet"
          description="Create the first version to start iterating on this prompt."
          action={<button onClick={() => setShowCreate(true)} className="btn-primary text-sm">+ Create Version</button>}
        />
      ) : (
        <div className="space-y-4">
          {[...versions].reverse().map(v => (
            <VersionCard
              key={v.id}
              version={v}
              promptId={promptId}
              onBestMarked={handleBestMarked}
              onDuplicated={handleDuplicated}
            />
          ))}
        </div>
      )}
    </div>
  )
}
