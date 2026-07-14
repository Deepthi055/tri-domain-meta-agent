import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import type { User } from '@/types'
import { authService } from '@/services'
import { STORAGE_KEYS } from '@/utils/constants'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => void
  setUser: (user: User | null) => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const stored = authService.getStoredUser()
    if (stored && authService.isAuthenticated()) {
      setUser(stored)
    }
    setIsLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    const token = await authService.login(email, password)
    authService.saveToken(token)
    const stored = authService.getStoredUser()
    if (!stored) {
      const newUser: User = {
        id: 'temp',
        name: email.split('@')[0],
        email,
        created_at: new Date().toISOString(),
      }
      authService.saveUser(newUser)
      setUser(newUser)
    } else {
      setUser(stored)
    }
  }

  const register = async (name: string, email: string, password: string) => {
    const newUser = await authService.register({ name, email, password })
    authService.saveUser(newUser)
    const token = await authService.login(email, password)
    authService.saveToken(token)
    setUser(newUser)
  }

  const logout = () => {
    authService.logout()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user && authService.isAuthenticated(),
        isLoading,
        login,
        register,
        logout,
        setUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
