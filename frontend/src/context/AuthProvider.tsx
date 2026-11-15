import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { authApi } from '@/api/auth'
import { TOKEN_KEY, setUnauthorizedHandler, tokenStorage } from '@/api/client'
import { usersApi } from '@/api/users'
import type { Role } from '@/config/roles'
import { AuthContext, meQueryKey, type AuthContextValue, type AuthStatus } from '@/context/auth-context'
import { toast } from '@/lib/toast'

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [token, setToken] = useState<string | null>(() => tokenStorage.get())

  // Roles and `is_active` live in the DB, so /users/me is the source of truth (re-checked on focus).
  const meQuery = useQuery({
    queryKey: meQueryKey,
    queryFn: usersApi.me,
    enabled: token !== null,
    staleTime: 60_000,
    retry: false,
    meta: { silent: true },
  })

  const logout = useCallback(
    (options?: { silent?: boolean }) => {
      tokenStorage.clear()
      setToken(null)
      queryClient.clear()
      if (!options?.silent) toast.info('Signed out')
    },
    [queryClient],
  )

  const login = useCallback(
    async (email: string, password: string) => {
      tokenStorage.clear() // never let a stale token interfere with signing in
      const result = await authApi.login({ email, password })
      tokenStorage.set(result.access_token)
      queryClient.setQueryData(meQueryKey, result.user)
      setToken(result.access_token)
      return result.user
    },
    [queryClient],
  )

  // 401 (expired / invalid token) or "Account is disabled" from any request ends the session.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      if (!tokenStorage.get()) return
      logout({ silent: true })
      toast.info('Your session has ended', 'Please sign in again.')
    })
    return () => setUnauthorizedHandler(null)
  }, [logout])

  // Keep several tabs in sync (sign in / out in one tab affects the others).
  useEffect(() => {
    function onStorage(event: StorageEvent) {
      if (event.key !== TOKEN_KEY && event.key !== null) return
      const next = tokenStorage.get()
      setToken(next)
      if (!next) queryClient.clear()
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [queryClient])

  const user = token !== null ? (meQuery.data ?? null) : null

  let status: AuthStatus
  if (token === null) status = 'unauthenticated'
  else if (user) status = 'authenticated'
  else if (meQuery.isError) status = 'error'
  else status = 'loading'

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      status,
      login,
      logout,
      hasRole: (...roles: Role[]) => !!user && roles.some((role) => user.roles.includes(role)),
      refetchUser: () => void meQuery.refetch(),
    }),
    // meQuery.refetch is stable; `status` and `user` carry every change that matters.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [user, status, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
