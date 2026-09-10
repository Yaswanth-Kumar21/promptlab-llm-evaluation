/**
 * PromptLab API client
 *
 * Centralised Axios instance — all requests automatically get:
 *  - Correct base URL (env or Vite proxy)
 *  - JSON Content-Type
 *  - 30-second timeout (LLM calls can be slow)
 *  - Normalised error objects
 */

import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,   // 60 s for slow models
  headers: { 'Content-Type': 'application/json' },
})

// ── Response interceptor — normalise errors ───────────────────────────────
api.interceptors.response.use(
  (res) => res,
  (error) => {
    const out = { message: 'An unexpected error occurred.', status: null, detail: null }

    if (error.response) {
      out.status = error.response.status
      const data = error.response.data
      if (typeof data === 'string') {
        out.message = data
      } else if (data?.detail) {
        out.message = Array.isArray(data.detail)
          ? data.detail.map((e) => e.msg).join(', ')
          : String(data.detail)
        out.detail = data.detail
      } else if (data?.message) {
        out.message = data.message
      }
      if (out.status === 500) out.message = 'The server encountered an error. Please try again.'
    } else if (error.request) {
      out.message = 'Could not reach the server. Is the backend running on port 8000?'
    } else if (error.code === 'ECONNABORTED') {
      out.message = 'Request timed out. The model may be busy — try again.'
    }

    return Promise.reject(out)
  },
)

export default api

// ── Typed helper functions ────────────────────────────────────────────────

// System
export const fetchHealth    = () => api.get('/health').then(r => r.data)
export const fetchProviders = () => api.get('/providers').then(r => r.data)

// Playground
export const runPrompt = (body) =>
  api.post('/prompts/run', body).then(r => r.data)

export const runTechnique = (body) =>
  api.post('/prompts/run/technique', body).then(r => r.data)

// Prompt Library
export const fetchPrompts = (params) =>
  api.get('/prompts', { params }).then(r => r.data)

export const createPrompt = (body) =>
  api.post('/prompts', body).then(r => r.data)

export const fetchPrompt = (id) =>
  api.get(`/prompts/${id}`).then(r => r.data)

export const updatePrompt = (id, body) =>
  api.put(`/prompts/${id}`, body).then(r => r.data)

export const deletePrompt = (id) =>
  api.delete(`/prompts/${id}`)

// Versions
export const fetchVersions = (promptId) =>
  api.get(`/prompts/${promptId}/versions`).then(r => r.data)

export const createVersion = (promptId, body) =>
  api.post(`/prompts/${promptId}/versions`, body).then(r => r.data)

export const markBestVersion = (promptId, versionId) =>
  api.put(`/prompts/${promptId}/versions/${versionId}/best`).then(r => r.data)

export const duplicateVersion = (promptId, versionId) =>
  api.post(`/prompts/${promptId}/versions/${versionId}/duplicate`).then(r => r.data)

// Experiments
export const fetchExperiments = (params) =>
  api.get('/experiments', { params }).then(r => r.data)

export const fetchExperiment  = (id) =>
  api.get(`/experiments/${id}`).then(r => r.data)

export const fetchStats = () =>
  api.get('/experiments/stats').then(r => r.data)
