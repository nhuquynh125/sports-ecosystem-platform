import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { useAddSlot, useDeleteSlot, useUpdateSlot } from '@/api/profiles'
import type { AvailabilitySlot } from '@/api/types'
import { Field } from '@/components/shared/Field'
import { FormAlert } from '@/components/shared/FormAlert'
import { Modal, ModalActions } from '@/components/shared/Modal'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { fieldA11y } from '@/lib/field'
import { applyApiErrors } from '@/lib/forms'
import { toast } from '@/lib/toast'
import { DAYS, toHHMM } from '@/lib/time'

const schema = z
  .object({
    day_of_week: z.string(),
    start_time: z.string().min(1, 'Start time is required'),
    end_time: z.string().min(1, 'End time is required'),
  })
  .refine((values) => !values.start_time || !values.end_time || values.end_time > values.start_time, {
    path: ['end_time'],
    message: 'End time must be after start time',
  })
type FormValues = z.infer<typeof schema>

export interface SlotDraft {
  day: number
  start: string
  end: string
}

function SlotForm({
  profileId,
  slot,
  draft,
  onDone,
}: {
  profileId: number
  slot?: AvailabilitySlot
  draft?: SlotDraft
  onDone: () => void
}) {
  const [formError, setFormError] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const addSlot = useAddSlot(profileId)
  const updateSlot = useUpdateSlot(profileId)
  const deleteSlot = useDeleteSlot(profileId)
  const saving = addSlot.isPending || updateSlot.isPending

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      day_of_week: String(slot?.day_of_week ?? draft?.day ?? 1),
      start_time: slot ? toHHMM(slot.start_time) : (draft?.start ?? '18:00'),
      end_time: slot ? toHHMM(slot.end_time) : (draft?.end ?? '20:00'),
    },
  })

  async function onSubmit(values: FormValues) {
    setFormError(null)
    const payload = {
      day_of_week: Number(values.day_of_week),
      start_time: values.start_time,
      end_time: values.end_time,
    }
    try {
      if (slot) await updateSlot.mutateAsync({ slotId: slot.id, payload })
      else await addSlot.mutateAsync(payload)
      toast.success(slot ? 'Availability updated' : 'Availability added')
      onDone()
    } catch (error) {
      // e.g. 422 "Availability window overlaps an existing window"
      setFormError(applyApiErrors(error, setError, ['day_of_week', 'start_time', 'end_time']))
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      <FormAlert message={formError} />
      <Field label="Day" htmlFor="slot-day" error={errors.day_of_week?.message}>
        <Select {...register('day_of_week')} {...fieldA11y('slot-day', errors.day_of_week?.message)}>
          {DAYS.map((day) => (
            <option key={day.value} value={day.value}>
              {day.long}
            </option>
          ))}
        </Select>
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field label="From" htmlFor="slot-start" error={errors.start_time?.message}>
          <Input {...register('start_time')} {...fieldA11y('slot-start', errors.start_time?.message)} type="time" step={900} />
        </Field>
        <Field label="To" htmlFor="slot-end" error={errors.end_time?.message}>
          <Input {...register('end_time')} {...fieldA11y('slot-end', errors.end_time?.message)} type="time" step={900} />
        </Field>
      </div>

      <ModalActions>
        {slot && (
          <Button
            type="button"
            variant={confirmDelete ? 'destructive' : 'ghost'}
            className={confirmDelete ? 'sm:mr-auto' : 'text-destructive hover:text-destructive sm:mr-auto'}
            loading={deleteSlot.isPending}
            onClick={() => {
              if (!confirmDelete) return setConfirmDelete(true)
              deleteSlot.mutate(slot.id, {
                onSuccess: () => {
                  toast.success('Availability removed')
                  onDone()
                },
              })
            }}
          >
            {confirmDelete ? 'Click again to confirm' : 'Delete'}
          </Button>
        )}
        <Button type="button" variant="outline" onClick={onDone} disabled={saving}>
          Cancel
        </Button>
        <Button type="submit" loading={saving}>
          {slot ? 'Save' : 'Add window'}
        </Button>
      </ModalActions>
    </form>
  )
}

export function SlotModal({
  profileId,
  open,
  onOpenChange,
  slot,
  draft,
}: {
  profileId: number
  open: boolean
  onOpenChange: (open: boolean) => void
  slot?: AvailabilitySlot
  draft?: SlotDraft
}) {
  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title={slot ? 'Edit availability' : 'Add availability'}
      description="A recurring weekly window. Windows on the same day cannot overlap."
      size="sm"
    >
      <SlotForm profileId={profileId} slot={slot} draft={draft} onDone={() => onOpenChange(false)} />
    </Modal>
  )
}
