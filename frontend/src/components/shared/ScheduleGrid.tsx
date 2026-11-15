import { useMemo } from 'react'
import { DAYS, dayLabel, minutesToTime, timeToMinutes, toHHMM } from '@/lib/time'
import { cn } from '@/lib/utils'

export interface ScheduleSlot {
  id: number | string
  /** 1 = Monday ... 7 = Sunday */
  day: number
  /** "HH:MM" or "HH:MM:SS" */
  start: string
  end: string
  label?: string
}

export interface ScheduleGridProps {
  slots: ScheduleSlot[]
  /** Click an existing block (edit / delete). */
  onSlotClick?: (slot: ScheduleSlot) => void
  /** Click an empty hour cell (create). Receives the day and "HH:00". Omit for a read-only grid. */
  onCellClick?: (day: number, time: string) => void
  /** Default visible range; the grid grows if a slot falls outside it. */
  startHour?: number
  endHour?: number
  className?: string
}

const ROW_HEIGHT = 40

/**
 * Weekly (Mon–Sun) time grid. Reused for player availability now and for court / match
 * schedules in later modules: it only knows about `{ day, start, end }` blocks.
 */
export function ScheduleGrid({
  slots,
  onSlotClick,
  onCellClick,
  startHour = 6,
  endHour = 23,
  className,
}: ScheduleGridProps) {
  const { firstHour, lastHour } = useMemo(() => {
    let first = startHour
    let last = endHour
    for (const slot of slots) {
      first = Math.min(first, Math.floor(timeToMinutes(slot.start) / 60))
      last = Math.max(last, Math.ceil(timeToMinutes(slot.end) / 60))
    }
    return { firstHour: Math.max(0, first), lastHour: Math.min(24, last) }
  }, [slots, startHour, endHour])

  const hours = Array.from({ length: lastHour - firstHour }, (_, index) => firstHour + index)
  const gridHeight = hours.length * ROW_HEIGHT
  const gridStartMinutes = firstHour * 60

  return (
    <div className={cn('overflow-x-auto rounded-lg border bg-card', className)}>
      <div className="min-w-[720px]">
        <div className="grid grid-cols-[3.5rem_repeat(7,minmax(0,1fr))] border-b bg-muted/50">
          <div />
          {DAYS.map((day) => (
            <div
              key={day.value}
              className="border-l py-2 text-center text-xs font-semibold uppercase tracking-wide text-muted-foreground"
            >
              <span aria-hidden>{day.short}</span>
              <span className="sr-only">{day.long}</span>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-[3.5rem_repeat(7,minmax(0,1fr))]" style={{ height: gridHeight }}>
          <div className="relative" aria-hidden>
            {hours.map((hour, index) => (
              <div
                key={hour}
                className="absolute right-2 -translate-y-1/2 text-[11px] tabular-nums text-muted-foreground"
                style={{ top: index * ROW_HEIGHT }}
              >
                {index === 0 ? '' : minutesToTime(hour * 60)}
              </div>
            ))}
          </div>

          {DAYS.map((day) => (
            <div key={day.value} className="relative border-l">
              {hours.map((hour) => {
                const time = minutesToTime(hour * 60)
                const cellClass = 'block w-full border-t'
                return onCellClick ? (
                  <button
                    key={hour}
                    type="button"
                    onClick={() => onCellClick(day.value, time)}
                    className={cn(cellClass, 'transition-colors hover:bg-accent focus-visible:z-10')}
                    style={{ height: ROW_HEIGHT }}
                    aria-label={`Add availability on ${day.long} at ${time}`}
                  />
                ) : (
                  <div key={hour} className={cellClass} style={{ height: ROW_HEIGHT }} />
                )
              })}

              {slots
                .filter((slot) => slot.day === day.value)
                .map((slot) => {
                  const start = timeToMinutes(slot.start)
                  const end = timeToMinutes(slot.end)
                  const top = ((start - gridStartMinutes) / 60) * ROW_HEIGHT
                  const height = Math.max(((end - start) / 60) * ROW_HEIGHT, 20)
                  const range = `${toHHMM(slot.start)}–${toHHMM(slot.end)}`
                  const content = (
                    <>
                      <span className="block text-xs font-semibold leading-tight">{range}</span>
                      {slot.label && height >= 44 && (
                        <span className="block truncate text-[11px] leading-tight opacity-80">{slot.label}</span>
                      )}
                    </>
                  )
                  const blockClass =
                    'absolute inset-x-1 overflow-hidden rounded-md border-l-4 border-primary bg-primary/15 px-1.5 py-1 text-left text-accent-foreground'
                  return onSlotClick ? (
                    <button
                      key={slot.id}
                      type="button"
                      onClick={() => onSlotClick(slot)}
                      className={cn(blockClass, 'z-10 transition-colors hover:bg-primary/25')}
                      style={{ top, height }}
                      aria-label={`${dayLabel(slot.day)} ${range}. Edit`}
                    >
                      {content}
                    </button>
                  ) : (
                    <div key={slot.id} className={blockClass} style={{ top, height }}>
                      {content}
                    </div>
                  )
                })}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
