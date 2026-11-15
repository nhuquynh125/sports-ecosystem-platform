/** Mirrors the backend Pydantic schemas (backend/app/schemas). */
import type { Role } from '@/config/roles'

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface User {
  id: number
  email: string
  username: string
  full_name: string
  phone: string | null
  avatar_url: string | null
  date_of_birth: string | null
  is_active: boolean
  allow_scouting: boolean
  roles: Role[]
  last_login_at: string | null
  created_at: string
  updated_at: string
}

export interface UserPublic {
  id: number
  username: string
  full_name: string
  avatar_url: string | null
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  username: string
  password: string
  full_name: string
  role: Role
}

export interface UserUpdatePayload {
  full_name?: string
  phone?: string | null
  avatar_url?: string | null
  date_of_birth?: string | null
  allow_scouting?: boolean
}

export interface PasswordChangePayload {
  current_password: string
  new_password: string
}

export interface Sport {
  id: number
  name: string
  slug: string
  description: string | null
  icon_url: string | null
  is_active: boolean
}

export const SKILL_LEVELS = ['beginner', 'intermediate', 'advanced', 'pro'] as const
export type SkillLevel = (typeof SKILL_LEVELS)[number]
export const PREFERRED_SIDES = ['left', 'right', 'both'] as const
export type PreferredSide = (typeof PREFERRED_SIDES)[number]

export interface PlayerProfile {
  id: number
  user_id: number
  sport_id: number
  position: string | null
  skill_level: SkillLevel
  preferred_side: PreferredSide | null
  height_cm: number | null
  weight_kg: number | null
  city: string | null
  bio: string | null
  is_visible: boolean
  created_at: string
  updated_at: string
  sport: Sport
  user: UserPublic
}

export interface PlayerProfileCreatePayload {
  sport_id: number
  position: string | null
  skill_level: SkillLevel
  preferred_side: PreferredSide | null
  height_cm: number | null
  weight_kg: number | null
  city: string | null
  bio: string | null
  is_visible: boolean
}

export type PlayerProfileUpdatePayload = Partial<Omit<PlayerProfileCreatePayload, 'sport_id'>>

export interface AvailabilitySlot {
  id: number
  player_profile_id: number
  day_of_week: number
  start_time: string
  end_time: string
  created_at: string
}

export interface AvailabilitySlotPayload {
  day_of_week: number
  start_time: string
  end_time: string
}

export interface AppNotification {
  id: number
  type: string
  title: string
  body: string | null
  data: Record<string, unknown> | null
  is_read: boolean
  read_at: string | null
  created_at: string
}

export interface AdminUserListParams {
  page: number
  page_size: number
  q?: string
  role?: string
  is_active?: boolean
}

// ─── CourtBook types ────────────────────────────────────────────────────────

export type SlotStatus = 'available' | 'booked' | 'past'
export type SurfaceType = 'grass' | 'turf' | 'wood' | 'hard' | 'clay' | 'synthetic'

export interface CourtRead {
  id: number
  venue_id: number
  sport_id: number
  sport: Sport
  name: string
  surface_type: SurfaceType | null
  capacity: number | null
  hourly_price: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface VenueBase {
  id: number
  owner_id: number
  name: string
  description: string | null
  address: string
  city: string
  district: string | null
  latitude: number | null
  longitude: number | null
  phone: string | null
  open_time: string // "HH:MM:SS"
  close_time: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface VenueListItem extends VenueBase {
  court_count: number
  min_hourly_price: number | null
  sports: Sport[]
}

export interface VenueDetail extends VenueBase {
  sports: Sport[]
  courts: CourtRead[]
}

export interface OwnerVenueRead extends VenueBase {
  courts: CourtRead[]
}

export interface CourtSlot {
  start_time: string // "HH:MM:SS"
  end_time: string
  status: SlotStatus
  price: number
}

export interface CourtAvailability {
  court: CourtRead
  slots: CourtSlot[]
}

export interface VenueAvailability {
  venue_id: number
  date: string
  slot_minutes: number
  open_time: string
  close_time: string
  courts: CourtAvailability[]
}

export interface BookingOut {
  id: number
  booking_code: string
  court_id: number
  court: CourtRead
  user_id: number
  booking_date: string
  time_slot: string
  end_time: string
  total_price: number
  status: string
  note: string | null
  cancelled_at: string | null
  cancel_reason: string | null
  created_at: string
  updated_at: string
  venue_id: number
  venue_name: string
  court_name: string
}

export interface BookingCreatePayload {
  court_id: number
  booking_date: string
  time_slot: string
  note?: string | null
}

export interface VenueCreatePayload {
  name: string
  description?: string | null
  address: string
  city: string
  district?: string | null
  phone?: string | null
  open_time: string
  close_time: string
  is_active?: boolean
}

export interface CourtCreatePayload {
  sport_id: number
  name: string
  surface_type?: SurfaceType | null
  capacity?: number | null
  hourly_price: number
  is_active?: boolean
}
