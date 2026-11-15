import { Building2, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { venueApi } from '@/api/courtbook'
import type { Sport, VenueListItem } from '@/api/types'
import { EmptyState } from '@/components/shared/EmptyState'
import { PageHeader } from '@/components/shared/PageHeader'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'

const PAGE_SIZE = 12

function formatVND(price: number | null): string {
  if (price == null) return '—'
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(price)
}

function formatTime(t: string): string {
  return t.slice(0, 5)
}

function VenueCardSkeleton() {
  return (
    <Card className="p-4 space-y-3">
      <Skeleton className="h-5 w-2/3" />
      <Skeleton className="h-4 w-1/2" />
      <div className="flex gap-2">
        <Skeleton className="h-5 w-16 rounded-full" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
      <Skeleton className="h-4 w-1/3" />
    </Card>
  )
}

function VenueCard({ venue, onClick }: { venue: VenueListItem; onClick: () => void }) {
  return (
    <Card
      className="p-4 space-y-2 cursor-pointer hover:shadow-md transition-shadow"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
    >
      <h3 className="font-semibold text-base leading-tight">{venue.name}</h3>
      <p className="text-sm text-muted-foreground">
        {venue.city}
        {venue.district ? `, ${venue.district}` : ''}
      </p>
      {venue.sports.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {venue.sports.map((s) => (
            <Badge key={s.id} variant="secondary" className="text-xs">
              {s.name}
            </Badge>
          ))}
        </div>
      )}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>{venue.court_count} court{venue.court_count !== 1 ? 's' : ''}</span>
        {venue.min_hourly_price != null && (
          <span className="font-medium text-foreground">from {formatVND(venue.min_hourly_price)}/h</span>
        )}
      </div>
      <p className="text-xs text-muted-foreground">
        Open {formatTime(venue.open_time)} – {formatTime(venue.close_time)}
      </p>
    </Card>
  )
}

export function VenuesPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [sportId, setSportId] = useState<number | undefined>()
  const [city, setCity] = useState('')
  const [q, setQ] = useState('')
  const [inputQ, setInputQ] = useState('')

  const sportsQuery = useQuery<{ items: Sport[] }>({
    queryKey: ['sports'],
    queryFn: () => api.get('/sports').then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  })

  const params = { sport_id: sportId, city: city || undefined, q: q || undefined, page, page_size: PAGE_SIZE }

  const venuesQuery = useQuery({
    queryKey: ['venues', params],
    queryFn: () => venueApi.list(params),
  })

  const total = venuesQuery.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  function handleSearch() {
    setQ(inputQ)
    setPage(1)
  }

  return (
    <>
      <PageHeader title="Find a court" description="Browse venues and book a court near you." />

      {/* Filter bar */}
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
          {sportsQuery.data?.items.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </Select>

        <input
          type="text"
          placeholder="City…"
          value={city}
          onChange={(e) => { setCity(e.target.value); setPage(1) }}
          className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring w-[140px]"
        />

        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Search venues…"
            value={inputQ}
            onChange={(e) => setInputQ(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring w-[200px]"
          />
          <Button variant="outline" size="sm" onClick={handleSearch}>
            <Search className="size-4 mr-1" />
            Search
          </Button>
        </div>
      </div>

      {/* Grid */}
      {venuesQuery.isPending ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <VenueCardSkeleton key={i} />
          ))}
        </div>
      ) : venuesQuery.isError ? (
        <div className="py-12 text-center text-destructive text-sm">
          Failed to load venues. Please try again.
        </div>
      ) : (venuesQuery.data?.items ?? []).length === 0 ? (
        <EmptyState
          icon={Building2}
          title="No venues found"
          description="Try adjusting your filters or search term."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {venuesQuery.data!.items.map((v) => (
            <VenueCard key={v.id} venue={v} onClick={() => navigate(`/venues/${v.id}`)} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!venuesQuery.isPending && total > PAGE_SIZE && (
        <div className="flex items-center justify-center gap-4 mt-6">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            <ChevronLeft className="size-4" />
            Prev
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
            <ChevronRight className="size-4" />
          </Button>
        </div>
      )}
    </>
  )
}
