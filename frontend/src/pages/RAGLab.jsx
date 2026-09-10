/**
 * RAG Lab — Phase 9
 *
 * Two tabs:
 *  1. Documents — upload, list, delete
 *  2. Query     — ask questions with source citations
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import PageHeader from '../components/ui/PageHeader'
import Spinner from '../components/ui/Spinner'
import ErrorAlert from '../components/ui/ErrorAlert'
import StatusBadge from '../components/ui/StatusBadge'
import EmptyState from '../components/ui/EmptyState'
import api from '../services/api'
import { formatLatency } from '../utils/format'

// ── API helpers ───────────────────────────────────────────────────────────
const uploadDocument = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  }).then(r => r.data)
}
const fetchDocuments = () => api.get('/documents').then(r => r.data)
const deleteDocument = (id) => api.delete(`/documents/${id}`)
const queryRAG = (body) => api.post('/rag/query', body).then(r => r.data)
const fetchRAGStatus = () => api.get('/rag/status').then(r => r.data)

// ── Documents tab ─────────────────────────────────────────────────────────
function DocumentsTab() {
  const [docs, setDocs]           = useState([])
  const [loading, setLoading]     = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError]         = useState(null)
  const [status, setStatus]       = useState(null)
  const fileRef = useRef()

  const load = useCallback(async () => {
    try {
      const [d, s] = await Promise.all([fetchDocuments(), fetchRAGStatus()])
      setDocs(d.documents || [])
      setStatus(s)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      await uploadDocument(file)
      await load()
    } catch (e) {
      setError(e.message)
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this document and all its vectors?')) return
    try {
      await deleteDocument(id)
      setDocs(prev => prev.filter(d => d.id !== id))
    } catch (e) {
      setError(e.message)
    }
  }

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1048576) return `${(bytes/1024).toFixed(1)} KB`
    return `${(bytes/1048576).toFixed(1)} MB`
  }

  return (
    <div className="space-y-4">
      {/* Stats */}
      {status && (
        <div className="grid grid-cols-2 gap-3">
          <div className="card-sm text-center">
            <p className="text-2xl font-bold text-white">{status.documents_indexed}</p>
            <p className="text-xs text-gray-500">Documents indexed</p>
          </div>
          <div className="card-sm text-center">
            <p className="text-2xl font-bold text-white">{status.total_chunks}</p>
            <p className="text-xs text-gray-500">Total chunks in store</p>
          </div>
        </div>
      )}

      {/* Upload */}
      <div className="card">
        <p className="text-sm font-semibold text-gray-200 mb-3">Upload Document</p>
        <p className="text-xs text-gray-500 mb-3">Supported: PDF, TXT, Markdown · Max 10 MB</p>
        {error && <div className="mb-3"><ErrorAlert message={error} onDismiss={() => setError(null)} /></div>}
        <div className="flex items-center gap-3">
          <button onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="btn-primary flex items-center gap-2 text-sm">
            {uploading ? <><Spinner size="sm" />Processing…</> : '📄 Choose File'}
          </button>
          <input ref={fileRef} type="file" accept=".pdf,.txt,.md" className="hidden" onChange={handleUpload} />
          {uploading && <span className="text-xs text-gray-400">Extracting → Chunking → Embedding… (may take 10-30s)</span>}
        </div>
      </div>

      {/* Document list */}
      {loading ? (
        <div className="flex items-center gap-2 text-gray-500"><Spinner /><span className="text-sm">Loading…</span></div>
      ) : docs.length === 0 ? (
        <EmptyState icon="📄" title="No documents yet"
          description="Upload a PDF, TXT, or Markdown file to start building your knowledge base." />
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800">
                {['Filename', 'Type', 'Size', 'Chunks', 'Status', ''].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {docs.map(d => (
                <tr key={d.id} className="border-b border-gray-800 last:border-0 hover:bg-gray-800/30">
                  <td className="px-4 py-3">
                    <p className="text-sm font-medium text-gray-200">{d.original_filename}</p>
                    <p className="text-xs text-gray-600 font-mono">{d.id.slice(0, 8)}</p>
                  </td>
                  <td className="px-4 py-3"><span className="badge badge-blue">{d.file_type}</span></td>
                  <td className="px-4 py-3 text-xs text-gray-400">{formatSize(d.file_size)}</td>
                  <td className="px-4 py-3 text-sm text-gray-300">{d.chunk_count}</td>
                  <td className="px-4 py-3"><StatusBadge status={d.status} /></td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => handleDelete(d.id)}
                      className="text-xs text-red-500 hover:text-red-300">delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ── Query tab ─────────────────────────────────────────────────────────────
function QueryTab() {
  const [question, setQuestion] = useState('What is the refund policy for digital goods?')
  const [provider, setProvider] = useState('mock')
  const [topK, setTopK]         = useState(5)
  const [loading, setLoading]   = useState(false)
  const [result, setResult]     = useState(null)
  const [error, setError]       = useState(null)

  const handleQuery = async () => {
    if (!question.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const r = await queryRAG({ question, provider, top_k: topK })
      setResult(r)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="card-sm bg-brand-900/10 border-brand-700/30 text-xs text-brand-300">
        🔍 Retrieved chunks are injected with <code>&lt;context&gt;</code> delimiters to prevent
        indirect prompt injection. The model is instructed to answer only from context.
      </div>

      <div className="card space-y-3">
        <div>
          <label className="label">Question</label>
          <textarea className="input text-sm resize-none" rows={3} value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => { if ((e.ctrlKey||e.metaKey) && e.key==='Enter') handleQuery() }}
            placeholder="Ask anything about your uploaded documents… (Ctrl+Enter to run)" />
        </div>
        <div className="flex gap-3">
          <div>
            <label className="label">Provider</label>
            <select className="input text-sm w-36" value={provider} onChange={e => setProvider(e.target.value)}>
              {['mock','openai','anthropic','gemini','mistral'].map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Top-K chunks</label>
            <input type="number" min="1" max="10" className="input text-sm w-20"
              value={topK} onChange={e => setTopK(parseInt(e.target.value)||5)} />
          </div>
        </div>

        {error && <ErrorAlert message={error} />}

        <button onClick={handleQuery} disabled={loading || !question.trim()}
          className="btn-primary flex items-center gap-2">
          {loading ? <><Spinner size="sm" />Searching & generating…</> : '🔍 Ask'}
        </button>
      </div>

      {result && (
        <div className="space-y-3">
          {/* Answer */}
          <div className="card">
            <div className="flex items-center gap-3 mb-3 text-xs text-gray-500">
              <span className="badge badge-blue">{result.provider}</span>
              <span>{formatLatency(result.latency_ms)}</span>
              <span>{result.chunks_retrieved} chunks retrieved</span>
            </div>
            <p className="text-sm font-semibold text-gray-400 mb-2">Answer</p>
            <pre className="text-sm text-gray-200 whitespace-pre-wrap font-sans leading-relaxed">
              {result.answer}
            </pre>
          </div>

          {/* Sources */}
          {result.sources.length > 0 && (
            <div className="card">
              <p className="text-sm font-semibold text-gray-400 mb-3">
                Sources ({result.sources.length})
              </p>
              <div className="space-y-2">
                {result.sources.map((s, i) => (
                  <div key={s.chunk_id} className="border border-gray-800 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="badge badge-gray text-xs">#{i+1}</span>
                      <span className="text-sm font-medium text-gray-300">{s.filename}</span>
                      {s.page && <span className="text-xs text-gray-500">page {s.page}</span>}
                      <span className="text-xs text-gray-500">chunk {s.chunk_index}</span>
                      <span className={`text-xs font-mono ml-auto ${s.relevance_score > 0.6 ? 'text-green-400' : 'text-yellow-400'}`}>
                        {(s.relevance_score * 100).toFixed(0)}% match
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 leading-relaxed">{s.content_preview}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────
export default function RAGLab() {
  const [tab, setTab] = useState('documents')

  return (
    <div className="p-6 max-w-4xl">
      <PageHeader
        title="RAG Lab"
        subtitle="Upload documents, build a vector index, and get answers with source citations."
      />

      <div className="flex gap-1 mb-6 bg-gray-900 rounded-lg p-1 w-fit border border-gray-800">
        {[{ id:'documents', label:'📄 Documents' }, { id:'query', label:'🔍 Query' }].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              tab === t.id ? 'bg-brand-600 text-white' : 'text-gray-400 hover:text-gray-200'
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'documents' && <DocumentsTab />}
      {tab === 'query'     && <QueryTab />}
    </div>
  )
}
