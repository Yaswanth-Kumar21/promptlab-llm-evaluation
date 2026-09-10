/**
 * Prompt Library — Phase 4/6
 *
 * Browse, create, search, and manage saved prompts.
 * Each prompt can have multiple versions.
 */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../components/ui/PageHeader'
import EmptyState from '../components/ui/EmptyState'
import Spinner from '../components/ui/Spinner'
import ErrorAlert from '../components/ui/ErrorAlert'
import { fetchPrompts, createPrompt, deletePrompt } from '../services/api'
import { formatDateTime } from '../utils/format'

const CATEGORIES = ['general', 'zero-shot', 'few-shot', 'structured', 'rag', 'safety', 'job-analyzer']

// ── Create prompt modal ───────────────────────────────────────────────────
function CreateModal({ onClose, onCreate }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('general')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    setError(null)
    try {
      const prompt = await createPrompt({ name: name.trim(), description, category, tags: '' })
      onCreate(prompt)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-md p-6">
        <h2 className="text-lg font-bold text-white mb-4">New Prompt</h2>
        {error && <div className="mb-3"><ErrorAlert message={error} /></div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Name *</label>
            <input className="input" placeholder="e.g. Resume Analyser" value={name} onChange={e => setName(e.target.value)} autoFocus />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea className="input resize-none" rows={2} placeholder="What does this prompt do?" value={description} onChange={e => setDescription(e.target.value)} />
          </div>
          <div>
            <label className="label">Category</label>
            <select className="input" value={category} onChange={e => setCategory(e.target.value)}>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="flex gap-3 justify-end">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={loading || !name.trim()} className="btn-primary flex items-center gap-2">
              {loading ? <><Spinner size="sm" />Creating…</> : 'Create Prompt'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Prompt row ────────────────────────────────────────────────────────────
function PromptRow({ prompt, onDelete, onOpen }) {
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async (e) => {
    e.stopPropagation()
    if (!window.confirm(`Delete "${prompt.name}"? This also deletes all versions.`)) return
    setDeleting(true)
    try {
      await deletePrompt(prompt.id)
      onDelete(prompt.id)
    } catch {
      setDeleting(false)
    }
  }

  return (
    <tr
      className="border-b border-gray-800 hover:bg-gray-800/40 cursor-pointer transition-colors"
      onClick={() => onOpen(prompt.id)}
    >
      <td className="px-4 py-3">
        <p className="text-sm font-medium text-gray-200">{prompt.name}</p>
        {prompt.description && <p className="text-xs text-gray-500 mt-0.5">{prompt.description}</p>}
      </td>
      <td className="px-4 py-3">
        <span className="badge badge-blue text-xs">{prompt.category}</span>
      </td>
      <td className="px-4 py-3 text-sm text-gray-400 text-center">{prompt.version_count}</td>
      <td className="px-4 py-3 text-xs text-gray-500">{formatDateTime(prompt.updated_at)}</td>
      <td className="px-4 py-3 text-right">
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="text-xs text-red-500 hover:text-red-300 px-2 py-1"
        >
          {deleting ? '…' : 'delete'}
        </button>
      </td>
    </tr>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────
export default function PromptLibrary() {
  const navigate = useNavigate()
  const [data, setData] = useState({ prompts: [], total: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchPrompts({ search: search || undefined, category: category || undefined })
      setData(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [search, category])

  useEffect(() => { load() }, [load])

  const handleCreated = (prompt) => {
    setShowCreate(false)
    navigate(`/versions?prompt=${prompt.id}`)
  }

  const handleDelete = (id) => {
    setData(prev => ({ ...prev, prompts: prev.prompts.filter(p => p.id !== id), total: prev.total - 1 }))
  }

  return (
    <div className="p-6 max-w-5xl">
      <PageHeader
        title="Prompt Library"
        subtitle={`${data.total} saved prompt${data.total !== 1 ? 's' : ''}`}
        actions={
          <button onClick={() => setShowCreate(true)} className="btn-primary text-sm">
            + New Prompt
          </button>
        }
      />

      {/* Filters */}
      <div className="flex gap-3 mb-5">
        <input
          className="input max-w-xs"
          placeholder="Search by name…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select className="input w-44" value={category} onChange={e => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {error && <ErrorAlert message={error} />}

      {loading ? (
        <div className="flex items-center gap-2 text-gray-500 py-8"><Spinner /><span>Loading…</span></div>
      ) : data.prompts.length === 0 ? (
        <EmptyState
          icon="📚"
          title="No prompts yet"
          description="Create your first prompt to start building your library."
          action={<button onClick={() => setShowCreate(true)} className="btn-primary text-sm">+ Create Prompt</button>}
        />
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800 text-left">
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Name</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Category</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase text-center">Versions</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Updated</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.prompts.map(p => (
                <PromptRow
                  key={p.id}
                  prompt={p}
                  onDelete={handleDelete}
                  onOpen={id => navigate(`/versions?prompt=${id}`)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCreate && <CreateModal onClose={() => setShowCreate(false)} onCreate={handleCreated} />}
    </div>
  )
}
