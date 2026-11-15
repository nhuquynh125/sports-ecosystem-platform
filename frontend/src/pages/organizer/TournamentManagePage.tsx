/**
 * Organizer tournament management page — /organizer/tournaments/:id/manage
 * Features:
 *  - Generate Schedule panel (court IDs, start/end date, time slots, min matches per team)
 *  - Matches list with "Record Result" modal per match
 */
import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, CalendarClock, ClipboardList, Plus, Trash2 } from 'lucide-react'
import { getErrorMessage } from '@/api/client'
import {
  tournamentApi,
  type MatchEventIn,
  type MatchOut,
  type MatchResultSubmit,
  type ScheduleGenerateRequest,
} from '@/api/sportarena'
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
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

// ─── Match status badge ───────────────────────────────────────────────────────

const MATCH_STATUS_COLORS: Record<string, string> = {
  scheduled: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  cancelled: 'bg-destructive/10 text-destructive',
}

// ─── Generate Schedule Panel ──────────────────────────────────────────────────

function GenerateSchedulePanel({ tournamentId }: { tournamentId: number }) {
  const qc = useQueryClient()

  const [courtInput, setCourtInput] = useState('')
  const [courtIds, setCourtIds] = useState<number[]>([])
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [slotInput, setSlotInput] = useState('')
  const [timeSlots, setTimeSlots] = useState<string[]>(['08:00', '10:00', '14:00'])
  const [minMatches, setMinMatches] = useState(3)

  const mutation = useMutation({
    mutationFn: (payload: ScheduleGenerateRequest) =>
      tournamentApi.generateSchedule(tournamentId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['org-matches', tournamentId] })
    },
  })

  function addCourt() {
    const id = parseInt(courtInput.trim(), 10)
    if (!isNaN(id) && id > 0 && !courtIds.includes(id)) {
      setCourtIds((prev) => [...prev, id])
    }
    setCourtInput('')
  }

  function removeCourt(id: number) {
    setCourtIds((prev) => prev.filter((c) => c !== id))
  }

  function addSlot() {
    const slot = slotInput.trim()
    if (slot && !timeSlots.includes(slot)) {
      setTimeSlots((prev) => [...prev, slot])
    }
    setSlotInput('')
  }

  function removeSlot(slot: string) {
    setTimeSlots((prev) => prev.filter((s) => s !== slot))
  }

  function handleGenerate() {
    mutation.mutate({
      court_ids: courtIds,
      start_date: startDate,
      end_date: endDate,
      daily_time_slots: timeSlots,
      min_matches_per_team: minMatches,
    })
  }

  return (
    <Card className="p-5 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <CalendarClock className="size-5 text-primary" />
        <h2 className="font-semibold text-lg">Generate Schedule</h2>
      </div>

      {mutation.isSuccess && (
        <div className="mb-4 rounded-md bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-3 text-sm text-green-800 dark:text-green-300">
          ✓ Schedule generated: <strong>{mutation.data?.matches_created}</strong> matches created
          {mutation.data?.conflicts_skipped ? (
            <>, <strong>{mutation.data.conflicts_skipped}</strong> conflicts skipped</>
          ) : null}
          .
        </div>
      )}
      {mutation.isError && <FormAlert message={getErrorMessage(mutation.error)} />}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Court IDs */}
        <div className="space-y-1.5 sm:col-span-2">
          <Label>Court IDs</Label>
          <div className="flex gap-2">
            <Input
              placeholder="Enter a court ID…"
              value={courtInput}
              onChange={(e) => setCourtInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addCourt())}
              type="number"
              min={1}
            />
            <Button variant="outline" onClick={addCourt}>
              <Plus className="size-4" />
              Add
            </Button>
          </div>
          {courtIds.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {courtIds.map((id) => (
                <span
                  key={id}
                  className="inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-secondary text-secondary-foreground"
                >
                  Court {id}
                  <button
                    type="button"
                    onClick={() => removeCourt(id)}
                    className="text-muted-foreground hover:text-destructive"
                    aria-label={`Remove court ${id}`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Start date */}
        <div className="space-y-1.5">
          <Label htmlFor="sched-start">Start date *</Label>
          <Input
            id="sched-start"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>

        {/* End date */}
        <div className="space-y-1.5">
          <Label htmlFor="sched-end">End date *</Label>
          <Input
            id="sched-end"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>

        {/* Min matches per team */}
        <div className="space-y-1.5">
          <Label htmlFor="sched-min">Min matches per team</Label>
          <Input
            id="sched-min"
            type="number"
            min={1}
            max={20}
            value={minMatches}
            onChange={(e) => setMinMatches(Number(e.target.value))}
          />
        </div>

        {/* Time slots */}
        <div className="space-y-1.5">
          <Label>Daily time slots</Label>
          <div className="flex gap-2">
            <Input
              placeholder="HH:MM"
              value={slotInput}
              onChange={(e) => setSlotInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSlot())}
              type="time"
            />
            <Button variant="outline" onClick={addSlot}>
              <Plus className="size-4" />
              Add
            </Button>
          </div>
          {timeSlots.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {timeSlots.map((slot) => (
                <span
                  key={slot}
                  className="inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-secondary text-secondary-foreground"
                >
                  {slot}
                  <button
                    type="button"
                    onClick={() => removeSlot(slot)}
                    className="text-muted-foreground hover:text-destructive"
                    aria-label={`Remove slot ${slot}`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="mt-5 flex justify-end">
        <Button
          onClick={handleGenerate}
          loading={mutation.isPending}
          disabled={
            courtIds.length === 0 ||
            !startDate ||
            !endDate ||
            timeSlots.length === 0 ||
            mutation.isPending
          }
        >
          <CalendarClock className="size-4" />
          Generate schedule
        </Button>
      </div>
    </Card>
  )
}

// ─── Record Match Result Modal ────────────────────────────────────────────────

type EventType = MatchEventIn['event_type']

const EVENT_TYPE_LABELS: Record<EventType, string> = {
  goal: '⚽ Goal',
  assist: '🅰️ Assist',
  yellow_card: '🟡 Yellow card',
  red_card: '🔴 Red card',
  own_goal: '😬 Own goal',
}

function RecordResultModal({
  open,
  onOpenChange,
  match,
  tournamentId,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  match: MatchOut
  tournamentId: number
}) {
  const qc = useQueryClient()

  const [homeScore, setHomeScore] = useState<number>(match.home_score ?? 0)
  const [awayScore, setAwayScore] = useState<number>(match.away_score ?? 0)
  const [events, setEvents] = useState<MatchEventIn[]>(
    match.events.map((e) => ({
      player_id: e.player_id,
      team_id: e.team_id,
      event_type: e.event_type as EventType,
      minute: e.minute,
      notes: e.notes,
    })),
  )

  const mutation = useMutation({
    mutationFn: (payload: MatchResultSubmit) =>
      tournamentApi.submitResult(tournamentId, match.id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['org-matches', tournamentId] })
      qc.invalidateQueries({ queryKey: ['matches', tournamentId] })
      qc.invalidateQueries({ queryKey: ['standings', tournamentId] })
      qc.invalidateQueries({ queryKey: ['top-scorers', tournamentId] })
      onOpenChange(false)
    },
  })

  function addEvent() {
    setEvents((prev) => [
      ...prev,
      {
        team_id: match.home_team_id,
        event_type: 'goal',
        player_id: null,
        minute: null,
        notes: null,
      },
    ])
  }

  function updateEvent<K extends keyof MatchEventIn>(idx: number, key: K, value: MatchEventIn[K]) {
    setEvents((prev) => prev.map((e, i) => (i === idx ? { ...e, [key]: value } : e)))
  }

  function removeEvent(idx: number) {
    setEvents((prev) => prev.filter((_, i) => i !== idx))
  }

  function handleSubmit() {
    mutation.mutate({ home_score: homeScore, away_score: awayScore, events })
  }

  return (
    <Modal
      open={open}
      onOpenChange={(next) => {
        if (!mutation.isPending) onOpenChange(next)
      }}
      title="Record Match Result"
      description={`${match.home_team_name} vs ${match.away_team_name}`}
      size="lg"
    >
      <div className="space-y-5">
        {mutation.isError && <FormAlert message={getErrorMessage(mutation.error)} />}

        {/* Score row */}
        <div className="flex items-center gap-4">
          <div className="flex-1 text-center">
            <p className="text-sm font-medium text-muted-foreground mb-1 truncate">
              {match.home_team_name}
            </p>
            <Input
              type="number"
              min={0}
              className="text-center text-2xl font-bold h-14"
              value={homeScore}
              onChange={(e) => setHomeScore(Number(e.target.value))}
            />
          </div>
          <span className="text-2xl font-bold text-muted-foreground">–</span>
          <div className="flex-1 text-center">
            <p className="text-sm font-medium text-muted-foreground mb-1 truncate">
              {match.away_team_name}
            </p>
            <Input
              type="number"
              min={0}
              className="text-center text-2xl font-bold h-14"
              value={awayScore}
              onChange={(e) => setAwayScore(Number(e.target.value))}
            />
          </div>
        </div>

        {/* Match events */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <Label className="text-sm font-semibold">Match Events</Label>
            <Button size="sm" variant="outline" onClick={addEvent}>
              <Plus className="size-3.5" />
              Add event
            </Button>
          </div>

          {events.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4 border rounded-md">
              No events recorded.
            </p>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {events.map((ev, idx) => (
                <div
                  key={idx}
                  className="grid grid-cols-[1fr_1fr_80px_auto] gap-2 items-center border rounded-md p-2"
                >
                  {/* Event type */}
                  <Select
                    value={ev.event_type}
                    onChange={(e) => updateEvent(idx, 'event_type', e.target.value as EventType)}
                    className="text-sm h-8"
                  >
                    {Object.entries(EVENT_TYPE_LABELS).map(([val, label]) => (
                      <option key={val} value={val}>
                        {label}
                      </option>
                    ))}
                  </Select>

                  {/* Team */}
                  <Select
                    value={ev.team_id}
                    onChange={(e) => updateEvent(idx, 'team_id', Number(e.target.value))}
                    className="text-sm h-8"
                  >
                    <option value={match.home_team_id}>{match.home_team_name}</option>
                    <option value={match.away_team_id}>{match.away_team_name}</option>
                  </Select>

                  {/* Minute */}
                  <Input
                    type="number"
                    min={1}
                    max={120}
                    placeholder="Min"
                    className="h-8 text-sm"
                    value={ev.minute ?? ''}
                    onChange={(e) =>
                      updateEvent(idx, 'minute', e.target.value ? Number(e.target.value) : null)
                    }
                  />

                  {/* Remove */}
                  <button
                    type="button"
                    onClick={() => removeEvent(idx)}
                    className="text-muted-foreground hover:text-destructive p-1 rounded"
                    aria-label="Remove event"
                  >
                    <Trash2 className="size-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <ModalActions>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} loading={mutation.isPending}>
            Save result
          </Button>
        </ModalActions>
      </div>
    </Modal>
  )
}

// ─── Match Row ────────────────────────────────────────────────────────────────

function MatchRow({
  match,
  onRecord,
}: {
  match: MatchOut
  tournamentId: number
  onRecord: (match: MatchOut) => void
}) {
  const hasResult = match.home_score !== null && match.away_score !== null
  return (
    <TableRow>
      <TableCell className="text-xs text-muted-foreground">
        {match.group_name ?? '—'}
      </TableCell>
      <TableCell className="text-xs text-muted-foreground">
        {match.match_date ?? '—'}
        {match.time_slot ? ` · ${match.time_slot}` : ''}
      </TableCell>
      <TableCell className="font-medium text-sm">
        {match.home_team_name}
        {hasResult && (
          <span className="ml-2 font-bold">
            {match.home_score} – {match.away_score}
          </span>
        )}
        {' '}vs{' '}
        {match.away_team_name}
      </TableCell>
      <TableCell>
        <span
          className={`text-xs px-2 py-0.5 rounded-full font-medium ${MATCH_STATUS_COLORS[match.status] ?? 'bg-muted text-muted-foreground'}`}
        >
          {match.status}
        </span>
      </TableCell>
      <TableCell>
        <Button size="sm" variant="outline" onClick={() => onRecord(match)}>
          {hasResult ? 'Edit result' : 'Record result'}
        </Button>
      </TableCell>
    </TableRow>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function TournamentManagePage() {
  const { id } = useParams<{ id: string }>()
  const tournamentId = Number(id)
  const [selectedMatch, setSelectedMatch] = useState<MatchOut | null>(null)

  const tQuery = useQuery({
    queryKey: ['tournament', tournamentId],
    queryFn: () => tournamentApi.get(tournamentId),
    enabled: !isNaN(tournamentId),
  })

  const matchesQuery = useQuery({
    queryKey: ['org-matches', tournamentId],
    queryFn: () => tournamentApi.listMatches(tournamentId),
    enabled: !isNaN(tournamentId),
  })

  const t = tQuery.data
  const matches = matchesQuery.data ?? []

  return (
    <>
      <div className="mb-4">
        <Link
          to="/organizer/tournaments"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Back to my tournaments
        </Link>
      </div>

      <PageHeader
        title={t ? `Manage: ${t.name}` : 'Manage tournament'}
        description={t ? `${t.sport.name} · ${t.format.replace(/_/g, ' ')}` : undefined}
      />

      {/* Generate schedule */}
      <GenerateSchedulePanel tournamentId={tournamentId} />

      {/* Matches */}
      <Card>
        <div className="p-4 border-b flex items-center gap-2">
          <ClipboardList className="size-4" />
          <h2 className="font-semibold">
            Fixtures &amp; Results{' '}
            {matches.length > 0 && (
              <Badge variant="secondary" className="ml-1">
                {matches.length}
              </Badge>
            )}
          </h2>
        </div>

        {matchesQuery.isPending ? (
          <div className="p-4 space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : matches.length === 0 ? (
          <EmptyState
            icon={CalendarClock}
            title="No fixtures yet"
            description="Generate a schedule to create fixtures."
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Group</TableHead>
                <TableHead>Date / Time</TableHead>
                <TableHead>Match</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {matches.map((m) => (
                <MatchRow
                  key={m.id}
                  match={m}
                  tournamentId={tournamentId}
                  onRecord={setSelectedMatch}
                />
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      {selectedMatch && (
        <RecordResultModal
          open={!!selectedMatch}
          onOpenChange={(open) => !open && setSelectedMatch(null)}
          match={selectedMatch}
          tournamentId={tournamentId}
        />
      )}
    </>
  )
}
