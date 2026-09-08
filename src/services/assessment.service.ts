import { api } from './api'
import type {
  AssessmentHistoryItem,
  CareerAssessmentResponse,
  HealthAssessmentRequest,
  HealthAssessmentResponse,
} from '@/types'

export const assessmentService = {
  async getHistory(): Promise<AssessmentHistoryItem[]> {
    const res = await api.get<AssessmentHistoryItem[]>('/assessments/history')
    return res.data
  },

  async assessCareer(): Promise<CareerAssessmentResponse> {
    const res = await api.post<CareerAssessmentResponse>('/assessments/career')
    return res.data
  },

  async assessHealth(data: HealthAssessmentRequest): Promise<HealthAssessmentResponse> {
    const res = await api.post<HealthAssessmentResponse>('/assessments/health', data)
    return res.data
  },
}