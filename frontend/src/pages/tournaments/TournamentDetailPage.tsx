/** Tournament detail page — rules, registered teams, group standings, register-team modal. */
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Trophy } from 'lucide-react'
import { getErrorMessage } from '@/api/client'
import {
  teamApi,
  tournamentApi,
  type RegistrationOut,
  type TournamentDetailOut,
  type TournamentStatus,
} from '@/api/sportarena'
import { EmptyState } from '@/components/shared/EmptyState'
import { FormAlert } from '@/components/shared/FormAlert'
import { Modal, ModalActions } from '@/components/shared/Modal'
import { PageHeader } from '@/components/shared/PageHeader'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useAuth } from '@/hooks/use-auth'

// ─── Helpers ──────────────────────────────────────────────────────────────────

const STATUS_COLORS: Record<TournamentStatus, string> = {
  draft: 'bg-muted text-muted-foreground',
  registration: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  ongoing: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  completed: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
  cancelled: 'bg-destructive/10 text-destructive',
}

const REG_STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300',
  approved: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  rejected: 'bg-destructive/10 text-destructive',
}

// ─── Register team modal ──────────────────────────────────────────────────────

function RegisterTeamModal({
  open,
  onOpenChange,
  tournamentId,
  tournament,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  tournamentId: number
  tournament: TournamentDetailOut
}) {
  const qc = useQueryClient()
  const { user } = useAuth()

  const myTeamsQuery = useQuery({
    queryKey: ['teams', 'mine'],
    queryFn: () => teamApi.mine(),
    enabled: open && !!user,
  })

  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null)

  const mutation = useMutation({
    mutationFn: () => tournamentApi.registerTeam(tournamentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tournament', tournamentId] })
      onOpenChange(false)
    },
  })

  // Filter: show only teams the user captains
  const captainedTeams = (myTeamsQuery.data ?? []).filter(
    (t) => t.captain.id === user?.id && t.sport.id === tournament.sport.id,
  )

  // Check if already registered
  const alreadyRegistered = tournament.registrations.some(
    (r) => captainedTeams.some((t) => t.id === r.team.id),
  )

  return (
    <Modal
      open={open}
      onOpenChange={(next) => {
        if (!mutation.isPending) onOpenChange(next)
      }}
      title="Register a team"
      description={`Register one of your ${tournament.sport.name} teams for ${tournament.name}.`}
    >
      <div className="space-y-4">
        {mutation.isError && <FormAlert message={getErrorMessage(mutation.error)} />}
        {alreadyRegistered && (
          <FormAlert message="One of your teams is already registered for this tournament." />
        )}

        {myTeamsQuery.isPending ? (
          <Skeleton className="h-9 w-full" />
        ) : captainedTeams.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            You are not the captain of any {tournament.sport.name} team. Create a team first.
          </p>
        ) : (
          <div className="space-y-1.5">
            <label className="text-sm font-medium" htmlFor="reg-team">
              Select your team
            </label>
            <Select
              id="reg-team"
              value={selectedTeamId?.toString() ?? ''}
              onChange={(e) => setSelectedTeamId(e.target.value ? Number(e.target.value) : null)}
              className="w-full"
            >
              <option value="">Choose a team…</option>
              {captainedTeams.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.member_count} members)
                </option>
              ))}
            </Select>
          </div>
        )}

        <ModalActions>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            loading={mutation.isPending}
            disabled={!selectedTeamId || alreadyRegistered || captainedTeams.length === 0}
          >
            Register
          </Button>
        </ModalActions>
      </div>
    </Modal>
  )
}

// ─── Registration row ─────────────────────────────────────────────────────────

function RegistrationRow({ reg }: { reg: RegistrationOut }) {
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
      {reg.rejection_reason && (
        <TableCell className="text-sm text-destructive">{reg.rejection_reason}</TableCell>
      )}
    </TableRow>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function TournamentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const tournamentId = Number(id)
  const { user, hasRole } = useAuth()
  const [showRegister, setShowRegister] = useState(false)

  const tQuery = useQuery({
    queryKey: ['tournament', tournamentId],
    queryFn: () => tournamentApi.get(tournamentId),
    enabled: !isNaN(tournamentId),
  })

  const t = tQuery.data

  if (tQuery.isPending) {
    return (
      <>
        <Skeleton className="h-9 w-1/2 mb-2" />
        <Skeleton className="h-4 w-1/4 mb-8" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))}
        </div>
      </>
    )
  }

  if (tQuery.isError || !t) {
    return (
      <EmptyState icon={Trophy} title="Tournament not found" description="This tournament does not exist." />
    )
  }

  const canRegister = user && t.status === 'registration' && !hasRole('organizer', 'admin')

  return (
    <>
      <PageHeader
        title={t.name}
        description={[t.sport.name, t.location].filter(Boolean).join(' · ') || undefined}
        actions={
          canRegister ? (
            <Button onClick={() => setShowRegister(true)}>Register my team</Button>
          ) : undefined
        }
      />

      {/* Meta cards */}
      <div className="grid gap-4 mb-6 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: 'Status', value: <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[t.status]}`}>{t.status}</span> },
          { label: 'Format', value: t.format.replace(/_/g, ' ') },
          { label: 'Teams', value: `${t.registered_team_count}${t.max_teams ? ` / ${t.max_teams}` : ''}` },
          { label: 'Prize pool', value: t.prize_pool ?? '—' },
        ].map(({ label, value }) => (
          <Card key={label} className="p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground mb-1">{label}</p>
            <p className="font-semibold">{value}</p>
          </Card>
        ))}
      </div>

      {/* Dates */}
      {(t.start_date || t.end_date || t.registration_deadline) && (
        <Card className="p-4 mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {t.registration_deadline && (
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">Registration deadline</p>
                <p className="font-medium">{t.registration_deadline}</p>
              </div>
            )}
            {t.start_date && (
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">Start date</p>
                <p className="font-medium">{t.start_date}</p>
              </div>
            )}
            {t.end_date && (
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground mb-1">End date</p>
                <p className="font-medium">{t.end_date}</p>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Description */}
      {t.description && (
        <Card className="p-4 mb-6">
          <p className="text-sm font-medium mb-2 uppercase tracking-wide text-muted-foreground">About</p>
          <p className="text-sm whitespace-pre-wrap">{t.description}</p>
        </Card>
      )}

      {/* Rules */}
      {t.rules && (
        <Card className="p-4 mb-6">
          <p className="text-sm font-medium mb-2 uppercase tracking-wide text-muted-foreground">Rules</p>
          <p className="text-sm whitespace-pre-wrap">{t.rules}</p>
        </Card>
      )}

      {/* Registered teams */}
      <Card className="mb-6">
        <div className="p-4 border-b">
          <h2 className="font-semibold">Registered Teams ({t.registrations.length})</h2>
        </div>
        {t.registrations.length === 0 ? (
          <EmptyState icon={Trophy} title="No registrations yet" />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Team</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Registered</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {t.registrations.map((reg) => (
                <RegistrationRow key={reg.id} reg={reg} />
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      {/* Groups */}
      {t.groups.length > 0 && (
        <div className="space-y-4 mb-6">
          <h2 className="text-lg font-semibold">Group Standings</h2>
          {t.groups.map((g) => (
            <Card key={g.id}>
              <div className="p-4 border-b font-semibold">{g.name}</div>
              {g.description && (
                <p className="px-4 py-2 text-sm text-muted-foreground">{g.description}</p>
              )}
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">Seed</TableHead>
                    <TableHead>Team</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {g.teams.map((gt) => (
                    <TableRow key={gt.id}>
                      <TableCell className="text-muted-foreground">{gt.seeding ?? '—'}</TableCell>
                      <TableCell className="font-medium">{gt.team.name}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          ))}
        </div>
      )}

      {t && (
        <RegisterTeamModal
          open={showRegister}
          onOpenChange={setShowRegister}
          tournamentId={tournamentId}
          tournament={t}
        />
      )}
    </>
  )
}
