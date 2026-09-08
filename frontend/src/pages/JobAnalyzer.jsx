/**
 * AI Job Application Analyzer — implemented in Phase 12.
 */
import PageHeader from '../components/ui/PageHeader'
import EmptyState from '../components/ui/EmptyState'

export default function JobAnalyzer() {
  return (
    <div className="p-6">
      <PageHeader title="AI Job Application Analyzer" subtitle="Match a resume against a job description using structured prompting." />
      <EmptyState
        icon="💼"
        title="Coming in Phase 12"
        description="Paste a resume and job description. The system returns a match score, matched skills with evidence, missing skills, and a recommendation — without inventing skills."
      />
    </div>
  )
}
