import { api } from './api'
import type { FullProfile } from '@/types'

export const profileService = {
  async get(): Promise<FullProfile> {
    const res = await api.get<FullProfile>('/profile')
    return res.data
  },

  async create(data: FullProfile): Promise<FullProfile> {
    const res = await api.post<FullProfile>('/profile/create', data)
    return res.data
  },

  async update(data: FullProfile): Promise<FullProfile> {
    const res = await api.put<FullProfile>('/profile', data)
    return res.data
  },
}
