import { useQuery, useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query'
import {
  authService,
  chatService,
  memoryService,
  profileService,
  queryService,
  reportService,
} from '@/services'
import type {
  ChatRequest,
  FullProfile,
  MemoryCreate,
  QueryRequest,
  RegisterRequest,
  ReportCreate,
} from '@/types'

export const queryKeys = {
  profile: ['profile'] as const,
  memories: (category?: string) => ['memories', category] as const,
  chatHistory: ['chatHistory'] as const,
  conversation: (id: string) => ['conversation', id] as const,
  reports: ['reports'] as const,
  domains: ['domains'] as const,
  apiStatus: ['apiStatus'] as const,
}

export function invalidateProfileDependentQueries(qc: QueryClient) {
  return Promise.all([
    qc.invalidateQueries({ queryKey: queryKeys.profile }),
    qc.invalidateQueries({
      predicate: (query) => {
        const [key] = query.queryKey as [string?]
        return key === 'chatHistory' || key === 'reports' || key === 'memories' || key === 'domains'
      },
    }),
  ])
}

export function useProfile() {
  return useQuery({
    queryKey: queryKeys.profile,
    queryFn: () => profileService.get(),
    retry: 1,
  })
}

export function useUpdateProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: FullProfile) => profileService.update(data),
    onSuccess: async (data) => {
      qc.setQueryData(queryKeys.profile, data)
      await invalidateProfileDependentQueries(qc)
    },
  })
}

export function useCreateProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: FullProfile) => profileService.create(data),
    onSuccess: async (data) => {
      qc.setQueryData(queryKeys.profile, data)
      await invalidateProfileDependentQueries(qc)
    },
  })
}

export function useMemories(category?: string) {
  return useQuery({
    queryKey: queryKeys.memories(category),
    queryFn: () => memoryService.getAll(category),
  })
}

export function useCreateMemory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: MemoryCreate) => memoryService.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.memories() }),
  })
}

export function useChatHistory() {
  return useQuery({
    queryKey: queryKeys.chatHistory,
    queryFn: () => chatService.getHistory(),
  })
}

export function useConversation(id: string | null) {
  return useQuery({
    queryKey: queryKeys.conversation(id || ''),
    queryFn: () => chatService.getConversation(id!),
    enabled: !!id,
  })
}

export function useSendChat() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ChatRequest) => chatService.send(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.chatHistory })
      qc.invalidateQueries({ queryKey: queryKeys.memories() })
    },
  })
}

export function useReports() {
  return useQuery({
    queryKey: queryKeys.reports,
    queryFn: () => reportService.getAll(),
  })
}

export function useCreateReport() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ReportCreate) => reportService.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.reports }),
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
