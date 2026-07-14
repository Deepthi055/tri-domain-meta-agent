import { api } from './api'
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
    const res = await api.get(`/reports/${id}`, { responseType: 'blob' })
    return res.data
  },

  getDownloadUrl(id: string): string {
    const token = localStorage.getItem('tridomain_access_token')
    return `/reports/${id}?token=${token}`
  },
}
