import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import type { User } from '@/types'
import { authService } from '@/services'
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
    const initialize = async () => {
      const stored = authService.getStoredUser()
      if (authService.isAuthenticated()) {
        try {
          const fetched = await authService.me()
          authService.saveUser(fetched)
          setUser(fetched)
        } catch {
          authService.clearStorage()
          setUser(null)
        }
      } else if (stored) {
        setUser(stored)
      }
      setIsLoading(false)
    }

    initialize()
  }, [])

  const login = async (email: string, password: string) => {
    const token = await authService.login(email, password)
    authService.saveToken(token)
    const fetched = await authService.me()
    authService.saveUser(fetched)
    setUser(fetched)
  }

  const register = async (name: string, email: string, password: string) => {
    await authService.register({ name, email, password })
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
