/**
 * Dashboard — Phase 11 (live stats + charts)
 *
 * Shows:
 *  - Live backend health + provider status
 *  - Real experiment/prompt counts from the API
 *  - Provider breakdown bar chart (Recharts)
 *  - Getting-started guide
 */

import { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import PageHeader from '../components/ui/PageHeader'
import StatusBadge from '../components/ui/StatusBadge'
import Spinner from '../components/ui/Spinner'
import ErrorAlert from '../components/ui/ErrorAlert'
import { useHealth } from '../hooks/useHealth'
import { useProviders } from '../hooks/useProviders'
import { fetchStats } from '../services/api'

// ── Metric card ───────────────────────────────────────────────────────────
function StatCard({ icon, label, value, sub }) {
  return (
    <div className="card flex items-start gap-4">
      <div className="w-10 h-10 rounded-lg bg-gray-800 flex items-center justify-center text-xl flex-shrink-0">
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value ?? '—'}</p>
        <p className="text-sm font-medium text-gray-300">{label}</p>
        {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

const BAR_COLOURS = ['#6175f3','#10b981','#f59e0b','#ef4444','#a855f7']

// ── Main page ─────────────────────────────────────────────────────────────
export default function Dashboard() {
  const { health, loading: hLoading, error: hError, refetch } = useHealth(30_000)
  const { providers, loading: pLoading } = useProviders()

  const [stats, setStats]         = useState(null)
  const [statsLoading, setStatsLoading] = useState(true)

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setStatsLoading(false))
  }, [])

  const configuredCount = providers.filter(p => p.configured).length
  const chartData = stats?.provider_breakdown ?? []

  return (
    <div className="p-6 max-w-6xl">
      <PageHeader
        title="Dashboard"
        subtitle="PromptLab system overview — health, providers, and experiment metrics."
        actions={
          <button onClick={refetch} className="btn-secondary text-xs px-3 py-1.5">↻ Refresh</button>
        }
      />

      {hError && <div className="mb-4"><ErrorAlert message={hError} /></div>}

      {/* ── Metric cards ── */}
      <section className="mb-8">
        <h2 className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-3">Overview</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard icon="📝" label="Total Prompts"    value={stats?.total_prompts}    sub="saved prompts" />
          <StatCard icon="🔀" label="Prompt Versions"  value={stats?.total_versions}   sub="across all prompts" />
          <StatCard icon="🧪" label="Experiments"      value={stats?.total_experiments} sub="recorded runs" />
          <StatCard icon="⏱"  label="Avg Latency"
            value={stats?.avg_latency_ms ? `${stats.avg_latency_ms}ms` : null}
            sub="per LLM call" />
        </div>
      </section>

      {/* ── Charts + status ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Provider usage chart */}
        <div className="card">
          <p className="text-sm font-semibold text-gray-200 mb-4">Experiments by Provider</p>
          {statsLoading ? (
            <div className="flex items-center gap-2 text-gray-500 h-32"><Spinner size="sm" /><span className="text-sm">Loading…</span></div>
          ) : chartData.length === 0 ? (
            <div className="flex items-center justify-center h-32 text-gray-600 text-sm">
              No experiments yet — run a prompt to see data here.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <XAxis dataKey="provider" tick={{ fill: '#6b7280', fontSize: 12 }} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8, color: '#e5e7eb' }}
                  cursor={{ fill: 'rgba(255,255,255,0.04)' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {chartData.map((_, i) => (
                    <Cell key={i} fill={BAR_COLOURS[i % BAR_COLOURS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Provider status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm font-semibold text-gray-200">LLM Providers</p>
            {pLoading ? <Spinner size="sm" /> : (
              <span className="text-xs text-gray-500">{configuredCount}/{providers.length} configured</span>
            )}
          </div>
          {providers.map(p => (
            <div key={p.id} className="flex items-center justify-between py-2.5 border-b border-gray-800 last:border-0">
              <div>
                <p className="text-sm font-medium text-gray-200">{p.name}</p>
                <p className="text-xs text-gray-500 font-mono">{p.default_model}</p>
              </div>
              <StatusBadge status={p.status} />
            </div>
          ))}
        </div>
      </div>

      {/* ── Backend health ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-semibold text-gray-200">Backend Health</p>
            {hLoading && <Spinner size="sm" />}
          </div>
          {health ? (
            <>
              <div className="flex items-center gap-3 mb-3">
                <StatusBadge status={health.status} />
                <span className="text-xs text-gray-500">v{health.version} · {health.environment}</span>
              </div>
              {[['Database', health.database, health.database === 'ok'],
                ['Uptime', `${health.uptime_seconds}s`, true],
              ].map(([k, v, ok]) => (
                <div key={k} className="flex justify-between py-1.5 border-b border-gray-800 last:border-0 text-sm">
                  <span className="text-gray-500">{k}</span>
                  <span className={`font-mono ${ok ? 'text-green-400' : 'text-red-400'}`}>{v}</span>
                </div>
              ))}
            </>
          ) : !hLoading && (
            <p className="text-sm text-gray-500">
              Backend not reachable. Start it with:{' '}
              <code className="text-brand-400 text-xs">uvicorn app.main:app --reload</code>
            </p>
          )}
        </div>

        {/* Getting started */}
        <div className="card border-brand-700/40 bg-brand-900/10">
          <p className="text-sm font-semibold text-brand-300 mb-3">🚀 Quick Start</p>
          <ol className="text-sm text-gray-400 space-y-2 list-decimal list-inside">
            <li>Go to <strong className="text-gray-200">Playground</strong> → run a prompt with Mock provider</li>
            <li>Go to <strong className="text-gray-200">Evaluation</strong> → evaluate the response</li>
            <li>Go to <strong className="text-gray-200">Prompt Library</strong> → save and version your prompt</li>
            <li>Go to <strong className="text-gray-200">Safety Lab</strong> → test injection defences</li>
            <li>Add an API key to <code className="text-brand-400">.env</code> to use real LLMs</li>
          </ol>
        </div>
      </div>
    </div>
  )
}
