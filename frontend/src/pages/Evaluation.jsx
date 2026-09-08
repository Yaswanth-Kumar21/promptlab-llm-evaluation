/**
 * Evaluation — implemented in Phase 7.
 */
import PageHeader from '../components/ui/PageHeader'
import EmptyState from '../components/ui/EmptyState'

export default function Evaluation() {
  return (
    <div className="p-6">
      <PageHeader title="Evaluation" subtitle="Run accuracy, relevance, tone, consistency, and safety evaluations." />
      <EmptyState
        icon="📊"
        title="Coming in Phase 7"
        description="Run structured evaluation datasets against any prompt version. Each response is scored on accuracy, relevance, tone, consistency, JSON validity, and safety."
      />
    </div>
  )
}
