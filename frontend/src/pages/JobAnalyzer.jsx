/**
 * AI Job Application Analyzer — Phase 12
 *
 * Structured prompting demo: resume vs job description.
 * Shows match score, matched skills with evidence, missing skills,
 * and a recommendation.
 */

import { useState } from 'react'
import PageHeader from '../components/ui/PageHeader'
import Spinner from '../components/ui/Spinner'
import ErrorAlert from '../components/ui/ErrorAlert'
import ScoreBar from '../components/ui/ScoreBar'
import api from '../services/api'
import { formatLatency } from '../utils/format'

const analyzeJob = (body) => api.post('/job/analyze', body).then(r => r.data)

// ── Demo data ─────────────────────────────────────────────────────────────
const DEMO_RESUME = `John Smith
Software Engineer

SKILLS
- Python (5 years): FastAPI, Django, Flask
- JavaScript / React (3 years)
- SQL: PostgreSQL, MySQL
- Git, Docker basics
- REST API design and development
- Machine learning: scikit-learn, pandas, numpy

EXPERIENCE
Senior Software Engineer — TechCorp (2022–present)
- Built and deployed REST APIs using FastAPI serving 50k daily requests
- Implemented data pipelines using Python and pandas
- Collaborated with ML team to integrate scikit-learn models into production

Software Engineer — StartupXYZ (2020–2022)
- Developed React frontend with TypeScript
- Maintained PostgreSQL database schemas and wrote complex SQL queries

EDUCATION
B.Tech Computer Science — State University (2020)`

const DEMO_JD = `Senior Python Engineer — AI Products Team

We are looking for a Python engineer to build AI-powered features.

Required Skills:
- Python (3+ years)
- FastAPI or similar REST framework
- PostgreSQL
- Machine learning fundamentals
- Docker
- Git

Nice to Have:
- Kubernetes
- LLM API experience (OpenAI, Anthropic)
- React/TypeScript

Responsibilities:
- Build and maintain REST APIs
- Integrate ML models into production systems
- Work with PostgreSQL databases`

// ── Result display ────────────────────────────────────────────────────────
function AnalysisResult({ data }) {
  const r = data.result
  if (!r || Object.keys(r).length === 0) {
    return (
      <div className="card border-yellow-800/40">
        <p className="text-yellow-400 text-sm font-medium mb-2">⚠ JSON parsing issue</p>
        <p className="text-gray-400 text-xs mb-2">{data.json_validation?.reason}</p>
        <pre className="text-xs text-gray-500 bg-gray-950 rounded p-2 overflow-x-auto max-h-40">
          {data.raw_response}
        </pre>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Score card */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Match Score</p>
            <p className={`text-4xl font-bold mt-1 ${
              r.match_score >= 70 ? 'text-green-400' :
              r.match_score >= 40 ? 'text-yellow-400' : 'text-red-400'
            }`}>{r.match_score}%</p>
          </div>
          <div className="text-right">
            <span className="badge badge-blue">{data.provider}</span>
            <p className="text-xs text-gray-500 mt-1">{formatLatency(data.latency_ms)}</p>
            <p className="text-xs text-gray-600 mt-0.5">
              {data.json_valid ? '✓ valid JSON' : '⚠ JSON repair used'}
            </p>
          </div>
        </div>
        <ScoreBar score={r.match_score} />
        {r.recommendation && (
          <p className="text-sm text-gray-300 mt-3 pt-3 border-t border-gray-800">
            💡 {r.recommendation}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Matched skills */}
        <div className="card">
          <p className="text-sm font-semibold text-green-400 mb-3">
            ✓ Matched Skills ({r.matched_skills?.length ?? 0})
          </p>
          {r.matched_skills?.length > 0 ? (
            <div className="space-y-2">
              {r.matched_skills.map((s, i) => (
                <div key={i} className="bg-green-900/10 border border-green-800/30 rounded-lg p-3">
                  <p className="text-sm font-medium text-green-300">{s.skill}</p>
                  <p className="text-xs text-gray-500 mt-1 italic">"{s.evidence}"</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-500">No matching skills found.</p>
          )}
        </div>

        {/* Missing skills */}
        <div className="card">
          <p className="text-sm font-semibold text-red-400 mb-3">
            ✗ Missing Skills ({r.missing_skills?.length ?? 0})
          </p>
          {r.missing_skills?.length > 0 ? (
            <div className="space-y-1.5">
              {r.missing_skills.map((s, i) => (
                <div key={i} className="flex items-center gap-2 px-3 py-2 bg-red-900/10 border border-red-800/30 rounded-lg">
                  <span className="text-red-400 text-xs">✗</span>
                  <span className="text-sm text-red-300">{s}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-500">No missing required skills.</p>
          )}
        </div>
      </div>

      {/* Strengths */}
      {r.strengths?.length > 0 && (
        <div className="card">
          <p className="text-sm font-semibold text-brand-300 mb-3">⭐ Strengths</p>
          <ul className="space-y-1">
            {r.strengths.map((s, i) => (
              <li key={i} className="text-sm text-gray-300">• {s}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Prompt engineering notes */}
      <div className="card-sm bg-gray-800/50 border-gray-700">
        <p className="text-xs text-gray-500 font-semibold mb-1">Prompt Engineering Notes</p>
        <div className="text-xs text-gray-600 space-y-0.5">
          <p>Technique: {data.prompt_notes?.technique}</p>
          <p>Temperature: {data.prompt_notes?.temperature} (deterministic)</p>
          <p>Hallucination prevention: {data.prompt_notes?.hallucination_prevention}</p>
          <p>JSON repair: {data.json_repair_attempted ? 'was needed' : 'not needed'}</p>
        </div>
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────
export default function JobAnalyzer() {
  const [resume, setResume]   = useState(DEMO_RESUME)
  const [jd, setJd]           = useState(DEMO_JD)
  const [provider, setProvider] = useState('mock')
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)
  const [error, setError]     = useState(null)

  const handleAnalyze = async () => {
    if (!resume.trim() || !jd.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const r = await analyzeJob({ resume, job_description: jd, provider })
      setResult(r)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-5xl">
      <PageHeader
        title="AI Job Application Analyzer"
        subtitle="Structured prompting demo — matches resume skills against a job description with evidence. No skill invention."
      />

      <div className="card-sm bg-brand-900/10 border-brand-700/30 text-xs text-brand-300 mb-5">
        🏗️ <strong>Prompt technique:</strong> Structured JSON output + explicit grounding rules.
        Every matched skill requires a direct quote from the resume as evidence.
        The model cannot invent skills — if it's not in the resume, it goes to "missing".
      </div>

      <div className="flex gap-4 mb-4">
        <div className="flex-1">
          <label className="label">Resume</label>
          <textarea className="input text-sm font-mono resize-none" rows={18}
            value={resume} onChange={e => setResume(e.target.value)} />
        </div>
        <div className="flex-1">
          <label className="label">Job Description</label>
          <textarea className="input text-sm font-mono resize-none" rows={18}
            value={jd} onChange={e => setJd(e.target.value)} />
        </div>
      </div>

      <div className="flex items-center gap-4 mb-6">
        <div>
          <label className="label">Provider</label>
          <select className="input text-sm w-36" value={provider} onChange={e => setProvider(e.target.value)}>
            {['mock','openai','anthropic','gemini','mistral'].map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        {error && <div className="flex-1"><ErrorAlert message={error} onDismiss={() => setError(null)} /></div>}
        <button onClick={handleAnalyze}
          disabled={loading || !resume.trim() || !jd.trim()}
          className="btn-primary text-base px-6 py-3 flex items-center gap-2 self-end">
          {loading ? <><Spinner size="sm" />Analyzing…</> : '💼 Analyze Match'}
        </button>
      </div>

      {result && <AnalysisResult data={result} />}
    </div>
  )
}
