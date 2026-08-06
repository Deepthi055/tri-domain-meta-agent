import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppLayout } from '@/layouts/AppLayout'
import { AuthLayout } from '@/layouts/AuthLayout'
import { ProtectedRoute } from '@/routes/ProtectedRoute'
import { LoginPage } from '@/pages/auth/LoginPage'
import { RegisterPage } from '@/pages/auth/RegisterPage'
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { ChatPage } from '@/pages/ChatPage'
import { CareerPage } from '@/pages/CareerPage'
import { HealthPage } from '@/pages/HealthPage'
import { FinancePage } from '@/pages/FinancePage'
import { ProfilePage } from '@/pages/ProfilePage'
import { MemoryPage } from '@/pages/MemoryPage'
import { ReportsPage } from '@/pages/ReportsPage'
import { HistoryPage } from '@/pages/HistoryPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { ROUTES } from '@/utils/constants'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to={ROUTES.PROFILE} replace />,
  },
  {
    element: <AuthLayout />,
    children: [
      { path: ROUTES.LOGIN, element: <LoginPage /> },
      { path: ROUTES.REGISTER, element: <RegisterPage /> },
      { path: ROUTES.FORGOT_PASSWORD, element: <ForgotPasswordPage /> },
    ],
  },
  {
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { path: ROUTES.DASHBOARD, element: <DashboardPage /> },
      { path: ROUTES.CHAT, element: <ChatPage /> },
      { path: ROUTES.CAREER, element: <CareerPage /> },
      { path: ROUTES.HEALTH, element: <HealthPage /> },
      { path: ROUTES.FINANCE, element: <FinancePage /> },
      { path: ROUTES.PROFILE, element: <ProfilePage /> },
      { path: ROUTES.MEMORY, element: <MemoryPage /> },
      { path: ROUTES.REPORTS, element: <ReportsPage /> },
      { path: ROUTES.HISTORY, element: <HistoryPage /> },
      { path: ROUTES.SETTINGS, element: <SettingsPage /> },
    ],
  },
  {
    path: '*',
    element: <Navigate to={ROUTES.DASHBOARD} replace />,
  },
])
