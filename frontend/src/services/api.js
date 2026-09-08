/**
 * PromptLab API client
 *
 * Centralised Axios instance so every request automatically:
 *  - Targets the correct base URL (from env or proxy)
 *  - Sends JSON Content-Type
 *  - Has a reasonable timeout
 *  - Has consistent error handling
 *
 * Usage:
 *   import api from '@/services/api'
 *   const data = await api.get('/providers')
 */

import axios from 'axios'

// In development Vite proxies /api → http://localhost:8000/api
// In production set VITE_API_URL in your environment
const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,   // 30 s — LLM calls can be slow
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── Request interceptor ────────────────────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    // Nothing sensitive (keys, tokens) should be injected here.
    // Authentication will be added in a later phase.
    return config
  },
  (error) => Promise.reject(error),
)

// ── Response interceptor ──────────────────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Normalise error shape so every component sees the same structure
    const normalised = {
      message: 'An unexpected error occurred.',
      status: null,
      detail: null,
    }

    if (error.response) {
      normalised.status = error.response.status
      const data = error.response.data

      if (typeof data === 'string') {
        normalised.message = data
      } else if (data?.detail) {
        // FastAPI validation errors return { detail: [...] } or { detail: "string" }
        normalised.message = Array.isArray(data.detail)
          ? data.detail.map((e) => e.msg).join(', ')
          : data.detail
        normalised.detail = data.detail
      } else if (data?.message) {
        normalised.message = data.message
      }

      // Don't expose 500 details to the UI — just show a friendly message
      if (normalised.status === 500) {
        normalised.message =
          'The server encountered an error. Please try again.'
      }
    } else if (error.request) {
      normalised.message =
        'Could not reach the server. Is the backend running?'
    } else if (error.code === 'ECONNABORTED') {
      normalised.message = 'Request timed out. The model may be busy.'
    }

    return Promise.reject(normalised)
  },
)

export default api

// ── Typed helper functions ─────────────────────────────────────────────────

/** GET /api/health */
export const fetchHealth = () => api.get('/health').then((r) => r.data)

/** GET /api/providers */
export const fetchProviders = () => api.get('/providers').then((r) => r.data)

/** GET /api/prompts */
export const fetchPrompts = () => api.get('/prompts').then((r) => r.data)

/** GET /api/experiments */
export const fetchExperiments = () =>
  api.get('/experiments').then((r) => r.data)
