import { ArrowLeft, CalendarDays, Clock, MapPin, Phone } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isApiError } from '@/api/client'
import { bookingApi, venueApi } from '@/api/courtbook'
import type { CourtAvailability, CourtSlot } from '@/api/types'
import { PageHeader } from '@/components/shared/PageHeader'
import { Spinner } from '@/components/shared/Spinner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/hooks/use-auth'
import { toast } from '@/lib/toast'

function formatTime(t: string): string {
  return t.slice(0, 5)
}

function today(): string {
  return new Date().toISOString().split('T')[0]!
}

function maxDate(): string {
  const d = new Date()
  d.setDate(d.getDate() + 90)
  return d.toISOString().split('T')[0]!
}

function formatVND(price: number): string {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(price)
}

type SelectedSlot = {
  courtId: number
  courtName: string
  sportName: string
  slot: CourtSlot
}

function SlotButton({ slot, onClick }: { slot: CourtSlot; onClick?: () => void }) {
  if (slot.status === 'available') {
    return (
      <button
        onClick={onClick}
        className="rounded px-2 py-1 text-xs font-medium bg-green-100 text-green-800 hover:bg-green-200 transition-colors"
      >
        {formatTime(slot.start_time)}
      </button>
    )
  }
  if (slot.status === 'booked') {
    return (
      <button
        disabled
        className="rounded px-2 py-1 text-xs font-medium bg-gray-100 text-gray-400 cursor-not-allowed"
      >
        {formatTime(slot.start_time)}
      </button>
    )
  }
  // past
  return (
    <button
      disabled
      className="rounded px-2 py-1 text-xs font-medium bg-slate-100 text-slate-400 cursor-not-allowed"
    >
      {formatTime(slot.start_time)}
    </button>
  )
}

function CourtRow({ ca, onSelectSlot }: { ca: CourtAvailability; onSelectSlot: (s: SelectedSlot) => void }) {
  return (
    <div className="border rounded-lg p-4 space-y-3">
      <div className="flex items-center gap-2">
        <span className="font-medium">{ca.court.name}</span>
        <Badge variant="secondary" className="text-xs">
          {ca.court.sport.name}
        </Badge>
        {ca.court.surface_type && (
          <Badge variant="outline" className="text-xs capitalize">
            {ca.court.surface_type}
          </Badge>
        )}
        <span className="ml-auto text-sm text-muted-foreground">
          {formatVND(ca.court.hourly_price)}/h
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {ca.slots.map((slot) => (
          <SlotButton
            key={slot.start_time}
            slot={slot}
            onClick={
              slot.status === 'available'
                ? () =>
                    onSelectSlot({
                      courtId: ca.court.id,
                      courtName: ca.court.name,
                      sportName: ca.court.sport.name,
                      slot,
                    })
                : undefined
            }
          />
        ))}
        {ca.slots.length === 0 && (
          <span className="text-sm text-muted-foreground">No slots available.</span>
        )}
      </div>
    </div>
  )
}

export function VenueDetailPage() {
  const { id } = useParams<{ id: string }>()
  const venueId = Number(id)
  const navigate = useNavigate()
  const { status: authStatus } = useAuth()
  const queryClient = useQueryClient()

  const [date, setDate] = useState(today())
  const [selectedSlot, setSelectedSlot] = useState<SelectedSlot | null>(null)

  const venueQuery = useQuery({
    queryKey: ['venue', venueId],
    queryFn: () => venueApi.get(venueId),
    enabled: !isNaN(venueId),
  })

  const availQuery = useQuery({
    queryKey: ['venue-availability', venueId, date],
    queryFn: () => venueApi.availability(venueId, date),
    enabled: !isNaN(venueId),
  })

  const bookMutation = useMutation({
    mutationFn: () =>
      bookingApi.create({
        court_id: selectedSlot!.courtId,
        booking_date: date,
        time_slot: selectedSlot!.slot.start_time,
      }),
    onSuccess: (data) => {
      toast.success(`Booking confirmed! Code: ${data.booking_code}`)
      setSelectedSlot(null)
      void queryClient.invalidateQueries({ queryKey: ['venue-availability', venueId, date] })
    },
    onError: (err) => {
      toast.error(isApiError(err) ? err.messages[0]! : 'Something went wrong')
    },
  })

  function handleSlotSelect(s: SelectedSlot) {
    if (authStatus !== 'authenticated') {
      navigate('/login')
      return
    }
    setSelectedSlot(s)
  }

  if (venueQuery.isPending) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-1/2" />
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-4 w-1/4" />
      </div>
    )
  }

  if (venueQuery.isError || !venueQuery.data) {
    return (
      <div className="py-12 text-center text-destructive text-sm">
        Failed to load venue details.{' '}
        <Button variant="link" onClick={() => void venueQuery.refetch()}>
          Retry
        </Button>
      </div>
    )
  }

  const venue = venueQuery.data

  return (
    <>
      <div className="mb-4">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft className="size-4 mr-1" />
          Back
        </Button>
      </div>

      <PageHeader title={venue.name} description={venue.description ?? undefined} />

      <div className="flex flex-wrap gap-4 mb-6 text-sm text-muted-foreground">
        <div className="flex items-center gap-1">
          <MapPin className="size-4" />
          <span>
            {venue.address}, {venue.city}
            {venue.district ? `, ${venue.district}` : ''}
          </span>
        </div>
        {venue.phone && (
          <div className="flex items-center gap-1">
            <Phone className="size-4" />
            <span>{venue.phone}</span>
          </div>
        )}
        <div className="flex items-center gap-1">
          <Clock className="size-4" />
          <span>
            {formatTime(venue.open_time)} – {formatTime(venue.close_time)}
          </span>
        </div>
      </div>

      {venue.sports.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          {venue.sports.map((s) => (
            <Badge key={s.id} variant="secondary">
              {s.name}
            </Badge>
          ))}
        </div>
      )}

      {/* Date picker */}
      <Card className="p-4 mb-6">
        <div className="flex flex-wrap items-center gap-3">
          <CalendarDays className="size-5 text-muted-foreground" />
          <label htmlFor="avail-date" className="text-sm font-medium">
            Select date:
          </label>
          <input
            id="avail-date"
            type="date"
            value={date}
            min={today()}
            max={maxDate()}
            onChange={(e) => setDate(e.target.value)}
            className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          />
        </div>
      </Card>

      {/* Availability grid */}
      {availQuery.isPending ? (
        <div className="flex justify-center py-10">
          <Spinner className="size-7" />
        </div>
      ) : availQuery.isError ? (
        <div className="py-8 text-center text-destructive text-sm">
          Failed to load availability.{' '}
          <Button variant="link" onClick={() => void availQuery.refetch()}>
            Retry
          </Button>
        </div>
      ) : (availQuery.data?.courts ?? []).length === 0 ? (
        <div className="py-8 text-center text-muted-foreground text-sm">
          No courts available for this date.
        </div>
      ) : (
        <div className="space-y-4">
          {availQuery.data!.courts.map((ca) => (
            <CourtRow key={ca.court.id} ca={ca} onSelectSlot={handleSlotSelect} />
          ))}
        </div>
      )}

      {/* Booking Confirmation Modal */}
      <Dialog open={selectedSlot !== null} onOpenChange={(open) => !open && setSelectedSlot(null)}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Confirm Booking</DialogTitle>
            <DialogDescription>Review your booking details below.</DialogDescription>
          </DialogHeader>
          {selectedSlot && (
            <div className="space-y-3 py-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Venue</span>
                <span className="font-medium">{venue.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Court</span>
                <span className="font-medium">{selectedSlot.courtName}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Date</span>
                <span className="font-medium">{date}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Time</span>
                <span className="font-medium">
                  {formatTime(selectedSlot.slot.start_time)} – {formatTime(selectedSlot.slot.end_time)}
                </span>
              </div>
              <div className="flex justify-between border-t pt-2">
                <span className="font-medium">Total</span>
                <span className="font-semibold text-base">{formatVND(selectedSlot.slot.price)}</span>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedSlot(null)} disabled={bookMutation.isPending}>
              Cancel
            </Button>
            <Button onClick={() => bookMutation.mutate()} loading={bookMutation.isPending}>
              Confirm Booking
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
