/** Teams list page + create-team modal. */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Users } from 'lucide-react'
import { api } from '@/api/client'
import { teamApi, type TeamCreatePayload, type TeamOut } from '@/api/sportarena'
import type { Sport } from '@/api/types'
import { EmptyState } from '@/components/shared/EmptyState'
import { FormAlert } from '@/components/shared/FormAlert'
import { Modal, ModalActions } from '@/components/shared/Modal'
import { PageHeader } from '@/components/shared/PageHeader'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { getErrorMessage } from '@/api/client'

// ─── Create-team modal ────────────────────────────────────────────────────────

function CreateTeamModal({
  open,
  onOpenChange,
  sports,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  sports: Sport[]
}) {
  const qc = useQueryClient()
  const [form, setForm] = useState<TeamCreatePayload>({
    name: '',
    sport_id: sports[0]?.id ?? 0,
    description: '',
    city: '',
  })

  const mutation = useMutation({
    mutationFn: (payload: TeamCreatePayload) => teamApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['teams'] })
      qc.invalidateQueries({ queryKey: ['teams', 'mine'] })
      onOpenChange(false)
      setForm({ name: '', sport_id: sports[0]?.id ?? 0, description: '', city: '' })
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    mutation.mutate({ ...form, description: form.description || null, city: form.city || null })
  }

  return (
    <Modal
      open={open}
      onOpenChange={(next) => {
        if (!mutation.isPending) onOpenChange(next)
      }}
      title="Create a team"
      description="You will automatically become the captain."
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {mutation.isError && <FormAlert message={getErrorMessage(mutation.error)} />}

        <div className="space-y-1.5">
          <Label htmlFor="team-name">Team name *</Label>
          <Input
            id="team-name"
            required
            minLength={2}
            maxLength={100}
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            placeholder="Eagles FC"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="team-sport">Sport *</Label>
          <Select
            id="team-sport"
            value={form.sport_id}
            onChange={(e) => setForm((f) => ({ ...f, sport_id: Number(e.target.value) }))}
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
          <Label htmlFor="team-city">City</Label>
          <Input
            id="team-city"
            maxLength={100}
            value={form.city ?? ''}
            onChange={(e) => setForm((f) => ({ ...f, city: e.target.value }))}
            placeholder="Hanoi"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="team-desc">Description</Label>
          <Textarea
            id="team-desc"
            rows={3}
            maxLength={2000}
            value={form.description ?? ''}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            placeholder="Tell people about your team…"
          />
        </div>

        <ModalActions>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending} disabled={!form.name || !form.sport_id}>
            Create team
          </Button>
        </ModalActions>
      </form>
    </Modal>
  )
}

// ─── Team card ────────────────────────────────────────────────────────────────

function TeamCard({ team, onClick }: { team: TeamOut; onClick: () => void }) {
  return (
    <Card
      className="p-4 space-y-2 cursor-pointer hover:shadow-md transition-shadow"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-base leading-tight">{team.name}</h3>
        <Badge variant="secondary" className="text-xs shrink-0">
          {team.sport.name}
        </Badge>
      </div>
      {team.city && <p className="text-sm text-muted-foreground">{team.city}</p>}
      {team.description && (
        <p className="text-sm text-muted-foreground line-clamp-2">{team.description}</p>
      )}
      <div className="flex items-center gap-1 text-xs text-muted-foreground">
        <Users className="size-3.5" />
        {team.member_count} member{team.member_count !== 1 ? 's' : ''}
      </div>
    </Card>
  )
}

function TeamCardSkeleton() {
  return (
    <Card className="p-4 space-y-3">
      <Skeleton className="h-5 w-2/3" />
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-3 w-20" />
    </Card>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

const PAGE_SIZE = 12

export function TeamsPage() {
  const navigate = useNavigate()
  const [showCreate, setShowCreate] = useState(false)
  const [sportId, setSportId] = useState<number | undefined>()
  const [page, setPage] = useState(1)

  const sportsQuery = useQuery<{ items: Sport[] }>({
    queryKey: ['sports'],
    queryFn: () => api.get('/sports').then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  })

  const params = { sport_id: sportId, page, page_size: PAGE_SIZE }
  const teamsQuery = useQuery({
    queryKey: ['teams', params],
    queryFn: () => teamApi.list(params),
  })

  const sports = sportsQuery.data?.items ?? []
  const teams = teamsQuery.data?.items ?? []
  const total = teamsQuery.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <>
      <PageHeader
        title="Teams"
        description="Browse all teams or create your own."
        actions={
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="size-4 mr-1" />
            New team
          </Button>
        }
      />

      {/* Filter */}
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
          {sports.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </Select>
      </div>

      {/* Grid */}
      {teamsQuery.isPending ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <TeamCardSkeleton key={i} />
          ))}
        </div>
      ) : teamsQuery.isError ? (
        <div className="py-12 text-center text-destructive text-sm">
          Failed to load teams. Please try again.
        </div>
      ) : teams.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No teams yet"
          description="Be the first to create a team!"
          action={
            <Button onClick={() => setShowCreate(true)}>
              <Plus className="size-4 mr-1" />
              New team
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {teams.map((t) => (
            <TeamCard key={t.id} team={t} onClick={() => navigate(`/teams/${t.id}`)} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!teamsQuery.isPending && total > PAGE_SIZE && (
        <div className="flex items-center justify-center gap-4 mt-6">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Prev
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Next
          </Button>
        </div>
      )}

      <CreateTeamModal
        open={showCreate}
        onOpenChange={setShowCreate}
        sports={sports}
      />
    </>
  )
}
