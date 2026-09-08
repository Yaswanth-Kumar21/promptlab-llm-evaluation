/**
 * Safety Lab — implemented in Phase 8.
 */
import PageHeader from '../components/ui/PageHeader'
import EmptyState from '../components/ui/EmptyState'

export default function SafetyLab() {
  return (
    <div className="p-6">
      <PageHeader title="Safety Lab" subtitle="Prompt injection testing, hallucination detection, and bias evaluation." />
      <EmptyState
        icon="🛡️"
        title="Coming in Phase 8"
        description="Test your prompts against injection attacks, check for unsupported claims (hallucinations), and evaluate for demographic bias using controlled test cases."
      />
    </div>
  )
}
