import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { useCreateMatch } from '@/api/sporthub'
import { useSports } from '@/api/sports'
import { SKILL_LEVELS } from '@/api/types'
import { Field } from '@/components/shared/Field'
import { FormAlert } from '@/components/shared/FormAlert'
import { PageHeader } from '@/components/shared/PageHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { fieldA11y } from '@/lib/field'
import { applyApiErrors } from '@/lib/forms'
import { toast } from '@/lib/toast'

const todayLocal = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const schema = z.object({
  sport_id: z.string().min(1, 'Choose a sport'),
  title: z.string().trim().min(2, 'At least 2 characters').max(150, 'At most 150 characters'),
  area: z.string().trim().min(2, 'At least 2 characters').max(150, 'At most 150 characters'),
  skill_level: z.enum(SKILL_LEVELS),
  match_date: z.string().min(1, 'Pick a date').refine((v) => v >= todayLocal(), 'Date cannot be in the past'),
  time_slot: z.string().regex(/^\d{2}:\d{2}$/, 'Pick a start time'),
  max_players: z
    .string()
    .refine((v) => /^\d+$/.test(v) && Number(v) >= 2 && Number(v) <= 100, 'Between 2 and 100 players'),
  description: z.string().trim().max(1000, 'At most 1000 characters'),
})
type FormValues = z.infer<typeof schema>
const SERVER_FIELDS = ['sport_id', 'title', 'area', 'skill_level', 'match_date', 'time_slot', 'max_players', 'description'] as const

export function CreateMatchPage() {
  const navigate = useNavigate()
  const sports = useSports()
  const create = useCreateMatch()
  const [formError, setFormError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      sport_id: '',
      title: '',
      area: '',
      skill_level: 'intermediate',
      match_date: todayLocal(),
      time_slot: '18:00',
      max_players: '10',
      description: '',
    },
  })

  function onSubmit(values: FormValues) {
    setFormError(null)
    create.mutate(
      {
        sport_id: Number(values.sport_id),
        title: values.title,
        area: values.area,
        skill_level: values.skill_level,
        match_date: values.match_date,
        time_slot: values.time_slot,
        max_players: Number(values.max_players),
        description: values.description || null,
      },
      {
        onSuccess: (match) => {
          toast.success('Match created')
          navigate(match.id ? `/matches/${match.id}` : '/matches/me', { replace: true })
        },
        onError: (error) => setFormError(applyApiErrors(error, setError, SERVER_FIELDS)),
      },
    )
  }

  return (
    <>
      <PageHeader title="Create a match" description="Post an open game and let players join." />
      <Card className="max-w-2xl">
        <CardContent className="pt-5">
          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
            <FormAlert message={formError} />
            <Field label="Title" htmlFor="m-title" error={errors.title?.message} required>
              <Input {...register('title')} {...fieldA11y('m-title', errors.title?.message)} placeholder="Friday night 5v5" />
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Sport" htmlFor="m-sport" error={errors.sport_id?.message} required>
                <Select {...register('sport_id')} {...fieldA11y('m-sport', errors.sport_id?.message)}>
                  <option value="">Select a sport…</option>
                  {(sports.data ?? []).map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Skill level" htmlFor="m-skill" error={errors.skill_level?.message} required>
                <Select {...register('skill_level')} {...fieldA11y('m-skill', errors.skill_level?.message)}>
                  {SKILL_LEVELS.map((l) => (
                    <option key={l} value={l}>
                      {l[0]!.toUpperCase() + l.slice(1)}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Date" htmlFor="m-date" error={errors.match_date?.message} required>
                <Input type="date" min={todayLocal()} {...register('match_date')} {...fieldA11y('m-date', errors.match_date?.message)} />
              </Field>
              <Field label="Start time" htmlFor="m-time" error={errors.time_slot?.message} required>
                <Input type="time" {...register('time_slot')} {...fieldA11y('m-time', errors.time_slot?.message)} />
              </Field>
              <Field label="Area" htmlFor="m-area" error={errors.area?.message} hint="District and city" required>
                <Input {...register('area')} {...fieldA11y('m-area', errors.area?.message, 'hint')} placeholder="Hải Châu, Đà Nẵng" />
              </Field>
              <Field label="Max players" htmlFor="m-max" error={errors.max_players?.message} required>
                <Input inputMode="numeric" {...register('max_players')} {...fieldA11y('m-max', errors.max_players?.message)} />
              </Field>
            </div>
            <Field label="Description" htmlFor="m-desc" error={errors.description?.message}>
              <Textarea rows={3} {...register('description')} {...fieldA11y('m-desc', errors.description?.message)} />
            </Field>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => navigate(-1)} disabled={create.isPending}>
                Cancel
              </Button>
              <Button type="submit" loading={create.isPending}>
                Create match
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </>
  )
}