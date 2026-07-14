export const API_BASE_URL = import.meta.env.VITE_API_URL || ''

export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'tridomain_access_token',
  REFRESH_TOKEN: 'tridomain_refresh_token',
  USER: 'tridomain_user',
  THEME: 'tridomain_theme',
} as const

export const ROUTES = {
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  DASHBOARD: '/dashboard',
  CHAT: '/chat',
  CAREER: '/career',
  HEALTH: '/health',
  FINANCE: '/finance',
  PROFILE: '/profile',
  MEMORY: '/memory',
  REPORTS: '/reports',
  HISTORY: '/history',
  SETTINGS: '/settings',
} as const

export const DOMAIN_COLORS = {
  career: { bg: 'bg-blue-500/10', text: 'text-blue-500', border: 'border-blue-500/20', gradient: 'from-blue-500 to-indigo-500' },
  health: { bg: 'bg-emerald-500/10', text: 'text-emerald-500', border: 'border-emerald-500/20', gradient: 'from-emerald-500 to-teal-500' },
  finance: { bg: 'bg-amber-500/10', text: 'text-amber-500', border: 'border-amber-500/20', gradient: 'from-amber-500 to-orange-500' },
  auto: { bg: 'bg-purple-500/10', text: 'text-purple-500', border: 'border-purple-500/20', gradient: 'from-purple-500 to-pink-500' },
} as const

export const SUGGESTED_PROMPTS = [
  { domain: 'career', text: 'What skills should I learn to become a data scientist?' },
  { domain: 'career', text: 'Analyze my career path and suggest next steps' },
  { domain: 'health', text: 'Create a workout plan for my fitness goals' },
  { domain: 'health', text: 'How can I improve my sleep quality?' },
  { domain: 'finance', text: 'Help me create a monthly budget plan' },
  { domain: 'finance', text: 'What investment options suit my risk profile?' },
  { domain: 'auto', text: 'Give me a holistic life improvement plan' },
  { domain: 'auto', text: 'What should I focus on this month across all domains?' },
] as const
