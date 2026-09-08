/**
 * RAG Lab — implemented in Phase 9.
 */
import PageHeader from '../components/ui/PageHeader'
import EmptyState from '../components/ui/EmptyState'

export default function RAGLab() {
  return (
    <div className="p-6">
      <PageHeader title="RAG Lab" subtitle="Upload documents, build a vector index, and run retrieval-augmented generation." />
      <EmptyState
        icon="🔍"
        title="Coming in Phase 9"
        description="Upload PDFs, TXT, or Markdown files. The system chunks and embeds them into ChromaDB. Then ask questions and get answers with source citations."
      />
    </div>
  )
}
