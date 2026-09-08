/**
 * Prompt Versions — implemented in Phase 6.
 */
import PageHeader from '../components/ui/PageHeader'
import EmptyState from '../components/ui/EmptyState'

export default function PromptVersions() {
  return (
    <div className="p-6">
      <PageHeader title="Prompt Versions" subtitle="Compare and manage prompt versions side by side." />
      <EmptyState
        icon="🔀"
        title="Coming in Phase 6"
        description="Track every edit as a named version. Compare V1 vs V2 vs V3 on the same dataset. Mark the best version."
      />
    </div>
  )
}
