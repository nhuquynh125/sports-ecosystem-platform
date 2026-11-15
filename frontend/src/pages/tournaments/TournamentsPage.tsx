/** Tournament directory with sport + status filters. */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Trophy } from 'lucide-react'
import { api } from '@/api/client'
import { tournamentApi, type TournamentOut, type TournamentStatus } from '@/api/sportarena'
import type { Sport } from '@/api/types'
import { EmptyState } from '@/components/shared/EmptyState'
import { PageHeader } from '@/components/shared/PageHeader'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'

const STATUS_OPTIONS: { label: string; value: TournamentStatus | '' }[] = [
  { label: 'All statuses', value: '' },
  { label: 'Registration open', value: 'registration' },
  { label: 'Ongoing', value: 'ongoing' },
  { label: 'Completed', value: 'completed' },
  { label: 'Draft', value: 'draft' },
  { label: 'Cancelled', value: 'cancelled' },
]

const STATUS_COLORS: Record<TournamentStatus, string> = {
  draft: 'bg-muted text-muted-foreground',
  registration: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  ongoing: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  completed: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
  cancelled: 'bg-destructive/10 text-destructive',
}

function TournamentCard({ t, onClick }: { t: TournamentOut; onClick: () => void }) {
  return (
    <Card
      className="p-4 space-y-2 cursor-pointer hover:shadow-md transition-shadow"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-base leading-tight">{t.name}</h3>
        <span
          className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${STATUS_COLORS[t.status]}`}
        >
          {t.status}
        </span>
      </div>
      <div className="flex flex-wrap gap-1">
        <Badge variant="secondary" className="text-xs">
          {t.sport.name}
        </Badge>
        <Badge variant="outline" className="text-xs">
          {t.format.replace('_', ' ')}
        </Badge>
      </div>
      {t.location && <p className="text-sm text-muted-foreground">📍 {t.location}</p>}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>{t.registered_team_count}{t.max_teams ? ` / ${t.max_teams}` : ''} teams</span>
        {t.registration_deadline && (
          <span className="text-xs">Deadline: {t.registration_deadline}</span>
        )}
      </div>
      {t.prize_pool && (
        <p className="text-sm font-medium">🏆 {t.prize_pool}</p>
      )}
    </Card>
  )
}

function TournamentCardSkeleton() {
  return (
    <Card className="p-4 space-y-3">
      <Skeleton className="h-5 w-2/3" />
      <div className="flex gap-2">
        <Skeleton className="h-5 w-16 rounded-full" />
        <Skeleton className="h-5 w-20 rounded-full" />
      </div>
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-4 w-1/3" />
    </Card>
  )
}

const PAGE_SIZE = 12

export function TournamentsPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [sportId, setSportId] = useState<number | undefined>()
  const [status, setStatus] = useState<TournamentStatus | ''>('')

  const sportsQuery = useQuery<{ items: Sport[] }>({
    queryKey: ['sports'],
    queryFn: () => api.get('/sports').then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  })

  const params = {
    sport_id: sportId,
    status: status || undefined,
    page,
    page_size: PAGE_SIZE,
  }

  const tQuery = useQuery({
    queryKey: ['tournaments', params],
    queryFn: () => tournamentApi.list(params),
  })

  const sports = sportsQuery.data?.items ?? []
  const tournaments = tQuery.data?.items ?? []
  const total = tQuery.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <>
      <PageHeader title="Tournaments" description="Find and register for upcoming tournaments." />

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <Select
          value={sportId?.toString() ?? ''}
          onChange={(e) => {
            setSportId(e.target.value ? Number(e.target.value) : undefined)
            setPage(1)
          }}
          aria-label="Filter by sport"
          className="w-[160px]"
        >
          <option value="">All sports</option>
          {sports.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </Select>

        <Select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value as TournamentStatus | '')
            setPage(1)
          }}
          aria-label="Filter by status"
          className="w-[180px]"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </Select>
      </div>

      {/* Grid */}
      {tQuery.isPending ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <TournamentCardSkeleton key={i} />
          ))}
        </div>
      ) : tQuery.isError ? (
        <div className="py-12 text-center text-destructive text-sm">
          Failed to load tournaments. Please try again.
        </div>
      ) : tournaments.length === 0 ? (
        <EmptyState icon={Trophy} title="No tournaments found" description="Try adjusting your filters." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tournaments.map((t) => (
            <TournamentCard key={t.id} t={t} onClick={() => navigate(`/tournaments/${t.id}`)} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!tQuery.isPending && total > PAGE_SIZE && (
        <div className="flex items-center justify-center gap-4 mt-6">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Prev
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Next
          </Button>
        </div>
      )}
    </>
  )
}
