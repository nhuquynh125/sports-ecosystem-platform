import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query'
import { getErrorMessage, isApiError } from '@/api/client'
import { toast } from '@/lib/toast'

declare module '@tanstack/react-query' {
  interface Register {
    queryMeta: { silent?: boolean }
    mutationMeta: { silent?: boolean }
  }
}

/** 401 is handled globally (session ended), so it never needs its own toast. */
function isSessionError(error: unknown) {
  return isApiError(error) && error.status === 401
}

export const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error, query) => {
      // Initial load failures are rendered inline by the page; toast only background refetch failures.
      if (query.meta?.silent || query.state.data === undefined || isSessionError(error)) return
      toast.error('Could not refresh data', getErrorMessage(error))
    },
  }),
  mutationCache: new MutationCache({
    onError: (error, _variables, _context, mutation) => {
      if (mutation.meta?.silent || isSessionError(error)) return
      toast.error('Request failed', getErrorMessage(error))
    },
  }),
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: true,
      retry: (failureCount, error) => {
        if (isApiError(error) && error.status >= 400 && error.status < 500) return false
        return failureCount < 2
      },
    },
  },
})
