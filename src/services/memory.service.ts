import { api } from './api'
import type { Memory, MemoryCreate } from '@/types'

export const memoryService = {
  async getAll(category?: string): Promise<Memory[]> {
    const res = await api.get<Memory[]>('/memory', {
      params: category ? { category } : undefined,
    })
    return res.data
  },

  async create(data: MemoryCreate): Promise<Memory> {
    const res = await api.post<Memory>('/memory', data)
    return res.data
  },
}
