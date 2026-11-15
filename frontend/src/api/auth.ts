import { api } from '@/api/client'
import type { LoginPayload, RegisterPayload, TokenResponse, User } from '@/api/types'

export const authApi = {
  login: (payload: LoginPayload) =>
    api.post<TokenResponse>('/auth/login', payload, { skipAuth: true }).then((r) => r.data),
  register: (payload: RegisterPayload) =>
    api.post<User>('/auth/register', payload, { skipAuth: true }).then((r) => r.data),
}
