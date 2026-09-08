/**
 * Experiments — implemented in Phase 6 / Phase 11.
 */
import PageHeader from '../components/ui/PageHeader'
import EmptyState from '../components/ui/EmptyState'

export default function Experiments() {
  return (
    <div className="p-6">
      <PageHeader title="Experiments" subtitle="Browse full experiment history with scores and comparisons." />
      <EmptyState
        icon="🧪"
        title="Coming in Phase 6"
        description="Every prompt run is saved as an experiment: provider, model, temperature, response, latency, token usage, and all evaluation scores."
      />
    </div>
  )
}
