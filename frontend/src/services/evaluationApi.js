/**
 * Evaluation API helpers — Phase 7/8
 */
import api from './api'

export const runEvaluation   = (body) => api.post('/evaluations/run', body).then(r => r.data)
export const runDatasetEval  = (body) => api.post('/evaluations/dataset', body).then(r => r.data)
export const fetchDatasets   = ()     => api.get('/evaluations/datasets').then(r => r.data)
export const fetchEvaluations= (p)    => api.get('/evaluations', { params: p }).then(r => r.data)
export const runSafetyTest   = (body) => api.post('/evaluations/safety', body).then(r => r.data)
export const runBiasTest     = (body) => api.post('/evaluations/bias', body).then(r => r.data)
