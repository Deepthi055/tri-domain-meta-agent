import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

/** Clear all cached queries so the next user never sees the previous user's data. */
export function clearUserQueryCache(): void {
  queryClient.clear()
}
