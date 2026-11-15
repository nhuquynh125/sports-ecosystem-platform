import { CalendarDays } from 'lucide-react'
import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isApiError } from '@/api/client'
import { bookingApi } from '@/api/courtbook'
import type { BookingOut } from '@/api/types'
import { EmptyState } from '@/components/shared/EmptyState'
import { ConfirmDialog } from '@/components/shared/Modal'
import { PageHeader } from '@/components/shared/PageHeader'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from '@/lib/toast'

function formatTime(t: string): string {
  return t.slice(0, 5)
}

function formatVND(price: number): string {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(price)
}

function statusBadge(status: string) {
  if (status === 'confirmed')
    return <Badge className="bg-green-100 text-green-800 border-transparent capitalize">{status}</Badge>
  if (status === 'cancelled')
    return <Badge variant="destructive" className="capitalize">{status}</Badge>
  if (status === 'completed')
    return <Badge className="bg-blue-100 text-blue-800 border-transparent capitalize">{status}</Badge>
  return <Badge variant="secondary" className="capitalize">{status}</Badge>
}

function BookingCardSkeleton() {
  return (
    <Card className="p-4 space-y-3">
      <div className="flex justify-between">
        <Skeleton className="h-5 w-1/3" />
        <Skeleton className="h-5 w-20 rounded-full" />
      </div>
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-4 w-2/3" />
    </Card>
  )
}

function BookingCard({
  booking,
  onCancel,
}: {
  booking: BookingOut
  onCancel?: (b: BookingOut) => void
}) {
  return (
    <Card className="p-4 space-y-2">
      <div className="flex items-center justify-between">
        <span className="font-mono text-sm font-semibold">{booking.booking_code}</span>
        {statusBadge(booking.status)}
      </div>
      <div className="text-sm font-medium">{booking.venue_name}</div>
      <div className="text-sm text-muted-foreground">
        {booking.court_name}
        {booking.court?.sport && (
          <Badge variant="secondary" className="ml-2 text-xs">
            {booking.court.sport.name}
          </Badge>
        )}
      </div>
      <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
        <span>{booking.booking_date}</span>
        <span>
          {formatTime(booking.time_slot)} – {formatTime(booking.end_time)}
        </span>
        <span className="font-medium text-foreground">{formatVND(booking.total_price)}</span>
      </div>
      {onCancel && booking.status === 'confirmed' && (
        <div className="pt-1">
          <Button variant="destructive" size="sm" onClick={() => onCancel(booking)}>
            Cancel
          </Button>
        </div>
      )}
    </Card>
  )
}

export function MyBookingsPage() {
  const queryClient = useQueryClient()
  const [cancelTarget, setCancelTarget] = useState<BookingOut | null>(null)

  const query = useQuery({
    queryKey: ['my-bookings'],
    queryFn: () => bookingApi.mine({ page_size: 50 }),
  })

  const cancelMutation = useMutation({
    mutationFn: (id: number) => bookingApi.cancel(id),
    onSuccess: () => {
      toast.success('Booking cancelled')
      setCancelTarget(null)
      void queryClient.invalidateQueries({ queryKey: ['my-bookings'] })
    },
    onError: (err) => {
      toast.error(isApiError(err) ? err.messages[0]! : 'Failed to cancel booking')
      setCancelTarget(null)
    },
  })

  const bookings = query.data?.items ?? []
  const upcoming = bookings.filter((b) => b.status === 'confirmed')
  const past = bookings.filter((b) => b.status === 'cancelled' || b.status === 'completed')

  return (
    <>
      <PageHeader title="My Bookings" description="View and manage your court bookings." />

      {query.isPending ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <BookingCardSkeleton key={i} />
          ))}
        </div>
      ) : query.isError ? (
        <div className="py-12 text-center text-destructive text-sm">
          Failed to load bookings.{' '}
          <Button variant="link" onClick={() => void query.refetch()}>
            Retry
          </Button>
        </div>
      ) : (
        <Tabs defaultValue="upcoming">
          <TabsList className="mb-4">
            <TabsTrigger value="upcoming">Upcoming ({upcoming.length})</TabsTrigger>
            <TabsTrigger value="past">Past ({past.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="upcoming">
            {upcoming.length === 0 ? (
              <EmptyState
                icon={CalendarDays}
                title="No upcoming bookings"
                description="Find a court and make your first booking!"
              />
            ) : (
              <div className="space-y-3">
                {upcoming.map((b) => (
                  <BookingCard key={b.id} booking={b} onCancel={setCancelTarget} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="past">
            {past.length === 0 ? (
              <EmptyState
                icon={CalendarDays}
                title="No past bookings"
                description="Your completed and cancelled bookings will appear here."
              />
            ) : (
              <div className="space-y-3">
                {past.map((b) => (
                  <BookingCard key={b.id} booking={b} />
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      )}

      <ConfirmDialog
        open={cancelTarget !== null}
        onOpenChange={(open) => !open && setCancelTarget(null)}
        title="Cancel booking?"
        description={`Are you sure you want to cancel booking ${cancelTarget?.booking_code ?? ''}? This action cannot be undone.`}
        confirmLabel="Yes, cancel"
        cancelLabel="Keep it"
        destructive
        loading={cancelMutation.isPending}
        onConfirm={() => {
          if (cancelTarget) cancelMutation.mutate(cancelTarget.id)
        }}
      />
    </>
  )
}
