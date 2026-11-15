import { Eye, EyeOff, MapPin, Pencil, Plus, Ruler, Trash2, Trophy } from 'lucide-react'
import { useState } from 'react'
import { useDeleteProfile, useMyProfiles } from '@/api/profiles'
import { useSports } from '@/api/sports'
import type { PlayerProfile } from '@/api/types'
import { getErrorMessage } from '@/api/client'
import { EmptyState } from '@/components/shared/EmptyState'
import { ConfirmDialog } from '@/components/shared/Modal'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/hooks/use-auth'
import { toast } from '@/lib/toast'
import { ProfileFormModal } from './ProfileFormModal'

const LEVEL_VARIANT = { beginner: 'secondary', intermediate: 'success', advanced: 'warning', pro: 'highlight' } as const

export function PlayerProfilesTab() {
  const { hasRole } = useAuth()
  const isPlayer = hasRole('player')

  const profiles = useMyProfiles(isPlayer)
  const sports = useSports()
  const deleteProfile = useDeleteProfile()

  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<PlayerProfile | null>(null)
  const [deleting, setDeleting] = useState<PlayerProfile | null>(null)

  if (!isPlayer) {
    return (
      <Card>
        <EmptyState
          icon={Trophy}
          title="Player profiles are for players"
          description="Your account doesn't have the player role. Ask an admin to add it if you'd like to create sport profiles."
        />
      </Card>
    )
  }

  const takenSportIds = new Set((profiles.data ?? []).map((profile) => profile.sport_id))
  const available = (sports.data ?? []).filter((sport) => !takenSportIds.has(sport.id))

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">One profile per sport. Others can find you through these when searching for players.</p>
        <Button onClick={() => setCreating(true)} disabled={sports.isPending || available.length === 0}>
          <Plus aria-hidden />
          Add sport profile
        </Button>
      </div>

      {profiles.isPending ? (
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-44" />
          <Skeleton className="h-44" />
        </div>
      ) : profiles.isError ? (
        <Card>
          <EmptyState
            icon={Trophy}
            title="Could not load your profiles"
            description={getErrorMessage(profiles.error)}
            action={<Button variant="outline" onClick={() => void profiles.refetch()}>Try again</Button>}
          />
        </Card>
      ) : profiles.data.length === 0 ? (
        <Card>
          <EmptyState
            icon={Trophy}
            title="No sport profiles yet"
            description="Create your first profile to appear in player search and set your weekly availability."
            action={<Button onClick={() => setCreating(true)}>Create a profile</Button>}
          />
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {profiles.data.map((profile) => (
            <Card key={profile.id}>
              <CardHeader className="flex-row items-start justify-between gap-2 space-y-0">
                <div>
                  <CardTitle className="text-2xl">{profile.sport.name}</CardTitle>
                  <div className="mt-2 flex flex-wrap items-center gap-1.5">
                    <Badge variant={LEVEL_VARIANT[profile.skill_level]} className="capitalize">
                      {profile.skill_level}
                    </Badge>
                    {profile.position && <Badge variant="outline">{profile.position}</Badge>}
                    <Badge variant={profile.is_visible ? 'success' : 'secondary'}>
                      {profile.is_visible ? <Eye className="size-3" aria-hidden /> : <EyeOff className="size-3" aria-hidden />}
                      {profile.is_visible ? 'Visible' : 'Hidden'}
                    </Badge>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button variant="ghost" size="icon" onClick={() => setEditing(profile)} aria-label={`Edit ${profile.sport.name} profile`}>
                    <Pencil aria-hidden />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-destructive hover:text-destructive"
                    onClick={() => setDeleting(profile)}
                    aria-label={`Delete ${profile.sport.name} profile`}
                  >
                    <Trash2 aria-hidden />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p className="flex flex-wrap gap-x-4 gap-y-1 text-muted-foreground">
                  {profile.city && (
                    <span className="inline-flex items-center gap-1">
                      <MapPin className="size-3.5" aria-hidden />
                      {profile.city}
                    </span>
                  )}
                  {(profile.height_cm || profile.weight_kg) && (
                    <span className="inline-flex items-center gap-1">
                      <Ruler className="size-3.5" aria-hidden />
                      {[profile.height_cm && `${profile.height_cm} cm`, profile.weight_kg && `${profile.weight_kg} kg`].filter(Boolean).join(' · ')}
                    </span>
                  )}
                  {profile.preferred_side && <span className="capitalize">Prefers {profile.preferred_side}</span>}
                </p>
                {profile.bio ? <p className="line-clamp-3">{profile.bio}</p> : <p className="text-muted-foreground">No bio yet.</p>}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <ProfileFormModal open={creating} onOpenChange={setCreating} sports={available} />
      {editing && (
        <ProfileFormModal
          open
          onOpenChange={(open) => !open && setEditing(null)}
          profile={editing}
          sports={sports.data ?? [editing.sport]}
        />
      )}
      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        title={`Delete ${deleting?.sport.name ?? ''} profile?`}
        description="Its weekly availability will be deleted too. This cannot be undone."
        confirmLabel="Delete profile"
        destructive
        loading={deleteProfile.isPending}
        onConfirm={() => {
          if (!deleting) return
          deleteProfile.mutate(deleting.id, {
            onSuccess: () => {
              toast.success('Profile deleted')
              setDeleting(null)
            },
          })
        }}
      />
    </div>
  )
}
