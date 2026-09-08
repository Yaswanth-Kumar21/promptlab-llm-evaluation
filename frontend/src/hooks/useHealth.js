/**
 * useHealth — polls the backend health endpoint.
 *
 * Returns: { health, loading, error, refetch }
 *
 * Used by the sidebar status indicator and the Settings page.
 */

import { useState, useEffect, useCallback } from 'react'
import { fetchHealth } from '../services/api'

export function useHealth(pollIntervalMs = 30_000) {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]   = useState(null)

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchHealth()
      setHealth(data)
    } catch (err) {
      setError(err.message ?? 'Could not reach backend.')
      setHealth(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refetch()
    const id = setInterval(refetch, pollIntervalMs)
    return () => clearInterval(id)
  }, [refetch, pollIntervalMs])

  return { health, loading, error, refetch }
}
