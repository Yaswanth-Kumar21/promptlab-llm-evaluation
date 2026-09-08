/**
 * Prompt Library — implemented in Phase 4 / Phase 5.
 */
import PageHeader from '../components/ui/PageHeader'
import EmptyState from '../components/ui/EmptyState'

export default function PromptLibrary() {
  return (
    <div className="p-6">
      <PageHeader title="Prompt Library" subtitle="Browse, create, and manage reusable prompts." />
      <EmptyState
        icon="📚"
        title="Coming in Phase 4"
        description="The Prompt Library stores all your prompts with categories (zero-shot, few-shot, structured, RAG, safety), tags, and version history."
      />
    </div>
  )
}
