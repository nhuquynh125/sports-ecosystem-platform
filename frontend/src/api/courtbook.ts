import { api } from './client'
import type {
  BookingCreatePayload,
  BookingOut,
  CourtCreatePayload,
  CourtRead,
  OwnerVenueRead,
  Page,
  VenueAvailability,
  VenueCreatePayload,
  VenueDetail,
  VenueListItem,
} from './types'

export interface VenueListParams {
  sport_id?: number
  city?: string
  q?: string
  page?: number
  page_size?: number
}

export const venueApi = {
  list: (params?: VenueListParams) =>
    api.get<Page<VenueListItem>>('/venues', { params }).then((r) => r.data),
  get: (id: number) =>
    api.get<VenueDetail>(`/venues/${id}`).then((r) => r.data),
  availability: (id: number, date: string) =>
    api
      .get<VenueAvailability>(`/venues/${id}/availability`, { params: { date } })
      .then((r) => r.data),
  // owner
  mine: (params?: { page?: number; page_size?: number }) =>
    api.get<Page<OwnerVenueRead>>('/venues/owner/mine', { params }).then((r) => r.data),
  create: (payload: VenueCreatePayload) =>
    api.post<OwnerVenueRead>('/venues', payload).then((r) => r.data),
  update: (id: number, payload: Partial<VenueCreatePayload>) =>
    api.patch<OwnerVenueRead>(`/venues/${id}`, payload).then((r) => r.data),
  createCourt: (venueId: number, payload: CourtCreatePayload) =>
    api.post<CourtRead>(`/venues/${venueId}/courts`, payload).then((r) => r.data),
  updateCourt: (venueId: number, courtId: number, payload: Partial<CourtCreatePayload>) =>
    api.patch<CourtRead>(`/venues/${venueId}/courts/${courtId}`, payload).then((r) => r.data),
  venuebookings: (venueId: number, params?: { page?: number; page_size?: number }) =>
    api.get<Page<BookingOut>>(`/bookings/venue/${venueId}`, { params }).then((r) => r.data),
}

export const bookingApi = {
  create: (payload: BookingCreatePayload) =>
    api.post<BookingOut>('/bookings', payload).then((r) => r.data),
  mine: (params?: { page?: number; page_size?: number }) =>
    api.get<Page<BookingOut>>('/bookings/me', { params }).then((r) => r.data),
  cancel: (id: number, reason?: string) =>
    api.delete(`/bookings/${id}`, { data: { cancel_reason: reason ?? null } }),
}
