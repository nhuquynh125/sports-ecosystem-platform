/** Team detail page — roster view, add/remove members (captain only). */
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Trash2, UserPlus, Users } from 'lucide-react'
import { getErrorMessage } from '@/api/client'
import { teamApi, type TeamMember } from '@/api/sportarena'
import { EmptyState } from '@/components/shared/EmptyState'
import { FormAlert } from '@/components/shared/FormAlert'
import { Modal, ModalActions } from '@/components/shared/Modal'
import { PageHeader } from '@/components/shared/PageHeader'
import { UserAvatar } from '@/components/shared/UserAvatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/hooks/use-auth'

// ─── Add member modal ─────────────────────────────────────────────────────────

function AddMemberModal({
  open,
  onOpenChange,
  teamId,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  teamId: number
}) {
  const qc = useQueryClient()
  const [userId, setUserId] = useState('')

  const mutation = useMutation({
    mutationFn: () => teamApi.addMember(teamId, Number(userId)),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['team', teamId] })
      onOpenChange(false)
      setUserId('')
    },
  })

  return (
    <Modal
      open={open}
      onOpenChange={(next) => {
        if (!mutation.isPending) onOpenChange(next)
      }}
      title="Add team member"
      description="Enter the user ID of the player to add."
    >
      <div className="space-y-4">
        {mutation.isError && <FormAlert message={getErrorMessage(mutation.error)} />}

        <div className="space-y-1.5">
          <Label htmlFor="add-user-id">User ID *</Label>
          <Input
            id="add-user-id"
            type="number"
            min={1}
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="e.g. 42"
          />
        </div>

        <ModalActions>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            loading={mutation.isPending}
            disabled={!userId || Number(userId) < 1}
          >
            <UserPlus className="size-4 mr-1" />
            Add member
          </Button>
        </ModalActions>
      </div>
    </Modal>
  )
}

// ─── Member row ───────────────────────────────────────────────────────────────

function MemberRow({
  member,
  isCaptain,
  canRemove,
  teamId,
}: {
  member: TeamMember
  isCaptain: boolean
  canRemove: boolean
  teamId: number
}) {
  const qc = useQueryClient()

  const removeMutation = useMutation({
    mutationFn: () => teamApi.removeMember(teamId, member.user_id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['team', teamId] })
    },
  })

  return (
    <div className="flex items-center gap-3 py-3 border-b last:border-0">
      <UserAvatar
        name={member.full_name}
        src={member.avatar_url}
        className="size-9 shrink-0"
      />
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm truncate">{member.full_name}</p>
        <p className="text-xs text-muted-foreground">@{member.username}</p>
      </div>
      <Badge variant={member.role === 'captain' ? 'default' : 'secondary'} className="text-xs">
        {member.role}
      </Badge>
      {canRemove && !isCaptain && (
        <Button
          variant="ghost"
          size="icon"
          className="size-8 text-destructive hover:text-destructive"
          onClick={() => removeMutation.mutate()}
          loading={removeMutation.isPending}
          aria-label={`Remove ${member.full_name}`}
        >
          <Trash2 className="size-4" />
        </Button>
      )}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function TeamDetailPage() {
  const { id } = useParams<{ id: string }>()
  const teamId = Number(id)
  const { user } = useAuth()
  const [showAddMember, setShowAddMember] = useState(false)

  const teamQuery = useQuery({
    queryKey: ['team', teamId],
    queryFn: () => teamApi.get(teamId),
    enabled: !isNaN(teamId),
  })

  const team = teamQuery.data
  const isCaptain = !!user && !!team && team.captain.id === user.id

  if (teamQuery.isPending) {
    return (
      <>
        <Skeleton className="h-9 w-1/3 mb-2" />
        <Skeleton className="h-4 w-1/4 mb-8" />
        <Card className="p-4 space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="size-9 rounded-full" />
              <div className="flex-1 space-y-1">
                <Skeleton className="h-4 w-1/3" />
                <Skeleton className="h-3 w-1/4" />
              </div>
            </div>
          ))}
        </Card>
      </>
    )
  }

  if (teamQuery.isError || !team) {
    return (
      <EmptyState
        icon={Users}
        title="Team not found"
        description="This team does not exist or has been removed."
      />
    )
  }

  return (
    <>
      <PageHeader
        title={team.name}
        description={
          [team.sport.name, team.city].filter(Boolean).join(' · ') || undefined
        }
        actions={
          isCaptain ? (
            <Button onClick={() => setShowAddMember(true)}>
              <UserPlus className="size-4 mr-1" />
              Add member
            </Button>
          ) : undefined
        }
      />

      {/* Info */}
      <div className="grid gap-4 mb-6 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: 'Sport', value: team.sport.name },
          { label: 'City', value: team.city ?? '—' },
          { label: 'Captain', value: team.captain.full_name },
          { label: 'Members', value: String(team.member_count) },
        ].map(({ label, value }) => (
          <Card key={label} className="p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground mb-1">{label}</p>
            <p className="font-semibold">{value}</p>
          </Card>
        ))}
      </div>

      {team.description && (
        <Card className="p-4 mb-6">
          <p className="text-sm font-medium mb-1 text-muted-foreground uppercase tracking-wide">About</p>
          <p className="text-sm whitespace-pre-wrap">{team.description}</p>
        </Card>
      )}

      {/* Roster */}
      <Card className="p-4">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Users className="size-5" />
          Roster
        </h2>
        {team.members.length === 0 ? (
          <EmptyState icon={Users} title="No members yet" />
        ) : (
          <div>
            {team.members.map((m) => (
              <MemberRow
                key={m.id}
                member={m}
                isCaptain={m.user_id === team.captain.id}
                canRemove={isCaptain}
                teamId={teamId}
              />
            ))}
          </div>
        )}
      </Card>

      <AddMemberModal open={showAddMember} onOpenChange={setShowAddMember} teamId={teamId} />
    </>
  )
}
