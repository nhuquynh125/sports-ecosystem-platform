import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { ForbiddenPage } from '@/pages/ForbiddenPage'
import { FullPageSpinner } from '@/components/shared/Spinner'
import { Button } from '@/components/ui/button'
import type { Role } from '@/config/roles'
import { useAuth } from '@/hooks/use-auth'

/**
 * Route guard. Not signed in -> /login (remembering where the user wanted to go).
 * Signed in without one of `roles` -> a 403 page (not a redirect, so the URL stays honest).
 *
 *   <Route element={<ProtectedRoute />}>                       // any signed-in user
 *   <Route element={<ProtectedRoute roles={['admin']} />}>     // admins only
 */
export function ProtectedRoute({ roles }: { roles?: Role[] }) {
  const { status, hasRole, refetchUser, logout } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <FullPageSpinner label="Loading your account" />

  if (status === 'unauthenticated') {
    return <Navigate to="/login" replace state={{ from: `${location.pathname}${location.search}` }} />
  }

  if (status === 'error') {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-6 text-center">
        <h1 className="text-3xl font-semibold uppercase">Can't load your account</h1>
        <p className="max-w-sm text-sm text-muted-foreground">The server could not be reached. Check your connection and try again.</p>
        <div className="flex gap-2">
          <Button onClick={refetchUser}>Try again</Button>
          <Button variant="outline" onClick={() => logout({ silent: true })}>
            Sign out
          </Button>
        </div>
      </div>
    )
  }

  if (roles && roles.length > 0 && !hasRole(...roles)) return <ForbiddenPage />

  return <Outlet />
}
