/** Weekly availability helpers. The API uses 1 = Monday ... 7 = Sunday and "HH:MM[:SS]" strings. */
export const DAYS = [
  { value: 1, short: 'Mon', long: 'Monday' },
  { value: 2, short: 'Tue', long: 'Tuesday' },
  { value: 3, short: 'Wed', long: 'Wednesday' },
  { value: 4, short: 'Thu', long: 'Thursday' },
  { value: 5, short: 'Fri', long: 'Friday' },
  { value: 6, short: 'Sat', long: 'Saturday' },
  { value: 7, short: 'Sun', long: 'Sunday' },
] as const

export function dayLabel(day: number, style: 'short' | 'long' = 'long'): string {
  return DAYS.find((d) => d.value === day)?.[style] ?? String(day)
}

export function timeToMinutes(time: string): number {
  const [h = '0', m = '0'] = time.split(':')
  return Number(h) * 60 + Number(m)
}

export function minutesToTime(total: number): string {
  const clamped = Math.max(0, Math.min(total, 24 * 60 - 1))
  const h = Math.floor(clamped / 60)
  const m = clamped % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

/** "08:00:00" -> "08:00" */
export function toHHMM(time: string): string {
  return time.slice(0, 5)
}
