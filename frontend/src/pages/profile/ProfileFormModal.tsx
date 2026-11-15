import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { z } from 'zod'
import { useCreateProfile, useUpdateProfile } from '@/api/profiles'
import { PREFERRED_SIDES, SKILL_LEVELS, type PlayerProfile, type Sport } from '@/api/types'
import { Field } from '@/components/shared/Field'
import { FormAlert } from '@/components/shared/FormAlert'
import { Modal, ModalActions } from '@/components/shared/Modal'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { fieldA11y } from '@/lib/field'
import { applyApiErrors, emptyToNull, numberOrNull } from '@/lib/forms'
import { toast } from '@/lib/toast'

const intInRange = (min: number, max: number, label: string) =>
  z
    .string()
    .trim()
    .refine((value) => value === '' || (/^\d+$/.test(value) && Number(value) >= min && Number(value) <= max), `${label} must be ${min}–${max}`)

const schema = z.object({
  sport_id: z.string().min(1, 'Choose a sport'),
  position: z.string().trim().max(50, 'At most 50 characters'),
  skill_level: z.enum(SKILL_LEVELS),
  preferred_side: z.enum(['', ...PREFERRED_SIDES]),
  height_cm: intInRange(50, 260, 'Height'),
  weight_kg: intInRange(20, 300, 'Weight'),
  city: z.string().trim().max(100, 'At most 100 characters'),
  bio: z.string().trim().max(2000, 'At most 2000 characters'),
  is_visible: z.boolean(),
})
type FormValues = z.infer<typeof schema>
const SERVER_FIELDS = ['sport_id', 'position', 'skill_level', 'preferred_side', 'height_cm', 'weight_kg', 'city', 'bio', 'is_visible'] as const

const LEVEL_LABELS: Record<(typeof SKILL_LEVELS)[number], string> = {
  beginner: 'Beginner',
  intermediate: 'Intermediate',
  advanced: 'Advanced',
  pro: 'Pro',
}

function ProfileForm({
  profile,
  sports,
  onDone,
}: {
  profile?: PlayerProfile
  sports: Sport[]
  onDone: () => void
}) {
  const [formError, setFormError] = useState<string | null>(null)
  const createProfile = useCreateProfile()
  const updateProfile = useUpdateProfile()
  const saving = createProfile.isPending || updateProfile.isPending

  const {
    register,
    control,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      sport_id: profile ? String(profile.sport_id) : sports.length === 1 ? String(sports[0]!.id) : '',
      position: profile?.position ?? '',
      skill_level: profile?.skill_level ?? 'beginner',
      preferred_side: profile?.preferred_side ?? '',
      height_cm: profile?.height_cm?.toString() ?? '',
      weight_kg: profile?.weight_kg?.toString() ?? '',
      city: profile?.city ?? '',
      bio: profile?.bio ?? '',
      is_visible: profile?.is_visible ?? true,
    },
  })

  async function onSubmit(values: FormValues) {
    setFormError(null)
    const common = {
      position: emptyToNull(values.position),
      skill_level: values.skill_level,
      preferred_side: values.preferred_side === '' ? null : values.preferred_side,
      height_cm: numberOrNull(values.height_cm),
      weight_kg: numberOrNull(values.weight_kg),
      city: emptyToNull(values.city),
      bio: emptyToNull(values.bio),
      is_visible: values.is_visible,
    }
    try {
      if (profile) {
        await updateProfile.mutateAsync({ id: profile.id, payload: common })
        toast.success('Profile updated')
      } else {
        await createProfile.mutateAsync({ sport_id: Number(values.sport_id), ...common })
        toast.success('Profile created')
      }
      onDone()
    } catch (error) {
      setFormError(applyApiErrors(error, setError, SERVER_FIELDS))
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      <FormAlert message={formError} />

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Sport" htmlFor="pf-sport" error={errors.sport_id?.message} hint={profile ? 'The sport cannot be changed' : undefined} required>
          <Select {...register('sport_id')} {...fieldA11y('pf-sport', errors.sport_id?.message, profile ? 'x' : undefined)} disabled={!!profile}>
            {!profile && <option value="">Select a sport…</option>}
            {sports.map((sport) => (
              <option key={sport.id} value={sport.id}>
                {sport.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Skill level" htmlFor="pf-level" error={errors.skill_level?.message} required>
          <Select {...register('skill_level')} {...fieldA11y('pf-level', errors.skill_level?.message)}>
            {SKILL_LEVELS.map((level) => (
              <option key={level} value={level}>
                {LEVEL_LABELS[level]}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Position" htmlFor="pf-position" error={errors.position?.message} hint="e.g. ST, Singles, Setter">
          <Input {...register('position')} {...fieldA11y('pf-position', errors.position?.message, 'x')} />
        </Field>
        <Field label="Preferred foot / hand" htmlFor="pf-side" error={errors.preferred_side?.message}>
          <Select {...register('preferred_side')} {...fieldA11y('pf-side', errors.preferred_side?.message)}>
            <option value="">No preference</option>
            {PREFERRED_SIDES.map((side) => (
              <option key={side} value={side}>
                {side[0]!.toUpperCase() + side.slice(1)}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Height (cm)" htmlFor="pf-height" error={errors.height_cm?.message}>
          <Input {...register('height_cm')} {...fieldA11y('pf-height', errors.height_cm?.message)} inputMode="numeric" />
        </Field>
        <Field label="Weight (kg)" htmlFor="pf-weight" error={errors.weight_kg?.message}>
          <Input {...register('weight_kg')} {...fieldA11y('pf-weight', errors.weight_kg?.message)} inputMode="numeric" />
        </Field>
      </div>

      <Field label="City / playing area" htmlFor="pf-city" error={errors.city?.message} hint="Used when others search for players near them">
        <Input {...register('city')} {...fieldA11y('pf-city', errors.city?.message, 'x')} placeholder="Đà Nẵng" />
      </Field>
      <Field label="Bio" htmlFor="pf-bio" error={errors.bio?.message}>
        <Textarea {...register('bio')} {...fieldA11y('pf-bio', errors.bio?.message)} rows={3} />
      </Field>

      <div className="flex items-start justify-between gap-4 rounded-lg border p-3.5">
        <div>
          <label htmlFor="pf-visible" className="text-sm font-medium">
            Visible in player search
          </label>
          <p className="text-xs text-muted-foreground">Turn off to hide this profile from other users.</p>
        </div>
        <Controller
          control={control}
          name="is_visible"
          render={({ field }) => <Switch id="pf-visible" checked={field.value} onCheckedChange={field.onChange} />}
        />
      </div>

      <ModalActions>
        <Button type="button" variant="outline" onClick={onDone} disabled={saving}>
          Cancel
        </Button>
        <Button type="submit" loading={saving}>
          {profile ? 'Save profile' : 'Create profile'}
        </Button>
      </ModalActions>
    </form>
  )
}

export function ProfileFormModal({
  open,
  onOpenChange,
  profile,
  sports,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Pass to edit; omit to create. */
  profile?: PlayerProfile
  /** Sports that can be chosen (already filtered for create mode). */
  sports: Sport[]
}) {
  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title={profile ? `Edit ${profile.sport.name} profile` : 'New sport profile'}
      description={profile ? undefined : 'You can have one profile per sport.'}
      size="lg"
    >
      <ProfileForm profile={profile} sports={sports} onDone={() => onOpenChange(false)} />
    </Modal>
  )
}
