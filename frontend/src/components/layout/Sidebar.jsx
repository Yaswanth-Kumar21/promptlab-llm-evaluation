/**
 * Sidebar navigation component.
 *
 * Contains links for all 11 pages.
 * Shows a live backend status indicator using useHealth.
 * Collapses to icons-only on small screens (future improvement marker).
 */

import { NavLink } from 'react-router-dom'
import { useHealth } from '../../hooks/useHealth'

// ── Navigation items ────────────────────────────────────────────────────────
const NAV_ITEMS = [
  {
    section: 'Core',
    items: [
      { to: '/',           label: 'Dashboard',      icon: '▤' },
      { to: '/playground', label: 'Playground',     icon: '⚡' },
      { to: '/techniques', label: 'Techniques',     icon: '🔬' },
      { to: '/library',    label: 'Prompt Library', icon: '📚' },
      { to: '/versions',   label: 'Versions',       icon: '🔀' },
      { to: '/experiments',label: 'Experiments',    icon: '🧪' },
    ],
  },
  {
    section: 'Evaluation',
    items: [
      { to: '/evaluation', label: 'Evaluation',     icon: '📊' },
      { to: '/rag',        label: 'RAG Lab',        icon: '🔍' },
      { to: '/safety',     label: 'Safety Lab',     icon: '🛡️' },
    ],
  },
  {
    section: 'Tools',
    items: [
      { to: '/job-analyzer',  label: 'Job Analyzer',    icon: '💼' },
      { to: '/knowledge-base',label: 'Knowledge Base',  icon: '🎓' },
      { to: '/settings',      label: 'Settings',        icon: '⚙️' },
    ],
  },
]

// ── Status indicator ────────────────────────────────────────────────────────
function BackendStatus() {
  const { health, loading, error } = useHealth(30_000)

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span className="w-2 h-2 rounded-full bg-gray-600 animate-pulse" />
        Connecting…
      </div>
    )
  }

  if (error || !health) {
    return (
      <div className="flex items-center gap-2 text-xs text-red-400">
        <span className="w-2 h-2 rounded-full bg-red-500" />
        Backend offline
      </div>
    )
  }

  const isHealthy = health.status === 'healthy'
  return (
    <div className={`flex items-center gap-2 text-xs ${isHealthy ? 'text-green-400' : 'text-yellow-400'}`}>
      <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-yellow-500'}`} />
      {isHealthy ? 'Backend healthy' : 'Backend degraded'}
    </div>
  )
}

// ── Sidebar component ───────────────────────────────────────────────────────
export default function Sidebar() {
  return (
    <aside className="w-60 min-h-screen bg-gray-900 border-r border-gray-800 flex flex-col">
      {/* Logo / brand */}
      <div className="px-5 py-5 border-b border-gray-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white font-bold text-sm">
            PL
          </div>
          <div>
            <p className="text-white font-semibold text-sm leading-none">PromptLab</p>
            <p className="text-gray-500 text-xs mt-0.5">v0.1.0</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {NAV_ITEMS.map(({ section, items }) => (
          <div key={section}>
            <p className="px-2 mb-1.5 text-xs font-semibold text-gray-600 uppercase tracking-wider">
              {section}
            </p>
            <ul className="space-y-0.5">
              {items.map(({ to, label, icon }) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    end={to === '/'}
                    className={({ isActive }) =>
                      `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-100 ${
                        isActive
                          ? 'bg-brand-600/20 text-brand-300 border border-brand-600/30'
                          : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                      }`
                    }
                  >
                    <span className="text-base leading-none">{icon}</span>
                    {label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      {/* Bottom status bar */}
      <div className="px-5 py-4 border-t border-gray-800">
        <BackendStatus />
      </div>
    </aside>
  )
}
