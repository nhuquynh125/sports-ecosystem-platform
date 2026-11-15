import { Navigate, Outlet } from 'react-router-dom'
import { FullPageSpinner } from '@/components/shared/Spinner'
import { useAuth } from '@/hooks/use-auth'

/** Login / register: signed-in users are sent to the dashboard instead. */
export function GuestRoute() {
  const { status } = useAuth()
  if (status === 'loading') return <FullPageSpinner />
  if (status === 'authenticated') return <Navigate to="/" replace />
  return <Outlet />
}
