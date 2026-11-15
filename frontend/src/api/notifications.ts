import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { AppNotification, Page } from '@/api/types'

export const notificationKeys = {
  all: ['notifications'] as const,
  unread: ['notifications', 'unread-count'] as const,
  list: ['notifications', 'list'] as const,
}

/** Polled so the bell badge stays live without a WebSocket (push is not built yet). */
export function useUnreadCount(enabled: boolean) {
  return useQuery({
    queryKey: notificationKeys.unread,
    queryFn: () => api.get<{ unread: number }>('/notifications/unread-count').then((r) => r.data.unread),
    enabled,
    refetchInterval: 30_000,
    meta: { silent: true },
  })
}

export function useNotifications(enabled: boolean) {
  return useQuery({
    queryKey: notificationKeys.list,
    queryFn: () =>
      api
        .get<Page<AppNotification>>('/notifications', { params: { page: 1, page_size: 10 } })
        .then((r) => r.data),
    enabled,
    staleTime: 0,
  })
}

export function useMarkRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.patch<AppNotification>(`/notifications/${id}/read`).then((r) => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: notificationKeys.all }),
  })
}

export function useMarkAllRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => api.patch<{ updated: number }>('/notifications/read-all').then((r) => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: notificationKeys.all }),
  })
}
