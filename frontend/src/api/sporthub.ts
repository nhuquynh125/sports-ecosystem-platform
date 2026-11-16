import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { SkillLevel } from '@/api/types'

// ── tolerant JSON helpers (FastAPI and Laravel payload shapes both work) ─────
type Json = Record<string, unknown>
const rec = (v: unknown): Json => (typeof v === 'object' && v !== null && !Array.isArray(v) ? (v as Json) : {})
const str = (v: unknown): string | null => (typeof v === 'string' && v !== '' ? v : null)
const num = (v: unknown, fallback = 0): number => {
  const n = typeof v === 'number' ? v : typeof v === 'string' && v.trim() !== '' ? Number(v) : NaN
  return Number.isFinite(n) ? n : fallback
}
function unwrapOne(data: unknown): Json {
  const r = rec(data)
  return typeof r.data === 'object' && r.data !== null && !Array.isArray(r.data) ? rec(r.data) : r
}
function toList(data: unknown): unknown[] {
  if (Array.isArray(data)) return data
  const r = rec(data)
  if (Array.isArray(r.items)) return r.items
  if (Array.isArray(r.data)) return r.data
  return []
}

// ── types ────────────────────────────────────────────────────────────────────
export type MatchStatus = 'open' | 'full' | 'ongoing' | 'completed' | 'cancelled'

export interface MatchPerson {
  id: number
  username: string
  full_name: string
  avatar_url: string | null
}
export interface MatchParticipant {
  user: MatchPerson
  status: string
  attended: boolean
}
export interface PickupMatch {
  id: number
  title: string | null
  host_id: number
  host: MatchPerson | null
  sport_id: number
  sport_name: string
  area: string
  skill_level: SkillLevel
  match_date: string // YYYY-MM-DD
  time_slot: string // HH:MM
  max_players: number
  current_players: number
  status: MatchStatus
  description: string | null
  chat_room_id: number | null
  /** null = backend did not include the roster in this payload */
  players: MatchParticipant[] | null
}

export interface MatchFilters {
  sport_id?: number
  area?: string
  skill_level?: string
  match_date?: string
}

export interface MatchCreatePayload {
  sport_id: number
  title: string
  area: string
  skill_level: SkillLevel
  match_date: string
  time_slot: string
  max_players: number
  description: string | null
}

export interface RatingPayload {
  rated_user_id: number
  skill_score: number
  punctuality_score: number
  comment: string | null
}

export interface ChatMessage {
  id: number
  sender_id: number | null
  sender_name: string
  content: string
  created_at: string
}

export interface FeatureBreakdown {
  sport_match: number
  skill_level_proximity: number
  area_match: number
  availability_overlap_ratio: number
  on_time_attendance_rate: number
  avg_rating: number
}
export interface PlayerRecommendation {
  user: MatchPerson
  suitability_pct: number
  breakdown: FeatureBreakdown
}

// ── normalizers ──────────────────────────────────────────────────────────────
function toPerson(raw: unknown, fallbackId = 0): MatchPerson {
  const r = rec(raw)
  const username = str(r.username) ?? ''
  return {
    id: num(r.id, fallbackId),
    username,
    full_name: str(r.full_name) ?? str(r.name) ?? username,
    avatar_url: str(r.avatar_url),
  }
}

function toParticipant(raw: unknown): MatchParticipant {
  const r = rec(raw)
  return {
    user: toPerson(r.user, num(r.user_id)),
    status: str(r.status) ?? 'joined',
    attended: r.attended === true,
  }
}

export function toMatch(raw: unknown): PickupMatch {
  const r = unwrapOne(raw)
  const host = r.host ? toPerson(r.host, num(r.host_id)) : null
  const players = Array.isArray(r.players)
    ? r.players.map(toParticipant).filter((p) => p.status === 'joined')
    : null
  return {
    id: num(r.id),
    title: str(r.title),
    host_id: num(r.host_id, host?.id ?? 0),
    host,
    sport_id: num(r.sport_id, num(rec(r.sport).id)),
    sport_name: str(rec(r.sport).name) ?? 'Sport',
    area: str(r.area) ?? '',
    skill_level: (str(r.skill_level) ?? 'intermediate') as SkillLevel,
    match_date: (str(r.match_date) ?? '').slice(0, 10),
    time_slot: (str(r.time_slot) ?? '').slice(0, 5),
    max_players: num(r.max_players, 10),
    current_players: num(r.current_player_count ?? r.current_players ?? players?.length, 0),
    status: (str(r.status) ?? 'open') as MatchStatus,
    description: str(r.description),
    chat_room_id: r.chat_room_id == null ? null : num(r.chat_room_id),
    players,
  }
}

function toMessage(raw: unknown): ChatMessage {
  const r = rec(raw)
  return {
    id: num(r.id),
    sender_id: r.sender_id == null ? null : num(r.sender_id),
    sender_name: str(r.sender_name) ?? str(rec(r.sender).full_name) ?? 'Player',
    content: str(r.content) ?? '',
    created_at: str(r.created_at) ?? new Date().toISOString(),
  }
}

function toRecommendation(raw: unknown): PlayerRecommendation {
  const r = rec(raw)
  const b = rec(r.feature_breakdown ?? r.breakdown)
  const user = r.user ? toPerson(r.user, num(r.user_id)) : toPerson(r, num(r.user_id))
  return {
    user: { ...user, id: num(r.user_id, user.id) },
    suitability_pct: Math.min(100, Math.max(0, num(r.suitability_pct ?? r.match_percentage))),
    breakdown: {
      sport_match: num(b.sport_match),
      skill_level_proximity: num(b.skill_level_proximity),
      area_match: num(b.area_match),
      availability_overlap_ratio: num(b.availability_overlap_ratio),
      on_time_attendance_rate: num(b.on_time_attendance_rate),
      avg_rating: num(b.avg_rating),
    },
  }
}

// ── query keys ───────────────────────────────────────────────────────────────
export const matchKeys = {
  all: ['matches'] as const,
  list: (filters: MatchFilters) => ['matches', 'list', filters] as const,
  mine: (userId: number | undefined) => ['matches', 'mine', userId] as const,
  detail: (id: number) => ['matches', 'detail', id] as const,
  chat: (roomId: number) => ['chat', roomId] as const,
  smart: (matchId: number) => ['smart-match', matchId] as const,
}

// ── matches ──────────────────────────────────────────────────────────────────
export function useMatches(filters: MatchFilters) {
  return useQuery({
    queryKey: matchKeys.list(filters),
    queryFn: () =>
      api.get('/matches', { params: { ...filters, limit: 60 } }).then((r) => toList(r.data).map(toMatch)),
  })
}

/** There is no /matches/me endpoint, so hosted/joined are derived from the full list (see notes). */
export function useMyMatches(userId: number | undefined) {
  return useQuery({
    queryKey: matchKeys.mine(userId),
    enabled: userId !== undefined,
    queryFn: () =>
      api
        .get('/matches', { params: { status: '', limit: 200 } })
        .then((r) =>
          toList(r.data)
            .map(toMatch)
            .filter((m) => m.host_id === userId || (m.players?.some((p) => p.user.id === userId) ?? false)),
        ),
  })
}

export function useMatch(id: number) {
  return useQuery({
    queryKey: matchKeys.detail(id),
    enabled: Number.isFinite(id),
    refetchInterval: 15_000,
    queryFn: () => api.get(`/matches/${id}`).then((r) => toMatch(r.data)),
  })
}

export function useCreateMatch() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: MatchCreatePayload) =>
      api.post('/matches', payload).then((r) => toMatch(r.data)),
    meta: { silent: true },
    onSuccess: () => qc.invalidateQueries({ queryKey: matchKeys.all }),
  })
}

export function useJoinMatch(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.post(`/matches/${id}/join`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: matchKeys.all }),
  })
}

export function useLeaveMatch(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.delete(`/matches/${id}/leave`).then(() => undefined),
    onSuccess: () => qc.invalidateQueries({ queryKey: matchKeys.all }),
  })
}

export function useRatePlayer(matchId: number) {
  return useMutation({
    mutationFn: (payload: RatingPayload) =>
      api.post(`/matches/${matchId}/ratings`, payload).then((r) => r.data),
    meta: { silent: true },
  })
}

// ── chat (polling; see notes for Reverb) ─────────────────────────────────────
export function useChatMessages(roomId: number | null) {
  return useQuery({
    queryKey: matchKeys.chat(roomId ?? 0),
    enabled: roomId !== null,
    refetchInterval: 3_000,
    meta: { silent: true },
    queryFn: () =>
      api
        .get(`/chat/rooms/${roomId}/messages`, { params: { page_size: 100 } })
        .then((r) => toList(r.data).map(toMessage).sort((a, b) => a.id - b.id)),
  })
}

export function useSendMessage(roomId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (content: string) =>
      api.post(`/chat/rooms/${roomId}/messages`, { content }).then((r) => toMessage(unwrapOne(r.data))),
    onSuccess: (message) => {
      qc.setQueryData<ChatMessage[]>(matchKeys.chat(roomId), (old = []) =>
        old.some((m) => m.id === message.id) ? old : [...old, message],
      )
      void qc.invalidateQueries({ queryKey: matchKeys.chat(roomId) })
    },
  })
}

// ── smart match ──────────────────────────────────────────────────────────────
export function useSmartMatch(matchId: number, topN = 8) {
  return useQuery({
    queryKey: matchKeys.smart(matchId),
    enabled: Number.isFinite(matchId),
    staleTime: 60_000,
    queryFn: () =>
      api
        .post('/ai/smart-match', { match_id: matchId, top_n: topN })
        .then((r) => toList(rec(unwrapOne(r.data)).recommendations).map(toRecommendation)),
  })
}

/** One-click invite = open (or reuse) a direct room, then post a link to the match. */
export function useInvitePlayer() {
  return useMutation({
    mutationFn: async ({ match, userId }: { match: PickupMatch; userId: number }) => {
      const room = unwrapOne(await api.post('/chat/rooms', { user_id: userId }).then((r) => r.data))
      const label = match.title ?? `${match.sport_name} match`
      await api.post(`/chat/rooms/${num(room.id)}/messages`, {
        content: `Join my ${label} on ${match.match_date} at ${match.time_slot} (${match.area}): ${window.location.origin}/matches/${match.id}`,
      })
    },
  })
}