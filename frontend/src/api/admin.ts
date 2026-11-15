import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { AdminUserListParams, Page, User } from '@/api/types'
import type { Role } from '@/config/roles'

export const adminKeys = {
  all: ['admin-users'] as const,
  list: (params: AdminUserListParams) => ['admin-users', 'list', params] as const,
}

export function useAdminUsers(params: AdminUserListParams) {
  return useQuery({
    queryKey: adminKeys.list(params),
    queryFn: () =>
      api
        .get<Page<User>>('/admin/users', {
          // Omit empty filters instead of sending `q=` / `role=`.
          params: {
            page: params.page,
            page_size: params.page_size,
            q: params.q || undefined,
            role: params.role || undefined,
            is_active: params.is_active,
          },
        })
        .then((r) => r.data),
    placeholderData: keepPreviousData,
  })
}

export function useSetUserStatus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, isActive }: { userId: number; isActive: boolean }) =>
      api.patch<User>(`/admin/users/${userId}/status`, { is_active: isActive }).then((r) => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: adminKeys.all }),
  })
}

export function useSetUserRoles() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, roles }: { userId: number; roles: Role[] }) =>
      api.put<User>(`/admin/users/${userId}/roles`, { roles }).then((r) => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: adminKeys.all }),
  })
}
