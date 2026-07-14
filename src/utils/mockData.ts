import type { ConversationSummary, Memory, Report } from '@/types'

export const mockDomainScores = {
  career: 78,
  health: 85,
  finance: 72,
  overall: 78,
}

export const mockCareerData = {
  skills: [
    { name: 'Python', level: 85, category: 'Technical' },
    { name: 'Machine Learning', level: 72, category: 'Technical' },
    { name: 'SQL', level: 90, category: 'Technical' },
    { name: 'Communication', level: 78, category: 'Soft' },
    { name: 'Leadership', level: 65, category: 'Soft' },
    { name: 'Data Visualization', level: 80, category: 'Technical' },
  ],
  roadmap: [
    { phase: 'Foundation', duration: '3 months', tasks: ['Master Python fundamentals', 'Learn SQL & databases', 'Statistics basics'] },
    { phase: 'Intermediate', duration: '4 months', tasks: ['Machine Learning algorithms', 'Deep Learning intro', 'Build portfolio projects'] },
    { phase: 'Advanced', duration: '5 months', tasks: ['MLOps & deployment', 'System design', 'Interview preparation'] },
  ],
  salaryPrediction: { current: 850000, predicted: 1200000, timeframe: '18 months' },
  certifications: ['AWS ML Specialty', 'Google Data Analytics', 'TensorFlow Developer'],
  jobRecommendations: [
    { title: 'Data Scientist', company: 'Tech Corp', match: 92 },
    { title: 'ML Engineer', company: 'AI Startup', match: 87 },
    { title: 'Analytics Lead', company: 'FinTech Inc', match: 81 },
  ],
  progressData: [
    { month: 'Jan', skills: 45, projects: 2 },
    { month: 'Feb', skills: 52, projects: 3 },
    { month: 'Mar', skills: 58, projects: 3 },
    { month: 'Apr', skills: 65, projects: 4 },
    { month: 'May', skills: 72, projects: 5 },
    { month: 'Jun', skills: 78, projects: 6 },
  ],
}

export const mockHealthData = {
  bmi: 23.4,
  sleep: { hours: 7.2, quality: 8, trend: 'improving' },
  stress: { level: 4, trend: 'stable' },
  calories: { consumed: 1850, target: 2200, burned: 450 },
  water: { glasses: 6, target: 8 },
  weeklyActivity: [
    { day: 'Mon', steps: 8200, workout: 45 },
    { day: 'Tue', steps: 6500, workout: 0 },
    { day: 'Wed', steps: 9100, workout: 60 },
    { day: 'Thu', steps: 7800, workout: 30 },
    { day: 'Fri', steps: 10200, workout: 45 },
    { day: 'Sat', steps: 5500, workout: 90 },
    { day: 'Sun', steps: 4200, workout: 0 },
  ],
  dietSuggestions: ['Increase protein intake to 1.2g/kg', 'Add more leafy greens', 'Reduce processed sugar'],
  workoutSuggestions: ['30 min cardio 3x/week', 'Strength training 2x/week', 'Yoga for flexibility'],
}

export const mockFinanceData = {
  monthlyIncome: 85000,
  monthlyExpenses: 52000,
  savings: 33000,
  savingsRate: 38.8,
  budgetBreakdown: [
    { name: 'Housing', value: 18000, color: '#10b981' },
    { name: 'Food', value: 8000, color: '#14b8a6' },
    { name: 'Transport', value: 5000, color: '#06b6d4' },
    { name: 'Utilities', value: 4000, color: '#8b5cf6' },
    { name: 'Entertainment', value: 6000, color: '#f59e0b' },
    { name: 'Savings', value: 11000, color: '#22c55e' },
    { name: 'Other', value: 5000, color: '#64748b' },
  ],
  monthlyTrend: [
    { month: 'Jan', income: 80000, expenses: 48000, savings: 32000 },
    { month: 'Feb', income: 82000, expenses: 50000, savings: 32000 },
    { month: 'Mar', income: 85000, expenses: 51000, savings: 34000 },
    { month: 'Apr', income: 85000, expenses: 49000, savings: 36000 },
    { month: 'May', income: 85000, expenses: 53000, savings: 32000 },
    { month: 'Jun', income: 85000, expenses: 52000, savings: 33000 },
  ],
  riskProfile: 'Moderate',
  portfolio: [
    { asset: 'Equity Funds', allocation: 45, value: 450000 },
    { asset: 'Debt Funds', allocation: 25, value: 250000 },
    { asset: 'Gold ETF', allocation: 10, value: 100000 },
    { asset: 'Fixed Deposits', allocation: 15, value: 150000 },
    { asset: 'Crypto', allocation: 5, value: 50000 },
  ],
  investments: ['Index Funds (Nifty 50)', 'PPF for tax savings', 'ELSS mutual funds', 'Emergency fund in liquid funds'],
}

export const mockActivities = [
  { id: '1', type: 'chat', title: 'Career advice session', domain: 'career', timestamp: new Date(Date.now() - 3600000).toISOString() },
  { id: '2', type: 'report', title: 'Health Advisory Report generated', domain: 'health', timestamp: new Date(Date.now() - 86400000).toISOString() },
  { id: '3', type: 'memory', title: 'New memory saved: fitness goal', domain: 'health', timestamp: new Date(Date.now() - 172800000).toISOString() },
  { id: '4', type: 'chat', title: 'Budget planning discussion', domain: 'finance', timestamp: new Date(Date.now() - 259200000).toISOString() },
  { id: '5', type: 'profile', title: 'Profile updated', domain: 'auto', timestamp: new Date(Date.now() - 432000000).toISOString() },
]

export const mockConversations: ConversationSummary[] = [
  { id: 'mock-1', domain: 'career', created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: 'mock-2', domain: 'health', created_at: new Date(Date.now() - 86400000).toISOString() },
  { id: 'mock-3', domain: 'finance', created_at: new Date(Date.now() - 172800000).toISOString() },
]

export const mockMemories: Memory[] = [
  { id: 'm1', memory_text: 'User wants to transition to data science role within 12 months', category: 'career', importance_score: 0.9, created_at: new Date(Date.now() - 86400000).toISOString() },
  { id: 'm2', memory_text: 'Prefers morning workouts, 3 days per week', category: 'health', importance_score: 0.7, created_at: new Date(Date.now() - 172800000).toISOString() },
  { id: 'm3', memory_text: 'Monthly savings goal is ₹15,000', category: 'finance', importance_score: 0.8, created_at: new Date(Date.now() - 259200000).toISOString() },
]

export const mockReports: Report[] = [
  { id: 'r1', report_name: 'Career Advisory Report', file_path: './reports/career_report.pdf', generated_at: new Date(Date.now() - 86400000).toISOString() },
  { id: 'r2', report_name: 'Health Advisory Report', file_path: './reports/health_report.pdf', generated_at: new Date(Date.now() - 604800000).toISOString() },
]
