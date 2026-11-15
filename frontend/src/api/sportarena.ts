/** SportArena API — teams and tournaments. */
import { api } from './client'
import type { Page } from './types'

// ─── Team types ──────────────────────────────────────────────────────────────

export interface SportRef {
  id: number
  name: string
  slug: string
}

export interface CaptainRef {
  id: number
  username: string
  full_name: string
  avatar_url: string | null
}

export interface TeamMember {
  id: number
  user_id: number
  username: string
  full_name: string
  avatar_url: string | null
  role: string
  joined_at: string
}

export interface TeamOut {
  id: number
  name: string
  slug: string
  sport: SportRef
  captain: CaptainRef
  description: string | null
  logo_url: string | null
  city: string | null
  is_active: boolean
  created_at: string
  member_count: number
}

export interface TeamDetailOut extends TeamOut {
  members: TeamMember[]
}

export interface TeamCreatePayload {
  name: string
  sport_id: number
  description?: string | null
  logo_url?: string | null
  city?: string | null
}

// ─── Tournament types ─────────────────────────────────────────────────────────

export interface TeamRef {
  id: number
  name: string
  slug: string
  logo_url: string | null
}

export interface OrganizerRef {
  id: number
  username: string
  full_name: string
  avatar_url: string | null
}

export type RegistrationStatus = 'pending' | 'approved' | 'rejected'

export interface RegistrationOut {
  id: number
  team: TeamRef
  registration_status: RegistrationStatus
  registered_at: string
  reviewed_at: string | null
  rejection_reason: string | null
}

export interface GroupTeamOut {
  id: number
  tournament_team_id: number
  team: TeamRef
  seeding: number | null
}

export interface GroupOut {
  id: number
  name: string
  description: string | null
  created_at: string
  teams: GroupTeamOut[]
}

export type TournamentStatus = 'draft' | 'registration' | 'ongoing' | 'completed' | 'cancelled'
export type TournamentFormat = 'group_stage' | 'knockout' | 'round_robin' | 'double_elimination'

export interface TournamentOut {
  id: number
  name: string
  sport: SportRef
  organizer: OrganizerRef
  description: string | null
  format: TournamentFormat
  status: TournamentStatus
  max_teams: number | null
  prize_pool: string | null
  location: string | null
  start_date: string | null
  end_date: string | null
  registration_deadline: string | null
  is_public: boolean
  registered_team_count: number
  created_at: string
}

export interface TournamentDetailOut extends TournamentOut {
  rules: string | null
  registrations: RegistrationOut[]
  groups: GroupOut[]
}

export interface TournamentCreatePayload {
  name: string
  sport_id: number
  description?: string | null
  format?: TournamentFormat
  max_teams?: number | null
  prize_pool?: string | null
  location?: string | null
  start_date?: string | null
  end_date?: string | null
  registration_deadline?: string | null
  rules?: string | null
  is_public?: boolean
}

export interface RegistrationDecisionPayload {
  action: 'approve' | 'reject'
  rejection_reason?: string | null
}

export interface GroupCreatePayload {
  name: string
  description?: string | null
  team_ids: number[]
}

// ─── Team API ─────────────────────────────────────────────────────────────────

export interface TeamListParams {
  sport_id?: number
  page?: number
  page_size?: number
}

export const teamApi = {
  list: (params?: TeamListParams) =>
    api.get<Page<TeamOut>>('/teams', { params }).then((r) => r.data),
  mine: () =>
    api.get<TeamOut[]>('/teams/me').then((r) => r.data),
  get: (id: number) =>
    api.get<TeamDetailOut>(`/teams/${id}`).then((r) => r.data),
  create: (payload: TeamCreatePayload) =>
    api.post<TeamDetailOut>('/teams', payload).then((r) => r.data),
  addMember: (teamId: number, userId: number) =>
    api.post<TeamMember>(`/teams/${teamId}/members`, { user_id: userId }).then((r) => r.data),
  removeMember: (teamId: number, userId: number) =>
    api.delete(`/teams/${teamId}/members/${userId}`),
}

// ─── Match / Schedule / Standings types ──────────────────────────────────────

export interface MatchEventOut {
  id: number
  player_id: number | null
  team_id: number
  event_type: string
  minute: number | null
  notes: string | null
}

export interface MatchOut {
  id: number
  tournament_id: number
  group_id: number | null
  group_name: string | null
  home_team_id: number
  home_team_name: string
  away_team_id: number
  away_team_name: string
  court_id: number | null
  match_date: string | null
  time_slot: string | null
  home_score: number | null
  away_score: number | null
  status: string
  events: MatchEventOut[]
}

export interface StandingRow {
  team_id: number
  team_name: string
  group_id: number
  group_name: string
  played: number
  won: number
  drawn: number
  lost: number
  goals_for: number
  goals_against: number
  goal_difference: number
  points: number
}

export interface TopScorerRow {
  player_id: number
  player_name: string
  team_id: number
  team_name: string
  goals: number
}

export interface ScheduleGenerateRequest {
  court_ids: number[]
  start_date: string
  end_date: string
  daily_time_slots: string[]
  min_matches_per_team?: number
}

export interface ScheduleGenerateOut {
  matches_created: number
  conflicts_skipped: number
}

export interface MatchEventIn {
  player_id?: number | null
  team_id: number
  event_type: 'goal' | 'assist' | 'yellow_card' | 'red_card' | 'own_goal'
  minute?: number | null
  notes?: string | null
}

export interface MatchResultSubmit {
  home_score: number
  away_score: number
  events: MatchEventIn[]
}

// ─── Tournament API ───────────────────────────────────────────────────────────

export interface TournamentListParams {
  sport_id?: number
  status?: TournamentStatus
  page?: number
  page_size?: number
}

export const tournamentApi = {
  list: (params?: TournamentListParams) =>
    api.get<Page<TournamentOut>>('/tournaments', { params }).then((r) => r.data),
  get: (id: number) =>
    api.get<TournamentDetailOut>(`/tournaments/${id}`).then((r) => r.data),
  create: (payload: TournamentCreatePayload) =>
    api.post<TournamentOut>('/tournaments', payload).then((r) => r.data),
  registerTeam: (tournamentId: number) =>
    api.post<RegistrationOut>(`/tournaments/${tournamentId}/register`).then((r) => r.data),
  decideRegistration: (tournamentId: number, teamId: number, payload: RegistrationDecisionPayload) =>
    api
      .patch<RegistrationOut>(`/tournaments/${tournamentId}/registrations/${teamId}`, payload)
      .then((r) => r.data),
  createGroup: (tournamentId: number, payload: GroupCreatePayload) =>
    api.post<GroupOut>(`/tournaments/${tournamentId}/groups`, payload).then((r) => r.data),
  generateSchedule: (tournamentId: number, payload: ScheduleGenerateRequest) =>
    api
      .post<ScheduleGenerateOut>(`/tournaments/${tournamentId}/generate-schedule`, payload)
      .then((r) => r.data),
  listMatches: (tournamentId: number) =>
    api.get<MatchOut[]>(`/tournaments/${tournamentId}/matches`).then((r) => r.data),
  submitResult: (tournamentId: number, matchId: number, payload: MatchResultSubmit) =>
    api
      .patch<MatchOut>(`/tournaments/${tournamentId}/matches/${matchId}/result`, payload)
      .then((r) => r.data),
  getStandings: (tournamentId: number) =>
    api.get<StandingRow[]>(`/tournaments/${tournamentId}/standings`).then((r) => r.data),
  getTopScorers: (tournamentId: number) =>
    api.get<TopScorerRow[]>(`/tournaments/${tournamentId}/top-scorers`).then((r) => r.data),
}
