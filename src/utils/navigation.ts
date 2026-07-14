import {
  Activity,
  BarChart3,
  Brain,
  Briefcase,
  Clock,
  Heart,
  History,
  LayoutDashboard,
  LogOut,
  MessageSquare,
  Settings,
  User,
  Wallet,
  FileText,
} from 'lucide-react'
import { ROUTES } from '@/utils/constants'

export interface NavItem {
  title: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string
}

export const mainNavItems: NavItem[] = [
  { title: 'Dashboard', href: ROUTES.DASHBOARD, icon: LayoutDashboard },
  { title: 'Ask AI', href: ROUTES.CHAT, icon: MessageSquare, badge: 'AI' },
  { title: 'Career', href: ROUTES.CAREER, icon: Briefcase },
  { title: 'Health', href: ROUTES.HEALTH, icon: Heart },
  { title: 'Finance', href: ROUTES.FINANCE, icon: Wallet },
]

export const secondaryNavItems: NavItem[] = [
  { title: 'Profile', href: ROUTES.PROFILE, icon: User },
  { title: 'Memory', href: ROUTES.MEMORY, icon: Brain },
  { title: 'Reports', href: ROUTES.REPORTS, icon: FileText },
  { title: 'History', href: ROUTES.HISTORY, icon: History },
  { title: 'Settings', href: ROUTES.SETTINGS, icon: Settings },
]

export const breadcrumbLabels: Record<string, string> = {
  dashboard: 'Dashboard',
  chat: 'Ask AI',
  career: 'Career',
  health: 'Health',
  finance: 'Finance',
  profile: 'Profile',
  memory: 'Memory',
  reports: 'Reports',
  history: 'History',
  settings: 'Settings',
  login: 'Login',
  register: 'Register',
}

export const domainIcons = {
  career: Briefcase,
  health: Heart,
  finance: Wallet,
  auto: Brain,
}

export const activityIcons = {
  chat: MessageSquare,
  report: FileText,
  memory: Brain,
  profile: User,
  default: Activity,
}
