import { api } from './api'
import type { RegisterRequest, Token, User } from '@/types'
import { STORAGE_KEYS } from '@/utils/constants'

export const authService = {
  async register(data: RegisterRequest): Promise<User> {
    const res = await api.post<User>('/auth/register', data)
    return res.data
  },

  async login(email: string, password: string): Promise<Token> {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)
    const res = await api.post<Token>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return res.data
  },

  async forgotPassword(email: string): Promise<{ message: string }> {
    const res = await api.post<{ message: string }>('/auth/forgot-password', { email })
    return res.data
  },

  async changePassword(current_password: string, new_password: string): Promise<{ message: string }> {
    const res = await api.post<{ message: string }>('/auth/change-password', {
      current_password,
      new_password,
    })
    return res.data
  },

  async me(): Promise<User> {
    const res = await api.get<User>('/auth/me')
    return res.data
  },

  async uploadAvatar(avatarUrl: string): Promise<User> {
    const res = await api.post<User>('/auth/avatar', { avatar_url: avatarUrl })
    return res.data
  },

  async updateCurrentUser(name: string): Promise<User> {
    const res = await api.put<User>('/auth/me', { name })
    return res.data
  },

  async setTwoFactorEnabled(enabled: boolean, current_password?: string): Promise<User> {
    const res = await api.post<User>('/auth/two-factor', {
      enabled,
      current_password,
    })
    return res.data
  },

  saveToken(token: Token): void {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, token.access_token)
  },

  saveUser(user: User): void {
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user))
  },

  getStoredUser(): User | null {
    const raw = localStorage.getItem(STORAGE_KEYS.USER)
    if (!raw) return null
    try {
      return JSON.parse(raw) as User
    } catch {
      return null
    }
  },

  clearStorage(): void {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
    localStorage.removeItem(STORAGE_KEYS.USER)
  },

  logout(): void {
    this.clearStorage()
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
  },
}
