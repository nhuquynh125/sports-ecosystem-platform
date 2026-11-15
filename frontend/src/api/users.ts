import { api } from '@/api/client'
import type { PasswordChangePayload, User, UserUpdatePayload } from '@/api/types'

export const usersApi = {
  me: () => api.get<User>('/users/me').then((r) => r.data),
  updateMe: (payload: UserUpdatePayload) => api.patch<User>('/users/me', payload).then((r) => r.data),
  changePassword: (payload: PasswordChangePayload) =>
    api.post<void>('/users/me/password', payload).then(() => undefined),
  deleteMe: () => api.delete<void>('/users/me').then(() => undefined),
}
