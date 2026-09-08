/**
 * Settings page.
 *
 * Phase 1: Shows provider configuration status and API documentation links.
 * Later phases will add provider selection, theme toggles, etc.
 */

import PageHeader from '../components/ui/PageHeader'
import StatusBadge from '../components/ui/StatusBadge'
import Spinner from '../components/ui/Spinner'
import ErrorAlert from '../components/ui/ErrorAlert'
import { useProviders } from '../hooks/useProviders'
import { useHealth } from '../hooks/useHealth'

export default function Settings() {
  const { providers, defaultProvider, loading, error } = useProviders()
  const { health } = useHealth(60_000)

  return (
    <div className="p-6 max-w-3xl">
      <PageHeader
        title="Settings"
        subtitle="Provider configuration, API status, and environment information."
      />

      {/* ── Provider configuration ── */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
          LLM Provider Configuration
        </h2>

        {error && <ErrorAlert message={error} />}
        {loading && <div className="flex items-center gap-2 text-gray-500"><Spinner size="sm" /><span className="text-sm">Loading providers…</span></div>}

        {!loading && !error && (
          <div className="card space-y-0 divide-y divide-gray-800">
            {providers.map((p) => (
              <div key={p.id} className="py-4 flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-sm font-medium text-gray-200">{p.name}</p>
                    {p.id === defaultProvider && (
                      <span className="badge badge-blue">default</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mb-2">{p.description}</p>
                  <p className="text-xs text-gray-600 font-mono">
                    Default model: {p.default_model}
                  </p>
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {p.models.map((m) => (
                      <span key={m} className="badge badge-gray font-mono">{m}</span>
                    ))}
                  </div>
                </div>
                <StatusBadge status={p.status} />
              </div>
            ))}
          </div>
        )}

        <div className="mt-3 card-sm bg-yellow-900/10 border-yellow-800/40">
          <p className="text-xs text-yellow-400 font-medium mb-1">⚠ How to configure a provider</p>
          <p className="text-xs text-gray-400">
            Add the provider's API key to your <code className="text-yellow-300">.env</code> file
            (e.g. <code className="text-yellow-300">OPENAI_API_KEY=sk-…</code>) and restart the backend.
            API keys are never stored in the database or returned by the API.
          </p>
        </div>
      </section>

      {/* ── System information ── */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
          System Information
        </h2>
        <div className="card space-y-3">
          <Row label="Backend version"  value={health?.version ?? '—'} />
          <Row label="Environment"      value={health?.environment ?? '—'} />
          <Row label="Database"         value={health?.database ?? '—'} />
          <Row label="Backend status"   value={health?.status ?? '—'} />
          <Row label="Uptime"           value={health ? `${health.uptime_seconds}s` : '—'} />
        </div>
      </section>

      {/* ── API links ── */}
      <section>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
          API Documentation
        </h2>
        <div className="card space-y-2">
          <ApiLink href="http://localhost:8000/docs"        label="Swagger UI"         desc="Interactive API explorer" />
          <ApiLink href="http://localhost:8000/redoc"       label="ReDoc"              desc="Readable API reference" />
          <ApiLink href="http://localhost:8000/openapi.json"label="OpenAPI JSON"       desc="Machine-readable schema" />
          <ApiLink href="http://localhost:8000/api/health"  label="Health Endpoint"    desc="GET /api/health" />
          <ApiLink href="http://localhost:8000/api/providers" label="Providers Endpoint" desc="GET /api/providers" />
        </div>
      </section>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="text-gray-300 font-mono">{value}</span>
    </div>
  )
}

function ApiLink({ href, label, desc }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center justify-between py-2 hover:bg-gray-800 -mx-2 px-2 rounded-lg transition-colors"
    >
      <div>
        <p className="text-sm font-medium text-brand-400">{label}</p>
        <p className="text-xs text-gray-500">{desc}</p>
      </div>
      <span className="text-gray-600 text-xs">↗</span>
    </a>
  )
}
