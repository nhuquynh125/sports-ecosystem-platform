import { Star } from 'lucide-react'
import { useState } from 'react'
import { isApiError } from '@/api/client'
import { useRatePlayer, type PickupMatch } from '@/api/sporthub'
import { FormAlert } from '@/components/shared/FormAlert'
import { Modal, ModalActions } from '@/components/shared/Modal'
import { UserAvatar } from '@/components/shared/UserAvatar'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { toast } from '@/lib/toast'
import { cn } from '@/lib/utils'

interface Draft {
  skill: number
  punctuality: number
  comment: string
}

function Stars({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="flex" role="radiogroup" aria-label={label}>
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            role="radio"
            aria-checked={value === n}
            aria-label={`${n} of 5`}
            onClick={() => onChange(n)}
            className="rounded p-0.5"
          >
            <Star className={cn('size-5', n <= value ? 'fill-warning text-warning' : 'text-muted-foreground/40')} aria-hidden />
          </button>
        ))}
      </div>
    </div>
  )
}

function RateForm({ match, meId, onDone }: { match: PickupMatch; meId: number; onDone: () => void }) {
  const rate = useRatePlayer(match.id)
  const [drafts, setDrafts] = useState<Record<number, Draft>>({})
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const targets = (match.players ?? []).filter((p) => p.user.id !== meId)
  const ready = targets.filter((p) => (drafts[p.user.id]?.skill ?? 0) > 0 && (drafts[p.user.id]?.punctuality ?? 0) > 0)

  function patch(userId: number, change: Partial<Draft>) {
    setDrafts((prev) => ({ ...prev, [userId]: { skill: 0, punctuality: 0, comment: '', ...prev[userId], ...change } }))
  }

  async function submit() {
    setError(null)
    setSaving(true)
    let ok = 0
    let already = 0
    const failures: string[] = []
    for (const p of ready) {
      const d = drafts[p.user.id]!
      try {
        await rate.mutateAsync({
          rated_user_id: p.user.id,
          skill_score: d.skill,
          punctuality_score: d.punctuality,
          comment: d.comment.trim() || null,
        })
        ok += 1
      } catch (e) {
        if (isApiError(e) && e.status === 409) already += 1
        else failures.push(`${p.user.full_name}: ${isApiError(e) ? e.message : 'failed'}`)
      }
    }
    setSaving(false)
    if (failures.length > 0) {
      setError(failures.join(' · '))
      return
    }
    toast.success('Ratings submitted', `${ok} saved${already ? `, ${already} already rated` : ''}.`)
    onDone()
  }

  if (targets.length === 0) {
    return <p className="py-6 text-center text-sm text-muted-foreground">No other players to rate for this match.</p>
  }

  return (
    <div className="space-y-4">
      <FormAlert message={error} />
      <ul className="space-y-3">
        {targets.map((p) => {
          const d = drafts[p.user.id]
          return (
            <li key={p.user.id} className="space-y-2 rounded-lg border p-3">
              <div className="flex items-center gap-3">
                <UserAvatar name={p.user.full_name} src={p.user.avatar_url} />
                <span className="text-sm font-medium">{p.user.full_name}</span>
              </div>
              <Stars label="Skill" value={d?.skill ?? 0} onChange={(v) => patch(p.user.id, { skill: v })} />
              <Stars label="Punctuality" value={d?.punctuality ?? 0} onChange={(v) => patch(p.user.id, { punctuality: v })} />
              <Input
                placeholder="Comment (optional)"
                maxLength={500}
                aria-label={`Comment for ${p.user.full_name}`}
                value={d?.comment ?? ''}
                onChange={(e) => patch(p.user.id, { comment: e.target.value })}
              />
            </li>
          )
        })}
      </ul>
      <ModalActions>
        <Button variant="outline" onClick={onDone} disabled={saving}>
          Cancel
        </Button>
        <Button onClick={() => void submit()} loading={saving} disabled={ready.length === 0}>
          Submit {ready.length > 0 ? `(${ready.length})` : ''}
        </Button>
      </ModalActions>
    </div>
  )
}

export function RatePlayersModal({
  match,
  meId,
  onClose,
}: {
  match: PickupMatch | null
  meId: number
  onClose: () => void
}) {
  return (
    <Modal
      open={match !== null}
      onOpenChange={(open) => !open && onClose()}
      title="Rate players"
      description="Rate skill and punctuality from 1 to 5. Only rated players are submitted."
    >
      {match && <RateForm key={match.id} match={match} meId={meId} onDone={onClose} />}
    </Modal>
  )
}