import { api } from './api'
import type { ApiStatus, Domain, HealthCheck, QueryRequest, QueryResponse } from '@/types'

export const queryService = {
  async query(data: QueryRequest): Promise<QueryResponse> {
    const res = await api.post<QueryResponse>('/query', data)
    return res.data
  },

  async queryLangchain(data: QueryRequest): Promise<QueryResponse> {
    const res = await api.post<QueryResponse>('/query-langchain', data)
    return res.data
  },

  async getDomains(): Promise<{ domains: Domain[] }> {
    const res = await api.get<{ domains: Domain[] }>('/domains')
    return res.data
  },

  async getApiStatus(): Promise<ApiStatus> {
    const res = await api.get<ApiStatus>('/api-status')
    return res.data
  },

  async healthCheck(): Promise<HealthCheck> {
    const res = await api.get<HealthCheck>('/health-check')
    return res.data
  },
}
