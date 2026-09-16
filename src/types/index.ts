export interface User {
  id: string
  name: string
  email: string
  created_at: string
  avatar_url?: string
  two_factor_enabled?: boolean
}

export interface Token {
  access_token: string
  token_type: string
}

export interface NotificationPreferences {
  email: boolean
  push: boolean
  reports: boolean
  insights: boolean
}

export type LanguageCode = 'en' | 'hi' | 'kn'

export interface RegisterRequest {
  name: string
  email: string
  password: string
}

export interface GeneralProfile {
  age?: number
  gender?: string
  height_cm?: number
  weight_kg?: number
  location?: string
  updated_at?: string
}

export interface CareerProfile {
  education?: string
  current_skills?: string[]
  target_role?: string
  experience_level?: string
  career_goal?: string
  preferred_roles?: string
  resume?: string
  resume_text?: string
  updated_at?: string
}

export interface HealthProfile {
  medical_conditions?: string
  lifestyle?: string
  fitness_goal?: string
  sleep_hours?: number
  sleep_quality?: number
  mood_score?: number
  stress_level?: number
  anxiety_level?: number
  active_days_per_week?: number
  diet_preference?: string
  workout?: string
  health_goals?: string
  water_intake?: number
  updated_at?: string
}

export interface MedicalReportFinding {
  item: string
  meaning: string
  severity: 'normal' | 'watch' | 'urgent' | string
}

export interface MedicalReportResponse {
  filename: string
  extracted_text: string
  analysis: {
    summary: string
    findings: MedicalReportFinding[]
    next_steps: string[]
    reassurance: string
    disclaimer: string
    analysis_available: boolean
  }
}

export interface FinanceProfile {
  monthly_income?: number
  monthly_expenses?: number
  current_savings?: number
  savings_goal?: number
  investments?: string
  portfolio?: Record<string, number>
  risk_appetite?: string
  investment_experience?: string
  financial_goals?: string
  budget?: string
  debts?: DebtEntry[]
  total_debt?: number
  monthly_debt_payment?: number
  retirement_age?: number
  retirement_savings?: number
  monthly_contribution?: number
  annual_income?: number
  tax_deductions?: Record<string, number>
  updated_at?: string
}

export interface DebtEntry {
  name: string
  balance: number
  interest_rate: number
  min_payment: number
}

export interface FullProfile {
  general?: GeneralProfile
  career?: CareerProfile
  health?: HealthProfile
  finance?: FinanceProfile
}

export interface Memory {
  id: string
  memory_text: string
  category: string
  importance_score: number
  created_at: string
}

export interface MemoryCreate {
  memory_text: string
  category: string
  importance_score?: number
}

export interface ChatRequest {
  query: string
  domain: string
  conversation_id?: string | null
}

export interface ChatResponse {
  conversation_id: string
  domain: string
  answer: string
  reason?: string | null
  confidence?: number | null
  memory_saved: string[]
  sources: string[]
  messages?: Message[]
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | string
  content: string
  timestamp: string
}

export interface Conversation {
  id: string
  domain: string
  created_at: string
  messages: Message[]
}

export interface ConversationSummary {
  id: string
  domain: string
  created_at: string
}

export interface Report {
  id: string
  report_name: string
  file_path: string
  generated_at: string
}

export interface ReportCreate {
  domain: string
  conversation_id?: string | null
}

export interface AssessmentHistoryItem {
  assessment_id: string
  domain: 'career' | 'health' | 'finance'
  assessment_type: 'target_role_skill_match' | 'fitness' | 'savings_rate'
  value: number
  value_kind: 'score' | 'percentage'
  target_role: string | null
  assessed_at: string
}

export interface CareerAssessmentResponse {
  assessment_id: string
  domain: 'career'
  assessment_type: 'target_role_skill_match'
  value: number
  value_kind: 'score'
  target_role: string | null
  assessed_at: string
  source: string
  calculation_version: string
  details: {
    matched_skills: string[]
    missing_skills: string[]
    total_required_skills: number
  }
}

export interface HealthAssessmentRequest {
  sleep_quality: number
  stress_level: number
  mood_score: number
  active_days_per_week: number
}

export interface HealthAssessmentResponse {
  assessment_id: string
  domain: 'health'
  assessment_type: 'fitness'
  value: number
  value_kind: 'score'
  target_role: null
  assessed_at: string
  source: string
  calculation_version: string
  details: Record<string, unknown>
}

export interface QueryRequest {
  name: string
  age: number
  query: string
  domain?: string
  current_skills?: string[]
  target_role?: string
  experience_level?: string
  location?: string
  years_experience?: number
  current_level?: string
  timeline_months?: number
  resume_text?: string
  weight_kg?: number
  height_cm?: number
  fitness_goal?: string
  sleep_hours?: number
  monthly_income?: number
  monthly_expenses?: number
  savings_goal?: number
  current_savings?: number
  expenses?: Record<string, number>
  portfolio?: Record<string, number>
  risk_tolerance?: string
  investment_experience?: string
  financial_goals?: string
  debts?: DebtEntry[]
  total_debt?: number
  monthly_debt_payment?: number
  retirement_age?: number
  retirement_savings?: number
  monthly_contribution?: number
  annual_income?: number
  tax_deductions?: Record<string, number>
}

export interface QueryIntent {
  domains: string[]
  confidence: number
  reasoning: string
}

export interface QueryResponse {
  status: string
  intent?: QueryIntent
  responses?: DomainAgentResponse[]
  domains_activated?: string[]
  warning?: string
  reason?: string
  message?: string
  agent_framework?: string
}

export interface DomainAgentResponse {
  domain: string
  recommendation: string
  reason: string
  confidence: number
  explainability?: Record<string, unknown>
  skill_gap?: Record<string, unknown>
  jobs?: Array<{
    title?: string
    company?: string
    location?: string
    embedding_match_score?: number
    description?: string
    apply_link?: string
    employment_type?: string
    is_remote?: boolean
  }>
  job_matches?: unknown[]
  salary_benchmark?: Record<string, unknown>
  learning_path?: unknown[]
  resume_analysis?: {
    semantic_match_score?: number
    required_skills?: string[]
    skills_not_evidenced?: string[]
    suggestions?: string[]
    structure_checks?: Record<string, boolean>
    structure_missing?: string[]
    error?: string
  }
  summary?: string
  bmi?: number
  fitness?: Record<string, unknown>
  workout_plan?: unknown[]
  nutrition?: Record<string, unknown>
  sleep?: Record<string, unknown>
  savings?: Record<string, unknown>
  debt_ratio?: number
  tools_used?: string[]
  tool_outputs?: Record<string, FinanceToolOutput>
}

export interface FinanceCategoryBreakdown {
  category: string
  amount: number
  share_pct: number
  status: string
  recommended_pct?: number
}

export interface FinanceToolOutput {
  error?: string
  recommendation?: string
  summary?: string
  calculation_steps?: string[]
  health_score?: number
  health_status?: string
  expense_ratio_pct?: number
  strengths?: unknown[]
  weaknesses?: unknown[]
  income?: number
  expenses?: number
  monthly_savings?: number
  total_expenses?: number
  disposable_income?: number
  remaining_amount?: number
  savings_rate_pct?: number
  savings_goal?: number | null
  goal_difference?: number | null
  current_savings?: number
  remaining_to_goal?: number | null
  months_to_goal?: number | null
  shortfall?: number | null
  category_breakdown?: FinanceCategoryBreakdown[]
  savings_status?: string
  overspending?: string[]
  total_debt?: number | null
  monthly_payment?: number
  recommended_strategy?: string
  interest_savings?: number
  debt_to_income_ratio?: number
  debt_status?: string
  projected_corpus?: number
  corpus_needed?: number
  gap_or_surplus?: number
  status?: string
  required_monthly_contrib?: number
  retirement_age?: number
  monthly_contribution?: number
  assumptions?: string[] | Record<string, number>
  gross_income?: number
  taxable_income?: number
  estimated_tax?: number
  recommended_regime?: string
  tax_savings_vs_other?: number
  optimisation_tips?: string[]
  old_regime?: Record<string, unknown>
  new_regime?: Record<string, unknown>
  portfolio_value?: number
  current_allocation?: Record<string, number>
  target_allocation?: Record<string, number>
  rebalancing_deltas?: Array<Record<string, string | number>>
  risk_profile?: string
  age_bracket?: string
  [key: string]: unknown
}

export interface Domain {
  name: string
  description: string
}

export interface ApiStatus {
  status: string
  system: string
}

export interface HealthCheck {
  status: string
}

export type DomainType = 'auto' | 'career' | 'health' | 'finance'

export interface ComparisonResult {
  standard: QueryResponse & { executionTime: number }
  langchain: QueryResponse & { executionTime: number }
}
