import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { Sport } from '@/api/types'

export function useSports() {
  return useQuery({
    queryKey: ['sports'],
    queryFn: () => api.get<Sport[]>('/sports').then((r) => r.data),
    staleTime: 5 * 60_000,
  })
}
