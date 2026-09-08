/**
 * Dashboard page — Phase 1 implementation.
 *
 * Shows:
 *  - Backend health status (live)
 *  - Provider configuration status (live)
 *  - Placeholder metric cards (will show real data from Phase 6+)
 *
 * Phase 11 will add Recharts visualisations.
 */

import PageHeader from '../components/ui/PageHeader'
import StatusBadge from '../components/ui/StatusBadge'
import Spinner from '../components/ui/Spinner'
import ErrorAlert from '../components/ui/ErrorAlert'
import { useHealth } from '../hooks/useHealth'
import { useProviders } from '../hooks/useProviders'

// ── Metric card (placeholder until real data exists) ──────────────────────
function MetricCard({ label, value, sub, icon }) {
  return (
    <div className="card flex items-start gap-4">
      <div className="w-10 h-10 rounded-lg bg-gray-800 flex items-center justify-center text-xl flex-shrink-0">
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-sm font-medium text-gray-300">{label}</p>
        {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

// ── Provider row ──────────────────────────────────────────────────────────
function ProviderRow({ provider }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-800 last:border-0">
      <div>
        <p className="text-sm font-medium text-gray-200">{provider.name}</p>
        <p className="text-xs text-gray-500">{provider.default_model}</p>
      </div>
      <StatusBadge status={provider.status} />
    </div>
  )
}

// ── Health detail row ─────────────────────────────────────────────────────
function HealthRow({ label, value, ok }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
      <span className="text-sm text-gray-400">{label}</span>
      <span className={`text-sm font-mono ${ok ? 'text-green-400' : 'text-red-400'}`}>
        {value}
      </span>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────
export default function Dashboard() {
  const { health, loading: hLoading, error: hError, refetch: hRefetch } = useHealth(30_000)
  const { providers, loading: pLoading, error: pError } = useProviders()

  const configuredCount = providers.filter((p) => p.configured).length

  return (
    <div className="p-6 max-w-6xl">
      <PageHeader
        title="Dashboard"
        subtitle="PromptLab system overview — health, providers, and experiment metrics."
        actions={
          <button onClick={hRefetch} className="btn-secondary text-xs px-3 py-1.5">
            ↻ Refresh
          </button>
        }
      />

      {/* ── Health error ── */}
      {hError && (
        <ErrorAlert
          message={hError}
          onDismiss={hRefetch}
        />
      )}

      {/* ── Metric cards (placeholders — real data in Phase 6+) ── */}
      <section className="mb-8">
        <h2 className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-3">
          Metrics (demo data — real counts coming in Phase 6)
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard icon="📝" label="Total Prompts"     value="—" sub="Phase 4" />
          <MetricCard icon="🔀" label="Prompt Versions"   value="—" sub="Phase 6" />
          <MetricCard icon="🧪" label="Experiments"       value="—" sub="Phase 6" />
          <MetricCard icon="📋" label="Test Cases"        value="—" sub="Phase 7" />
          <MetricCard icon="🎯" label="Avg Accuracy"      value="—" sub="Phase 7" />
          <MetricCard icon="💡" label="Avg Relevance"     value="—" sub="Phase 7" />
          <MetricCard icon="🛡️" label="Avg Safety Score"  value="—" sub="Phase 8" />
          <MetricCard icon="🔍" label="RAG Experiments"   value="—" sub="Phase 9" />
        </div>
      </section>

      {/* ── Two-column: health + providers ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Backend health */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-200">Backend Status</h2>
            {hLoading && <Spinner size="sm" />}
          </div>

          {health ? (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <StatusBadge status={health.status} />
                <span className="text-xs text-gray-500">v{health.version}</span>
              </div>
              <HealthRow label="Environment" value={health.environment}  ok />
              <HealthRow label="Database"    value={health.database}     ok={health.database === 'ok'} />
              <HealthRow label="Uptime"      value={`${health.uptime_seconds}s`} ok />
            </div>
          ) : !hLoading && (
            <p className="text-sm text-gray-500">
              Backend not reachable. Make sure <code className="text-brand-400">uvicorn app.main:app</code> is running on port 8000.
            </p>
          )}
        </div>

        {/* Provider status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-200">LLM Providers</h2>
            {pLoading ? (
              <Spinner size="sm" />
            ) : (
              <span className="text-xs text-gray-500">
                {configuredCount}/{providers.length} configured
              </span>
            )}
          </div>

          {pError && <ErrorAlert message={pError} />}

          {providers.length > 0 ? (
            providers.map((p) => <ProviderRow key={p.id} provider={p} />)
          ) : !pLoading && (
            <p className="text-sm text-gray-500">No providers loaded.</p>
          )}
        </div>
      </div>

      {/* ── Getting started callout ── */}
      <div className="mt-6 card border-brand-700/40 bg-brand-900/10">
        <h3 className="text-sm font-semibold text-brand-300 mb-2">🚀 Getting Started</h3>
        <ol className="text-sm text-gray-400 space-y-1 list-decimal list-inside">
          <li>Copy <code className="text-brand-400">.env.example</code> → <code className="text-brand-400">.env</code> and add at least one API key.</li>
          <li>The <strong className="text-gray-300">Mock</strong> provider works without any key — great for testing the UI.</li>
          <li>Head to <strong className="text-gray-300">Playground</strong> to run your first prompt (Phase 4).</li>
          <li>Use <strong className="text-gray-300">Evaluation</strong> to measure prompt quality (Phase 7).</li>
        </ol>
      </div>
    </div>
  )
}
