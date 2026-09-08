/**
 * PromptLab — Root application component.
 *
 * Sets up React Router with the sidebar layout and all 11 page routes.
 * Every page that isn't implemented yet shows a clear "Coming in Phase X"
 * placeholder — no broken routes or blank screens.
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom'

import Layout        from './components/layout/Layout'
import Dashboard     from './pages/Dashboard'
import Playground    from './pages/Playground'
import PromptLibrary from './pages/PromptLibrary'
import PromptVersions from './pages/PromptVersions'
import Experiments   from './pages/Experiments'
import Evaluation    from './pages/Evaluation'
import RAGLab        from './pages/RAGLab'
import SafetyLab     from './pages/SafetyLab'
import JobAnalyzer   from './pages/JobAnalyzer'
import KnowledgeBase from './pages/KnowledgeBase'
import Settings      from './pages/Settings'

// ── 404 fallback ──────────────────────────────────────────────────────────
function NotFound() {
  return (
    <div className="p-6 flex flex-col items-center justify-center h-64">
      <p className="text-5xl mb-4">🔭</p>
      <h1 className="text-xl font-bold text-white mb-2">404 — Page Not Found</h1>
      <p className="text-gray-500 text-sm">The page you're looking for doesn't exist.</p>
    </div>
  )
}

// ── App ───────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/"              element={<Dashboard />} />
          <Route path="/playground"    element={<Playground />} />
          <Route path="/library"       element={<PromptLibrary />} />
          <Route path="/versions"      element={<PromptVersions />} />
          <Route path="/experiments"   element={<Experiments />} />
          <Route path="/evaluation"    element={<Evaluation />} />
          <Route path="/rag"           element={<RAGLab />} />
          <Route path="/safety"        element={<SafetyLab />} />
          <Route path="/job-analyzer"  element={<JobAnalyzer />} />
          <Route path="/knowledge-base" element={<KnowledgeBase />} />
          <Route path="/settings"      element={<Settings />} />
          <Route path="*"             element={<NotFound />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
