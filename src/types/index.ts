export interface User {
  id: string
  name: string
  email: string
  created_at: string
}

export interface Token {
  access_token: string
  token_type: string
}

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
  current_skills?: string[]
  target_role?: string
  experience_level?: string
  career_goal?: string
  updated_at?: string
}

export interface HealthProfile {
  fitness_goal?: string
  sleep_hours?: number
  sleep_quality?: number
  diet_preference?: string
  updated_at?: string
}

export interface FinanceProfile {
  monthly_income?: number
  monthly_expenses?: number
  savings_goal?: number
  risk_appetite?: string
  investment_experience?: string
  updated_at?: string
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

export interface QueryRequest {
  name: string
  age: number
  query: string
  domain?: string
  current_skills?: string[]
  target_role?: string
  experience_level?: string
  location?: string
  weight_kg?: number
  height_cm?: number
  fitness_goal?: string
  sleep_hours?: number
  monthly_income?: number
  monthly_expenses?: number
  expenses?: Record<string, number>
  portfolio?: Record<string, number>
  risk_tolerance?: string
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
  job_matches?: unknown[]
  salary_benchmark?: Record<string, unknown>
  learning_path?: unknown[]
  bmi?: number
  fitness?: Record<string, unknown>
  workout_plan?: unknown[]
  nutrition?: Record<string, unknown>
  sleep?: Record<string, unknown>
  savings?: Record<string, unknown>
  debt_ratio?: number
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
