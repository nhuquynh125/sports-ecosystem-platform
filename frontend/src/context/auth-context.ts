import { createContext } from 'react'
import type { User } from '@/api/types'
import type { Role } from '@/config/roles'

export const meQueryKey = ['me'] as const

export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated' | 'error'

export interface AuthContextValue {
  user: User | null
  status: AuthStatus
  login: (email: string, password: string) => Promise<User>
  logout: (options?: { silent?: boolean }) => void
  hasRole: (...roles: Role[]) => boolean
  /** Re-fetch /users/me (e.g. after the roles changed). */
  refetchUser: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
