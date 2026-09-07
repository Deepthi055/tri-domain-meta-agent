import { useQuery, useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { API_BASE_URL } from '@/utils/constants'
import {
  authService,
  assessmentService,
  chatService,
  memoryService,
  profileService,
  queryService,
  reportService,
} from '@/services'
import type {
  ChatRequest,
  FullProfile,
  HealthAssessmentRequest,
  MemoryCreate,
  QueryRequest,
  RegisterRequest,
  ReportCreate,
} from '@/types'

export const queryKeys = {
  profile: (userId: string) => ['profile', userId] as const,
  memories: (userId: string, category?: string) => ['memories', userId, category] as const,
  chatHistory: (userId: string) => ['chatHistory', userId] as const,
  conversation: (userId: string, id: string) => ['conversation', userId, id] as const,
  reports: (userId: string) => ['reports', userId] as const,
  assessmentHistory: (userId: string) => ['assessmentHistory', userId] as const,
  domains: ['domains'] as const,
  apiStatus: ['apiStatus'] as const,
}

export function invalidateProfileDependentQueries(qc: QueryClient, userId: string) {
  return Promise.all([
    qc.invalidateQueries({ queryKey: queryKeys.profile(userId) }),
    qc.invalidateQueries({
      predicate: (query) => {
        const [key, id] = query.queryKey as [string?, string?]
        if (id !== userId) return false
        return key === 'chatHistory' || key === 'reports' || key === 'memories' || key === 'domains'
      },
    }),
  ])
}

export function useProfile() {
  const { user } = useAuth()
  return useQuery({
    queryKey: queryKeys.profile(user?.id ?? ''),
    queryFn: () => profileService.get(),
    enabled: !!user?.id,
    retry: 1,
  })
}

export function useUpdateProfile() {
  const qc = useQueryClient()
  const { user } = useAuth()
  return useMutation({
    mutationFn: (data: FullProfile) => profileService.update(data),
    onSuccess: async (data) => {
      if (!user?.id) return
      qc.setQueryData(queryKeys.profile(user.id), data)
      await invalidateProfileDependentQueries(qc, user.id)
    },
  })
}

export function useCreateProfile() {
  const qc = useQueryClient()
  const { user } = useAuth()
  return useMutation({
    mutationFn: (data: FullProfile) => profileService.create(data),
    onSuccess: async (data) => {
      if (!user?.id) return
      qc.setQueryData(queryKeys.profile(user.id), data)
      await invalidateProfileDependentQueries(qc, user.id)
    },
  })
}

export function useMemories(category?: string) {
  const { user } = useAuth()
  return useQuery({
    queryKey: queryKeys.memories(user?.id ?? '', category),
    queryFn: () => memoryService.getAll(category),
    enabled: !!user?.id,
  })
}

export function useCreateMemory() {
  const qc = useQueryClient()
  const { user } = useAuth()
  return useMutation({
    mutationFn: (data: MemoryCreate) => memoryService.create(data),
    onSuccess: () => {
      if (!user?.id) return
      qc.invalidateQueries({ queryKey: queryKeys.memories(user.id) })
    },
  })
}

export function useChatHistory() {
  const qc = useQueryClient()
  const { user } = useAuth()
  const userId = user?.id ?? ''
  const query = useQuery({
    queryKey: queryKeys.chatHistory(userId),
    queryFn: () => chatService.getHistory(),
    enabled: !!user?.id,
  })

  useEffect(() => {
    if (!user?.id) return

    const base = API_BASE_URL || window.location.origin
    const wsBase = base.replace(/^http/, 'ws')
    const wsUrl = `${wsBase}/chat/ws`
    let ws: WebSocket
    try {
      ws = new WebSocket(wsUrl)
    } catch {
      return
    }

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.type === 'conversation_created') {
          qc.setQueryData(queryKeys.chatHistory(user.id), (old: any[] | undefined) => {
            const existing = old ?? []
            const filtered = existing.filter((c) => c.id !== msg.payload.id)
            return [msg.payload, ...filtered].slice(0, 10)
          })
        }
      } catch {
        // ignore
      }
    }

    return () => {
      try {
        ws.close()
      } catch {}
    }
  }, [qc, user?.id])

  return query
}

export function useConversation(id: string | null) {
  const { user } = useAuth()
  return useQuery({
    queryKey: queryKeys.conversation(user?.id ?? '', id || ''),
    queryFn: () => chatService.getConversation(id!),
    enabled: !!user?.id && !!id,
  })
}

export function useSendChat() {
  const qc = useQueryClient()
  const { user } = useAuth()
  return useMutation({
    mutationFn: (data: ChatRequest) => chatService.send(data),
    onSuccess: (_data, variables) => {
      if (!user?.id) return
      qc.invalidateQueries({ queryKey: queryKeys.chatHistory(user.id) })
      qc.invalidateQueries({ queryKey: queryKeys.memories(user.id) })
      if (variables.conversation_id) {
        qc.invalidateQueries({
          queryKey: queryKeys.conversation(user.id, variables.conversation_id),
        })
      }
    },
  })
}

export function useReports() {
  const { user } = useAuth()
  return useQuery({
    queryKey: queryKeys.reports(user?.id ?? ''),
    queryFn: () => reportService.getAll(),
    enabled: !!user?.id,
  })
}

export function useAssessmentHistory() {
  const { user } = useAuth()
  return useQuery({
    queryKey: queryKeys.assessmentHistory(user?.id ?? ''),
    queryFn: () => assessmentService.getHistory(),
    enabled: !!user?.id,
  })
}

export function useCareerAssessment() {
  return useMutation({
    mutationFn: () => assessmentService.assessCareer(),
  })
}

export function useHealthAssessment() {
  return useMutation({
    mutationFn: (data: HealthAssessmentRequest) => assessmentService.assessHealth(data),
  })
}

export function useCreateReport() {
  const qc = useQueryClient()
  const { user } = useAuth()
  return useMutation({
    mutationFn: (data: ReportCreate) => reportService.create(data),
    onSuccess: () => {
      if (!user?.id) return
      qc.invalidateQueries({ queryKey: queryKeys.reports(user.id) })
    },
  })
}

export function useDomains() {
  return useQuery({
    queryKey: queryKeys.domains,
    queryFn: () => queryService.getDomains(),
    staleTime: 5 * 60 * 1000,
  })
}

export function useApiStatus() {
  return useQuery({
    queryKey: queryKeys.apiStatus,
    queryFn: () => queryService.getApiStatus(),
    refetchInterval: 60000,
  })
}

export function useQueryMutation() {
  return useMutation({
    mutationFn: (data: QueryRequest) => queryService.query(data),
  })
}

export function useLangchainQuery() {
  return useMutation({
    mutationFn: (data: QueryRequest) => queryService.queryLangchain(data),
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: (data: RegisterRequest) => authService.register(data),
  })
}

export function useLogin() {
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authService.login(email, password),
  })
}
