/**
 * useProviders — fetches the list of LLM providers.
 *
 * Returns: { providers, defaultProvider, loading, error, refetch }
 */

import { useState, useEffect, useCallback } from 'react'
import { fetchProviders } from '../services/api'

export function useProviders() {
  const [providers, setProviders]           = useState([])
  const [defaultProvider, setDefaultProvider] = useState('mock')
  const [loading, setLoading]               = useState(true)
  const [error, setError]                   = useState(null)

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchProviders()
      setProviders(data.providers ?? [])
      setDefaultProvider(data.default_provider ?? 'mock')
    } catch (err) {
      setError(err.message ?? 'Failed to load providers.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refetch() }, [refetch])

  return { providers, defaultProvider, loading, error, refetch }
}
