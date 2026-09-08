import { api } from './api'
import { API_BASE_URL } from '@/utils/constants'
import type { Report, ReportCreate } from '@/types'

export const reportService = {
  async getAll(): Promise<Report[]> {
    const res = await api.get<Report[]>('/reports')
    return res.data
  },

  async create(data: ReportCreate): Promise<Report> {
    const res = await api.post<Report>('/reports', data)
    return res.data
  },

  async download(id: string): Promise<Blob> {
    const token = localStorage.getItem('tridomain_access_token')

    if (!token) {
      throw new Error('Authentication token not found')
    }

    const res = await api.get(`/reports/${id}?token=${encodeURIComponent(token)}`, {
      responseType: 'blob',
    })

    return res.data
  },

  getDownloadUrl(id: string): string {
    const token = localStorage.getItem('tridomain_access_token')

    if (!token) {
      throw new Error('Authentication token not found')
    }

    return `${API_BASE_URL}/reports/${id}?token=${encodeURIComponent(token)}`
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/reports/${id}`)
  },
}