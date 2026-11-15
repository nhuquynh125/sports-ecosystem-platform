import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import { AppLayout } from '@/components/shared/AppLayout'
import { Spinner } from '@/components/shared/Spinner'
import { DashboardPage } from '@/pages/DashboardPage'
import { LoginPage } from '@/pages/LoginPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { RegisterPage } from '@/pages/RegisterPage'
import { GuestRoute } from '@/routes/GuestRoute'
import { ProtectedRoute } from '@/routes/ProtectedRoute'

// Admin
const AdminUsersPage = lazy(() =>
  import('@/pages/admin/AdminUsersPage').then((m) => ({ default: m.AdminUsersPage })),
)

// CourtBook — venue browsing & booking
const VenuesPage = lazy(() =>
  import('@/pages/venues/VenuesPage').then((m) => ({ default: m.VenuesPage })),
)
const VenueDetailPage = lazy(() =>
  import('@/pages/venues/VenueDetailPage').then((m) => ({ default: m.VenueDetailPage })),
)
const MyBookingsPage = lazy(() =>
  import('@/pages/bookings/MyBookingsPage').then((m) => ({ default: m.MyBookingsPage })),
)
const OwnerVenuesPage = lazy(() =>
  import('@/pages/owner/OwnerVenuesPage').then((m) => ({ default: m.OwnerVenuesPage })),
)

// SportArena — teams
const TeamsPage = lazy(() =>
  import('@/pages/teams/TeamsPage').then((m) => ({ default: m.TeamsPage })),
)
const TeamDetailPage = lazy(() =>
  import('@/pages/teams/TeamDetailPage').then((m) => ({ default: m.TeamDetailPage })),
)

// SportArena — tournaments
const TournamentsPage = lazy(() =>
  import('@/pages/tournaments/TournamentsPage').then((m) => ({ default: m.TournamentsPage })),
)
const TournamentDetailPage = lazy(() =>
  import('@/pages/tournaments/TournamentDetailPage').then((m) => ({
    default: m.TournamentDetailPage,
  })),
)

// Organizer dashboard
const OrganizerTournamentsPage = lazy(() =>
  import('@/pages/organizer/OrganizerTournamentsPage').then((m) => ({
    default: m.OrganizerTournamentsPage,
  })),
)

const SuspenseFallback = () => (
  <div className="flex justify-center py-20">
    <Spinner className="size-7" />
  </div>
)

export default function App() {
  return (
    <Routes>
      <Route element={<GuestRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Any signed-in user */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />

          {/* CourtBook — venue browsing & booking */}
          <Route
            path="/venues"
            element={
              <Suspense fallback={<SuspenseFallback />}>
                <VenuesPage />
              </Suspense>
            }
          />
          <Route
            path="/venues/:id"
            element={
              <Suspense fallback={<SuspenseFallback />}>
                <VenueDetailPage />
              </Suspense>
            }
          />
          <Route
            path="/bookings/me"
            element={
              <Suspense fallback={<SuspenseFallback />}>
                <MyBookingsPage />
              </Suspense>
            }
          />

          {/* SportArena — Teams */}
          <Route
            path="/teams"
            element={
              <Suspense fallback={<SuspenseFallback />}>
                <TeamsPage />
              </Suspense>
            }
          />
          <Route
            path="/teams/:id"
            element={
              <Suspense fallback={<SuspenseFallback />}>
                <TeamDetailPage />
              </Suspense>
            }
          />

          {/* SportArena — Tournaments */}
          <Route
            path="/tournaments"
            element={
              <Suspense fallback={<SuspenseFallback />}>
                <TournamentsPage />
              </Suspense>
            }
          />
          <Route
            path="/tournaments/:id"
            element={
              <Suspense fallback={<SuspenseFallback />}>
                <TournamentDetailPage />
              </Suspense>
            }
          />

          {/* Venue owner dashboard */}
          <Route element={<ProtectedRoute roles={['venue_owner', 'admin']} />}>
            <Route
              path="/owner/venues"
              element={
                <Suspense fallback={<SuspenseFallback />}>
                  <OwnerVenuesPage />
                </Suspense>
              }
            />
          </Route>

          {/* Organizer dashboard */}
          <Route element={<ProtectedRoute roles={['organizer', 'admin']} />}>
            <Route
              path="/organizer/tournaments"
              element={
                <Suspense fallback={<SuspenseFallback />}>
                  <OrganizerTournamentsPage />
                </Suspense>
              }
            />
          </Route>

          {/* Admin */}
          <Route element={<ProtectedRoute roles={['admin']} />}>
            <Route
              path="/admin/users"
              element={
                <Suspense fallback={<SuspenseFallback />}>
                  <AdminUsersPage />
                </Suspense>
              }
            />
          </Route>

          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  )
}
