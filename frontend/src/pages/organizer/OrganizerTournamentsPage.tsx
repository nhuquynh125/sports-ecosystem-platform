/** Organizer dashboard: create tournaments, review registrations, assign groups. */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, ChevronDown, ChevronUp, ClipboardList, CalendarClock, Plus, XCircle } from 'lucide-react'
import { getErrorMessage } from '@/api/client'
import { api } from '@/api/client'
import {
  tournamentApi,
  type GroupCreatePayload,
  type RegistrationOut,
  type TournamentCreatePayload,
  type TournamentDetailOut,
  type TournamentOut,
} from '@/api/sportarena'
import type { Sport } from '@/api/types'
import { EmptyState } from '@/components/shared/EmptyState'
import { FormAlert } from '@/components/shared/FormAlert'
import { Modal, ModalActions } from '@/components/shared/Modal'
import { PageHeader } from '@/components/shared/PageHeader'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Textarea } from '@/components/ui/textarea'
import { useAuth } from '@/hooks/use-auth'

// ─── Create tournament modal ──────────────────────────────────────────────────

function CreateTournamentModal({
  open,
  onOpenChange,
  sports,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  sports: Sport[]
}) {
  const qc = useQueryClient()
  const [form, setForm] = useState<TournamentCreatePayload>({
    name: '',
    sport_id: sports[0]?.id ?? 0,
    format: 'group_stage',
    is_public: true,
  })

  const mutation = useMutation({
    mutationFn: (payload: TournamentCreatePayload) => tournamentApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['org-tournaments'] })
      onOpenChange(false)
      setForm({ name: '', sport_id: sports[0]?.id ?? 0, format: 'group_stage', is_public: true })
    },
  })

  function update<K extends keyof TournamentCreatePayload>(key: K, value: TournamentCreatePayload[K]) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    mutation.mutate({
      ...form,
      description: form.description || null,
      location: form.location || null,
      prize_pool: form.prize_pool || null,
      rules: form.rules || null,
    })
  }

  return (
    <Modal
      open={open}
      onOpenChange={(next) => {
        if (!mutation.isPending) onOpenChange(next)
      }}
      title="Create tournament"
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {mutation.isError && <FormAlert message={getErrorMessage(mutation.error)} />}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="t-name">Tournament name *</Label>
            <Input
              id="t-name"
              required
              minLength={2}
              maxLength={150}
              value={form.name}
              onChange={(e) => update('name', e.target.value)}
              placeholder="City Cup 2026"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="t-sport">Sport *</Label>
            <Select
              id="t-sport"
              value={form.sport_id}
              onChange={(e) => update('sport_id', Number(e.target.value))}
              className="w-full"
            >
              {sports.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="t-format">Format</Label>
            <Select
              id="t-format"
              value={form.format}
              onChange={(e) => update('format', e.target.value as TournamentCreatePayload['format'])}
              className="w-full"
            >
              <option value="group_stage">Group stage</option>
              <option value="knockout">Knockout</option>
              <option value="round_robin">Round robin</option>
              <option value="double_elimination">Double elimination</option>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="t-max-teams">Max teams</Label>
            <Input
              id="t-max-teams"
              type="number"
              min={2}
              value={form.max_teams ?? ''}
              onChange={(e) => update('max_teams', e.target.value ? Number(e.target.value) : null)}
              placeholder="Unlimited"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="t-location">Location</Label>
            <Input
              id="t-location"
              maxLength={255}
              value={form.location ?? ''}
              onChange={(e) => update('location', e.target.value)}
              placeholder="Hanoi National Stadium"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="t-prize">Prize pool</Label>
            <Input
              id="t-prize"
              maxLength={255}
              value={form.prize_pool ?? ''}
              onChange={(e) => update('prize_pool', e.target.value)}
              placeholder="e.g. 10,000,000 VND"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="t-reg-deadline">Registration deadline</Label>
            <Input
              id="t-reg-deadline"
              type="date"
              value={form.registration_deadline ?? ''}
              onChange={(e) => update('registration_deadline', e.target.value || null)}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="t-start">Start date</Label>
            <Input
              id="t-start"
              type="date"
              value={form.start_date ?? ''}
              onChange={(e) => update('start_date', e.target.value || null)}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="t-end">End date</Label>
            <Input
              id="t-end"
              type="date"
              value={form.end_date ?? ''}
              onChange={(e) => update('end_date', e.target.value || null)}
            />
          </div>

          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="t-desc">Description</Label>
            <Textarea
              id="t-desc"
              rows={3}
              value={form.description ?? ''}
              onChange={(e) => update('description', e.target.value)}
              placeholder="Tell participants about this tournament…"
            />
          </div>

          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="t-rules">Rules</Label>
            <Textarea
              id="t-rules"
              rows={4}
              value={form.rules ?? ''}
              onChange={(e) => update('rules', e.target.value)}
              placeholder="Detail the rules and regulations…"
            />
          </div>
        </div>

        <ModalActions>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending} disabled={!form.name || !form.sport_id}>
            Create tournament
          </Button>
        </ModalActions>
      </form>
    </Modal>
  )
}

// ─── Create group modal ───────────────────────────────────────────────────────

function CreateGroupModal({
  open,
  onOpenChange,
  tournament,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  tournament: TournamentDetailOut
}) {
  const qc = useQueryClient()
  const approvedTeams = tournament.registrations.filter((r) => r.registration_status === 'approved')

  const [form, setForm] = useState<GroupCreatePayload>({
    name: '',
    description: '',
    team_ids: [],
  })

  const mutation = useMutation({
    mutationFn: (payload: GroupCreatePayload) =>
      tournamentApi.createGroup(tournament.id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['org-tournament', tournament.id] })
      onOpenChange(false)
      setForm({ name: '', description: '', team_ids: [] })
    },
  })

  function toggleTeam(id: number) {
    setForm((f) => ({
      ...f,
      team_ids: f.team_ids.includes(id) ? f.team_ids.filter((x) => x !== id) : [...f.team_ids, id],
    }))
  }

  return (
    <Modal
      open={open}
      onOpenChange={(next) => {
        if (!mutation.isPending) onOpenChange(next)
      }}
      title="Create group"
      description="Assign approved teams to a new group."
    >
      <div className="space-y-4">
        {mutation.isError && <FormAlert message={getErrorMessage(mutation.error)} />}

        <div className="space-y-1.5">
          <Label htmlFor="g-name">Group name *</Label>
          <Input
            id="g-name"
            required
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            placeholder="Group A"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="g-desc">Description</Label>
          <Input
            id="g-desc"
            value={form.description ?? ''}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            placeholder="Optional"
          />
        </div>

        <div className="space-y-1.5">
          <Label>Approved teams</Label>
          {approvedTeams.length === 0 ? (
            <p className="text-sm text-muted-foreground">No approved teams yet.</p>
          ) : (
            <div className="border rounded-md divide-y max-h-52 overflow-y-auto">
              {approvedTeams.map((reg) => (
                <label
                  key={reg.id}
                  className="flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-muted/50"
                >
                  <input
                    type="checkbox"
                    checked={form.team_ids.includes(reg.team.id)}
                    onChange={() => toggleTeam(reg.team.id)}
                    className="size-4 accent-primary"
                  />
                  <span className="text-sm">{reg.team.name}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        <ModalActions>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button
            onClick={() => mutation.mutate(form)}
            loading={mutation.isPending}
            disabled={!form.name}
          >
            Create group
          </Button>
        </ModalActions>
      </div>
    </Modal>
  )
}

// ─── Registration decision row ────────────────────────────────────────────────

const REG_STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300',
  approved: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  rejected: 'bg-destructive/10 text-destructive',
}

function RegistrationDecisionRow({
  reg,
  tournamentId,
}: {
  reg: RegistrationOut
  tournamentId: number
}) {
  const qc = useQueryClient()
  const [showRejectInput, setShowRejectInput] = useState(false)
  const [reason, setReason] = useState('')

  const approveMutation = useMutation({
    mutationFn: () =>
      tournamentApi.decideRegistration(tournamentId, reg.team.id, { action: 'approve' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['org-tournament', tournamentId] }),
  })

  const rejectMutation = useMutation({
    mutationFn: () =>
      tournamentApi.decideRegistration(tournamentId, reg.team.id, {
        action: 'reject',
        rejection_reason: reason || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['org-tournament', tournamentId] })
      setShowRejectInput(false)
    },
  })

  return (
    <TableRow>
      <TableCell className="font-medium">{reg.team.name}</TableCell>
      <TableCell>
        <span
          className={`text-xs px-2 py-0.5 rounded-full font-medium ${REG_STATUS_COLORS[reg.registration_status] ?? ''}`}
        >
          {reg.registration_status}
        </span>
      </TableCell>
      <TableCell className="text-sm text-muted-foreground">
        {new Date(reg.registered_at).toLocaleDateString()}
      </TableCell>
      <TableCell>
        {reg.registration_status === 'pending' && (
          <div className="flex flex-col gap-2">
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                className="text-green-700 border-green-300 hover:bg-green-50"
                onClick={() => approveMutation.mutate()}
                loading={approveMutation.isPending}
              >
                <CheckCircle2 className="size-4 mr-1" />
                Approve
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="text-destructive border-destructive/30 hover:bg-destructive/10"
                onClick={() => setShowRejectInput((v) => !v)}
              >
                <XCircle className="size-4 mr-1" />
                Reject
              </Button>
            </div>
            {showRejectInput && (
              <div className="flex gap-2 items-center">
                <Input
                  className="h-7 text-xs"
                  placeholder="Reason (optional)"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => rejectMutation.mutate()}
                  loading={rejectMutation.isPending}
                >
                  Confirm
                </Button>
              </div>
            )}
          </div>
        )}
        {reg.rejection_reason && (
          <p className="text-xs text-muted-foreground">{reg.rejection_reason}</p>
        )}
      </TableCell>
    </TableRow>
  )
}

// ─── Expandable tournament row ────────────────────────────────────────────────

function TournamentManageRow({ t }: { t: TournamentOut }) {
  const [expanded, setExpanded] = useState(false)
  const [showCreateGroup, setShowCreateGroup] = useState(false)

  const detailQuery = useQuery({
    queryKey: ['org-tournament', t.id],
    queryFn: () => tournamentApi.get(t.id),
    enabled: expanded,
  })

  const detail = detailQuery.data
  const pendingCount =
    detail?.registrations.filter((r) => r.registration_status === 'pending').length ?? 0

  return (
    <div className="border rounded-lg overflow-hidden mb-3">
      <button
        type="button"
        className="w-full flex items-center justify-between gap-3 px-4 py-3 text-left hover:bg-muted/50 transition-colors"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="font-semibold truncate">{t.name}</span>
          <Badge variant="secondary" className="text-xs shrink-0">
            {t.sport.name}
          </Badge>
          <span className="text-xs text-muted-foreground shrink-0 capitalize">{t.status}</span>
          {pendingCount > 0 && (
            <Badge variant="destructive" className="text-xs shrink-0">
              {pendingCount} pending
            </Badge>
          )}
        </div>
        {expanded ? (
          <ChevronUp className="size-4 shrink-0" />
        ) : (
          <ChevronDown className="size-4 shrink-0" />
        )}
      </button>

      {expanded && (
        <div className="border-t p-4 space-y-4">
          {detailQuery.isPending ? (
            <Skeleton className="h-24 w-full" />
          ) : detailQuery.isError ? (
            <p className="text-destructive text-sm">Failed to load details.</p>
          ) : detail ? (
            <>
              {/* Registrations */}
              <div>
                <h3 className="font-medium mb-2">Registrations ({detail.registrations.length})</h3>
                {detail.registrations.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No registrations yet.</p>
                ) : (
                  <div className="border rounded-md overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Team</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Registered</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {detail.registrations.map((reg) => (
                          <RegistrationDecisionRow key={reg.id} reg={reg} tournamentId={t.id} />
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>

              {/* Groups */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">Groups ({detail.groups.length})</h3>
                  <Button size="sm" variant="outline" onClick={() => setShowCreateGroup(true)}>
                    <Plus className="size-4 mr-1" />
                    New group
                  </Button>
                </div>
                {detail.groups.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No groups yet.</p>
                ) : (
                  <div className="space-y-2">
                    {detail.groups.map((g) => (
                      <div key={g.id} className="border rounded-md p-3">
                        <p className="font-medium text-sm">{g.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {g.teams.length} team{g.teams.length !== 1 ? 's' : ''}:{' '}
                          {g.teams.map((gt) => gt.team.name).join(', ')}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <CreateGroupModal
                open={showCreateGroup}
                onOpenChange={setShowCreateGroup}
                tournament={detail}
              />

              {/* Link to Schedule & Score management */}
              <div className="pt-2 border-t flex justify-end">
                <Button asChild size="sm" variant="outline">
                  <Link to={`/organizer/tournaments/${t.id}/manage`}>
                    <CalendarClock className="size-4 mr-1" />
                    Manage Schedule &amp; Scores
                  </Link>
                </Button>
              </div>
            </>
          ) : null}
        </div>
      )}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

const PAGE_SIZE = 20

export function OrganizerTournamentsPage() {
  const [showCreate, setShowCreate] = useState(false)
  const { user } = useAuth()

  const sportsQuery = useQuery<{ items: Sport[] }>({
    queryKey: ['sports'],
    queryFn: () => api.get('/sports').then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  })

  const tQuery = useQuery({
    queryKey: ['org-tournaments'],
    queryFn: () => tournamentApi.list({ page: 1, page_size: PAGE_SIZE }),
  })

  // Filter to current user's tournaments client-side
  const myTournaments = (tQuery.data?.items ?? []).filter((t) => t.organizer.id === user?.id)
  const sports = sportsQuery.data?.items ?? []

  return (
    <>
      <PageHeader
        title="My tournaments"
        description="Create and manage your tournaments."
        actions={
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="size-4 mr-1" />
            New tournament
          </Button>
        }
      />

      {tQuery.isPending ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full rounded-lg" />
          ))}
        </div>
      ) : myTournaments.length === 0 ? (
        <EmptyState
          icon={ClipboardList}
          title="No tournaments yet"
          description="Create your first tournament to get started."
          action={
            <Button onClick={() => setShowCreate(true)}>
              <Plus className="size-4 mr-1" />
              New tournament
            </Button>
          }
        />
      ) : (
        <>
          {myTournaments.map((t) => (
            <TournamentManageRow key={t.id} t={t} />
          ))}
        </>
      )}

      <CreateTournamentModal
        open={showCreate}
        onOpenChange={setShowCreate}
        sports={sports}
      />
    </>
  )
}
