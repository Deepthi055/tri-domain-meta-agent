import type { ConversationSummary, Memory, Report } from '@/types'

export const mockDomainScores = {
  career: 0,
  health: 0,
  finance: 0,
  overall: 0,
}

export const mockCareerData = {
  skills: [],
  roadmap: [],
  salaryPrediction: { current: 0, predicted: 0, timeframe: 'N/A' },
  certifications: [],
  jobRecommendations: [],
  progressData: [],
}

export const mockHealthData = {
  bmi: 0,
  sleep: { hours: 0, quality: 0, trend: 'pending' },
  stress: { level: 0, trend: 'pending' },
  calories: { consumed: 0, target: 0, burned: 0 },
  water: { glasses: 0, target: 0 },
  weeklyActivity: [],
  dietSuggestions: [],
  workoutSuggestions: [],
}

export const mockFinanceData = {
  monthlyIncome: 0,
  monthlyExpenses: 0,
  savings: 0,
  savingsRate: 0,
  budgetBreakdown: [],
  monthlyTrend: [],
  riskProfile: 'Pending',
  portfolio: [],
  investments: [],
}

export const mockActivities: Array<{ id: string; type: 'chat' | 'report' | 'memory' | 'profile'; title: string; domain: string; timestamp: string }> = []

export const mockConversations: ConversationSummary[] = []

export const mockMemories: Memory[] = []

export const mockReports: Report[] = []
