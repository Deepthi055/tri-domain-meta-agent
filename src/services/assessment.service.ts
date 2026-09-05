import { api } from './api'
import type { AssessmentHistoryItem } from '@/types'

export const assessmentService = {
  async getHistory(): Promise<AssessmentHistoryItem[]> {
    const res = await api.get<AssessmentHistoryItem[]>('/assessments/history')
    return res.data
  },
}