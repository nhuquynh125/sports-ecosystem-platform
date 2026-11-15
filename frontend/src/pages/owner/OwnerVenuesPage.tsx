import { Building2, ChevronDown, ChevronUp, PlusCircle } from 'lucide-react'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import { isApiError } from '@/api/client'
import { venueApi } from '@/api/courtbook'
import type { BookingOut, CourtCreatePayload, CourtRead, OwnerVenueRead, Sport, VenueCreatePayload } from '@/api/types'
import { EmptyState } from '@/components/shared/EmptyState'
import { Field } from '@/components/shared/Field'
import { Modal, ModalActions } from '@/components/shared/Modal'
import { PageHeader } from '@/components/shared/PageHeader'
import { Spinner } from '@/components/shared/Spinner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/lib/toast'

// ─── Venue Form ──────────────────────────────────────────────────────────────

const venueSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  address: z.string().min(1, 'Address is required'),
  city: z.string().min(1, 'City is required'),
  district: z.string().optional(),
  phone: z.string().optional(),
  open_time: z.string().min(1, 'Open time is required'),
  close_time: z.string().min(1, 'Close time is required'),
  description: z.string().optional(),
  is_active: z.boolean().optional(),
})
type VenueFormValues = z.infer<typeof venueSchema>

function VenueFormModal({
  open,
  onClose,
  venue,
}: {
  open: boolean
  onClose: () => void
  venue?: OwnerVenueRead
}) {
  const queryClient = useQueryClient()
  const isEdit = !!venue

  const form = useForm<VenueFormValues>({
    resolver: zodResolver(venueSchema),
    defaultValues: {
      name: venue?.name ?? '',
      address: venue?.address ?? '',
      city: venue?.city ?? '',
      district: venue?.district ?? '',
      phone: venue?.phone ?? '',
      open_time: venue?.open_time?.slice(0, 5) ?? '06:00',
      close_time: venue?.close_time?.slice(0, 5) ?? '22:00',
      description: venue?.description ?? '',
      is_active: venue?.is_active ?? true,
    },
  })
  const isActive = useWatch({ control: form.control, name: 'is_active' }) ?? true

  const mutation = useMutation({
    mutationFn: (values: VenueFormValues) => {
      const payload: VenueCreatePayload = {
        name: values.name,
        address: values.address,
        city: values.city,
        district: values.district || null,
        phone: values.phone || null,
        open_time: values.open_time + ':00',
        close_time: values.close_time + ':00',
        description: values.description || null,
        is_active: values.is_active ?? true,
      }
      return isEdit ? venueApi.update(venue!.id, payload) : venueApi.create(payload)
    },
    onSuccess: () => {
      toast.success(isEdit ? 'Venue updated' : 'Venue created')
      void queryClient.invalidateQueries({ queryKey: ['owner-venues'] })
      onClose()
    },
    onError: (err) => {
      toast.error(isApiError(err) ? err.messages[0]! : 'Something went wrong')
    },
  })

  return (
    <Modal
      open={open}
      onOpenChange={(o) => !o && onClose()}
      title={isEdit ? 'Edit Venue' : 'New Venue'}
      size="lg"
    >
      <form onSubmit={form.handleSubmit((v) => mutation.mutate(v))} className="space-y-4">
        <Field label="Name" htmlFor="v-name" required error={form.formState.errors.name?.message}>
          <Input id="v-name" {...form.register('name')} />
        </Field>
        <Field label="Address" htmlFor="v-addr" required error={form.formState.errors.address?.message}>
          <Input id="v-addr" {...form.register('address')} />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="City" htmlFor="v-city" required error={form.formState.errors.city?.message}>
            <Input id="v-city" {...form.register('city')} />
          </Field>
          <Field label="District" htmlFor="v-dist" error={form.formState.errors.district?.message}>
            <Input id="v-dist" {...form.register('district')} />
          </Field>
        </div>
        <Field label="Phone" htmlFor="v-phone" error={form.formState.errors.phone?.message}>
          <Input id="v-phone" {...form.register('phone')} />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Open time" htmlFor="v-open" required error={form.formState.errors.open_time?.message}>
            <Input id="v-open" type="time" {...form.register('open_time')} />
          </Field>
          <Field label="Close time" htmlFor="v-close" required error={form.formState.errors.close_time?.message}>
            <Input id="v-close" type="time" {...form.register('close_time')} />
          </Field>
        </div>
        <Field label="Description" htmlFor="v-desc" error={form.formState.errors.description?.message}>
          <Textarea id="v-desc" {...form.register('description')} rows={3} />
        </Field>
        <div className="flex items-center gap-3">
          <Switch
            id="v-active"
            checked={isActive}
            onCheckedChange={(v) => form.setValue('is_active', v)}
          />
          <label htmlFor="v-active" className="text-sm font-medium cursor-pointer">
            Active (visible to players)
          </label>
        </div>

        <ModalActions>
          <Button type="button" variant="outline" onClick={onClose} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending}>
            {isEdit ? 'Save changes' : 'Create venue'}
          </Button>
        </ModalActions>
      </form>
    </Modal>
  )
}

// ─── Court Form ──────────────────────────────────────────────────────────────

const SURFACE_TYPES = ['grass', 'turf', 'wood', 'hard', 'clay', 'synthetic'] as const

const courtSchema = z.object({
  sport_id: z.coerce.number().min(1, 'Sport is required'),
  name: z.string().min(1, 'Name is required'),
  surface_type: z.string().optional(),
  capacity: z.coerce.number().optional(),
  hourly_price: z.coerce.number().min(0, 'Price must be ≥ 0'),
  is_active: z.boolean().optional(),
})
type CourtFormValues = z.infer<typeof courtSchema>

function CourtFormModal({
  open,
  onClose,
  venueId,
  court,
}: {
  open: boolean
  onClose: () => void
  venueId: number
  court?: CourtRead
}) {
  const queryClient = useQueryClient()
  const isEdit = !!court

  const sportsQuery = useQuery<Sport[]>({
    queryKey: ['sports'],
    queryFn: () => api.get<Sport[]>('/sports').then((r) => r.data),
    staleTime: 5 * 60_000,
  })

  const form = useForm<CourtFormValues>({
    resolver: zodResolver(courtSchema),
    defaultValues: {
      sport_id: court?.sport_id ?? 0,
      name: court?.name ?? '',
      surface_type: court?.surface_type ?? '',
      capacity: court?.capacity ?? undefined,
      hourly_price: court?.hourly_price ?? 0,
      is_active: court?.is_active ?? true,
    },
  })
  const isActive = useWatch({ control: form.control, name: 'is_active' }) ?? true

  const mutation = useMutation({
    mutationFn: (values: CourtFormValues) => {
      const payload: CourtCreatePayload = {
        sport_id: values.sport_id,
        name: values.name,
        surface_type: (values.surface_type as CourtCreatePayload['surface_type']) || null,
        capacity: values.capacity ?? null,
        hourly_price: values.hourly_price,
        is_active: values.is_active ?? true,
      }
      return isEdit
        ? venueApi.updateCourt(venueId, court!.id, payload)
        : venueApi.createCourt(venueId, payload)
    },
    onSuccess: () => {
      toast.success(isEdit ? 'Court updated' : 'Court added')
      void queryClient.invalidateQueries({ queryKey: ['owner-venues'] })
      onClose()
    },
    onError: (err) => {
      toast.error(isApiError(err) ? err.messages[0]! : 'Something went wrong')
    },
  })

  return (
    <Modal
      open={open}
      onOpenChange={(o) => !o && onClose()}
      title={isEdit ? 'Edit Court' : 'Add Court'}
      size="md"
    >
      <form onSubmit={form.handleSubmit((v) => mutation.mutate(v))} className="space-y-4">
        <Field label="Sport" htmlFor="c-sport" required error={form.formState.errors.sport_id?.message}>
          <Select id="c-sport" {...form.register('sport_id')}>
            <option value="">Select sport</option>
            {(sportsQuery.data ?? []).map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Court name" htmlFor="c-name" required error={form.formState.errors.name?.message}>
          <Input id="c-name" {...form.register('name')} />
        </Field>
        <Field label="Surface type" htmlFor="c-surf" error={form.formState.errors.surface_type?.message}>
          <Select id="c-surf" {...form.register('surface_type')}>
            <option value="">— none —</option>
            {SURFACE_TYPES.map((t) => (
              <option key={t} value={t} className="capitalize">
                {t}
              </option>
            ))}
          </Select>
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Capacity" htmlFor="c-cap" error={form.formState.errors.capacity?.message}>
            <Input id="c-cap" type="number" min={0} {...form.register('capacity')} />
          </Field>
          <Field label="Hourly price (VND)" htmlFor="c-price" required error={form.formState.errors.hourly_price?.message}>
            <Input id="c-price" type="number" min={0} {...form.register('hourly_price')} />
          </Field>
        </div>
        <div className="flex items-center gap-3">
          <Switch
            id="c-active"
            checked={isActive}
            onCheckedChange={(v) => form.setValue('is_active', v)}
          />
          <label htmlFor="c-active" className="text-sm font-medium cursor-pointer">
            Active
          </label>
        </div>

        <ModalActions>
          <Button type="button" variant="outline" onClick={onClose} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending}>
            {isEdit ? 'Save changes' : 'Add court'}
          </Button>
        </ModalActions>
      </form>
    </Modal>
  )
}

// ─── Venue Bookings Modal ─────────────────────────────────────────────────────

function VenueBookingsModal({
  open,
  onClose,
  venueId,
  venueName,
}: {
  open: boolean
  onClose: () => void
  venueId: number
  venueName: string
}) {
  const query = useQuery({
    queryKey: ['venue-bookings', venueId],
    queryFn: () => venueApi.venuebookings(venueId, { page_size: 50 }),
    enabled: open,
  })

  const bookings: BookingOut[] = query.data?.items ?? []

  return (
    <Modal open={open} onOpenChange={(o) => !o && onClose()} title={`Bookings — ${venueName}`} size="xl">
      {query.isPending ? (
        <div className="flex justify-center py-8">
          <Spinner className="size-6" />
        </div>
      ) : bookings.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-6">No bookings yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-muted-foreground text-left">
                <th className="pb-2 pr-3 font-medium">Code</th>
                <th className="pb-2 pr-3 font-medium">Court</th>
                <th className="pb-2 pr-3 font-medium">Player</th>
                <th className="pb-2 pr-3 font-medium">Date</th>
                <th className="pb-2 pr-3 font-medium">Time</th>
                <th className="pb-2 pr-3 font-medium">Price</th>
                <th className="pb-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {bookings.map((b) => (
                <tr key={b.id} className="border-b last:border-0">
                  <td className="py-2 pr-3 font-mono">{b.booking_code}</td>
                  <td className="py-2 pr-3">{b.court_name}</td>
                  <td className="py-2 pr-3 text-muted-foreground">{b.user_id}</td>
                  <td className="py-2 pr-3">{b.booking_date}</td>
                  <td className="py-2 pr-3">
                    {b.time_slot.slice(0, 5)} – {b.end_time.slice(0, 5)}
                  </td>
                  <td className="py-2 pr-3">
                    {new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(b.total_price)}
                  </td>
                  <td className="py-2">
                    <Badge
                      variant={
                        b.status === 'confirmed'
                          ? 'success'
                          : b.status === 'cancelled'
                            ? 'destructive'
                            : 'secondary'
                      }
                      className="capitalize"
                    >
                      {b.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Modal>
  )
}

// ─── Courts Panel ─────────────────────────────────────────────────────────────

function CourtsPanel({ venue }: { venue: OwnerVenueRead }) {
  const [addCourtOpen, setAddCourtOpen] = useState(false)
  const [editCourt, setEditCourt] = useState<CourtRead | null>(null)

  return (
    <div className="mt-3 border rounded-lg p-4 space-y-3 bg-muted/30">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold">Courts ({venue.courts.length})</span>
        <Button size="sm" variant="outline" onClick={() => setAddCourtOpen(true)}>
          <PlusCircle className="size-4 mr-1" />
          Add court
        </Button>
      </div>
      {venue.courts.length === 0 ? (
        <p className="text-xs text-muted-foreground">No courts yet. Add your first court.</p>
      ) : (
        <div className="space-y-2">
          {venue.courts.map((c) => (
            <div key={c.id} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <span className="font-medium">{c.name}</span>
                <Badge variant="secondary" className="text-xs">{c.sport.name}</Badge>
                {!c.is_active && <Badge variant="outline" className="text-xs">Inactive</Badge>}
              </div>
              <div className="flex items-center gap-3">
                <span className="text-muted-foreground">
                  {new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(c.hourly_price)}/h
                </span>
                <Button size="sm" variant="ghost" onClick={() => setEditCourt(c)}>
                  Edit
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <CourtFormModal
        open={addCourtOpen}
        onClose={() => setAddCourtOpen(false)}
        venueId={venue.id}
      />
      {editCourt && (
        <CourtFormModal
          open
          onClose={() => setEditCourt(null)}
          venueId={venue.id}
          court={editCourt}
        />
      )}
    </div>
  )
}

// ─── Venue Row ─────────────────────────────────────────────────────────────────

function VenueRow({ venue }: { venue: OwnerVenueRead }) {
  const [showCourts, setShowCourts] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [bookingsOpen, setBookingsOpen] = useState(false)

  return (
    <Card className="p-4 space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold">{venue.name}</span>
            <Badge variant={venue.is_active ? 'success' : 'secondary'} className="text-xs">
              {venue.is_active ? 'Active' : 'Inactive'}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            {venue.city}
            {venue.district ? `, ${venue.district}` : ''} · {venue.courts.length} court{venue.courts.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Button size="sm" variant="outline" onClick={() => setEditOpen(true)}>
            Edit
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowCourts((v) => !v)}
          >
            Courts
            {showCourts ? <ChevronUp className="size-4 ml-1" /> : <ChevronDown className="size-4 ml-1" />}
          </Button>
          <Button size="sm" variant="outline" onClick={() => setBookingsOpen(true)}>
            Bookings
          </Button>
        </div>
      </div>

      {showCourts && <CourtsPanel venue={venue} />}

      <VenueFormModal open={editOpen} onClose={() => setEditOpen(false)} venue={venue} />
      <VenueBookingsModal
        open={bookingsOpen}
        onClose={() => setBookingsOpen(false)}
        venueId={venue.id}
        venueName={venue.name}
      />
    </Card>
  )
}

// ─── Page ──────────────────────────────────────────────────────────────────────

export function OwnerVenuesPage() {
  const [createOpen, setCreateOpen] = useState(false)

  const query = useQuery({
    queryKey: ['owner-venues'],
    queryFn: () => venueApi.mine({ page_size: 50 }),
  })

  return (
    <>
      <PageHeader
        title="My Venues"
        description="Manage your venues, courts and bookings."
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <PlusCircle className="size-4 mr-2" />
            New Venue
          </Button>
        }
      />

      {query.isPending ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} className="p-4">
              <Skeleton className="h-5 w-1/3 mb-2" />
              <Skeleton className="h-4 w-1/4" />
            </Card>
          ))}
        </div>
      ) : query.isError ? (
        <div className="py-12 text-center text-destructive text-sm">
          Failed to load venues.{' '}
          <Button variant="link" onClick={() => void query.refetch()}>
            Retry
          </Button>
        </div>
      ) : (query.data?.items ?? []).length === 0 ? (
        <EmptyState
          icon={Building2}
          title="No venues yet"
          description="Create your first venue to start accepting bookings."
          action={
            <Button onClick={() => setCreateOpen(true)}>
              <PlusCircle className="size-4 mr-2" />
              New Venue
            </Button>
          }
        />
      ) : (
        <div className="space-y-3">
          {query.data!.items.map((v) => (
            <VenueRow key={v.id} venue={v} />
          ))}
        </div>
      )}

      <VenueFormModal open={createOpen} onClose={() => setCreateOpen(false)} />
    </>
  )
}
