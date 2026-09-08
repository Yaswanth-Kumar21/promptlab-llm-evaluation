/**
 * Prompt Playground — implemented in Phase 4.
 */
import PageHeader from '../components/ui/PageHeader'
import EmptyState from '../components/ui/EmptyState'

export default function Playground() {
  return (
    <div className="p-6">
      <PageHeader title="Prompt Playground" subtitle="Run prompts against any configured LLM provider." />
      <EmptyState
        icon="⚡"
        title="Coming in Phase 4"
        description="The Playground lets you enter a system prompt, user prompt, temperature, and max tokens — then run it against any provider and see the response with latency and token counts."
      />
    </div>
  )
}
