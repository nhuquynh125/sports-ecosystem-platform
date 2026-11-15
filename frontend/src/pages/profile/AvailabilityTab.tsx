import { CalendarClock, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useMyProfiles, useSlots } from '@/api/profiles'
import type { AvailabilitySlot } from '@/api/types'
import { getErrorMessage } from '@/api/client'
import { EmptyState } from '@/components/shared/EmptyState'
import { ScheduleGrid, type ScheduleSlot } from '@/components/shared/ScheduleGrid'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/hooks/use-auth'
import { minutesToTime, timeToMinutes } from '@/lib/time'
import { SlotModal, type SlotDraft } from './SlotModal'

export function AvailabilityTab({ onGoToProfiles }: { onGoToProfiles: () => void }) {
  const { hasRole } = useAuth()
  const isPlayer = hasRole('player')
  const profiles = useMyProfiles(isPlayer)

  const [chosenId, setChosenId] = useState<number | null>(null)
  const [draft, setDraft] = useState<SlotDraft | null>(null)
  const [editing, setEditing] = useState<AvailabilitySlot | null>(null)

  const list = profiles.data ?? []
  const profile = list.find((p) => p.id === chosenId) ?? list[0] ?? null
  const slots = useSlots(profile?.id ?? null)

  const gridSlots = useMemo<ScheduleSlot[]>(
    () =>
      (slots.data ?? []).map((slot) => ({
        id: slot.id,
        day: slot.day_of_week,
        start: slot.start_time,
        end: slot.end_time,
      })),
    [slots.data],
  )

  if (!isPlayer) {
    return (
      <Card>
        <EmptyState icon={CalendarClock} title="Availability is for players" description="Add the player role to your account to set a weekly schedule." />
      </Card>
    )
  }

  if (profiles.isPending) return <Skeleton className="h-96" />

  if (profiles.isError) {
    return (
      <Card>
        <EmptyState
          icon={CalendarClock}
          title="Could not load your profiles"
          description={getErrorMessage(profiles.error)}
          action={<Button variant="outline" onClick={() => void profiles.refetch()}>Try again</Button>}
        />
      </Card>
    )
  }

  if (!profile) {
    return (
      <Card>
        <EmptyState
          icon={CalendarClock}
          title="Create a sport profile first"
          description="Availability belongs to a sport profile, so others can find you for that sport at the right time."
          action={<Button onClick={onGoToProfiles}>Go to player profiles</Button>}
        />
      </Card>
    )
  }

  function openNew(day = 1, start = '18:00') {
    const end = minutesToTime(Math.min(timeToMinutes(start) + 120, 23 * 60 + 59))
    setDraft({ day, start, end })
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex flex-wrap items-end gap-3">
          {list.length > 1 && (
            <div className="space-y-1.5">
              <label htmlFor="avail-profile" className="text-sm font-medium">
                Sport profile
              </label>
              <Select id="avail-profile" value={profile.id} onChange={(event) => setChosenId(Number(event.target.value))} className="min-w-[180px]">
                {list.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.sport.name}
                  </option>
                ))}
              </Select>
            </div>
          )}
          <p className="pb-2 text-sm text-muted-foreground">
            Click an empty hour to add a window, or a block to edit it.
            {slots.data && ` ${slots.data.length} window${slots.data.length === 1 ? '' : 's'} for ${profile.sport.name}.`}
          </p>
        </div>
        <Button onClick={() => openNew()}>
          <Plus aria-hidden />
          Add window
        </Button>
      </div>

      {slots.isPending ? (
        <Skeleton className="h-96" />
      ) : slots.isError ? (
        <Card>
          <EmptyState
            icon={CalendarClock}
            title="Could not load availability"
            description={getErrorMessage(slots.error)}
            action={<Button variant="outline" onClick={() => void slots.refetch()}>Try again</Button>}
          />
        </Card>
      ) : (
        <ScheduleGrid
          slots={gridSlots}
          onCellClick={(day, time) => openNew(day, time)}
          onSlotClick={(slot) => setEditing(slots.data?.find((s) => s.id === slot.id) ?? null)}
        />
      )}

      {draft && (
        <SlotModal profileId={profile.id} open onOpenChange={(open) => !open && setDraft(null)} draft={draft} />
      )}
      {editing && (
        <SlotModal profileId={profile.id} open onOpenChange={(open) => !open && setEditing(null)} slot={editing} />
      )}
    </div>
  )
}
