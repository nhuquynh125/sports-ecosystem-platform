import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'
import type { User } from '@/api/types'
import { usersApi } from '@/api/users'
import { ConfirmDialog } from '@/components/shared/Modal'
import { Field } from '@/components/shared/Field'
import { FormAlert } from '@/components/shared/FormAlert'
import { RoleBadge } from '@/components/shared/RoleBadge'
import { UserAvatar } from '@/components/shared/UserAvatar'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { meQueryKey } from '@/context/auth-context'
import { useAuth } from '@/hooks/use-auth'
import { fieldA11y } from '@/lib/field'
import { applyApiErrors, emptyToNull, passwordSchema } from '@/lib/forms'
import { toast } from '@/lib/toast'
import { formatDateTime } from '@/lib/utils'

const today = () => new Date().toISOString().slice(0, 10)

const accountSchema = z.object({
  full_name: z.string().trim().min(1, 'Full name is required').max(150, 'At most 150 characters'),
  phone: z.string().trim().max(30, 'At most 30 characters'),
  avatar_url: z
    .string()
    .trim()
    .max(500, 'At most 500 characters')
    .refine((value) => value === '' || /^https?:\/\//i.test(value), 'Must start with http:// or https://'),
  date_of_birth: z.string().refine((value) => value === '' || value <= today(), 'Date of birth cannot be in the future'),
  allow_scouting: z.boolean(),
})
type AccountValues = z.infer<typeof accountSchema>
const ACCOUNT_FIELDS = ['full_name', 'phone', 'avatar_url', 'date_of_birth', 'allow_scouting'] as const

function toAccountValues(user: User): AccountValues {
  return {
    full_name: user.full_name,
    phone: user.phone ?? '',
    avatar_url: user.avatar_url ?? '',
    date_of_birth: user.date_of_birth ?? '',
    allow_scouting: user.allow_scouting,
  }
}

function AccountForm({ user }: { user: User }) {
  const queryClient = useQueryClient()
  const [formError, setFormError] = useState<string | null>(null)

  const {
    register,
    control,
    handleSubmit,
    setError,
    formState: { errors, isDirty },
  } = useForm<AccountValues>({ resolver: zodResolver(accountSchema), values: toAccountValues(user) })
  const [watchedName, watchedAvatar] = useWatch({ control, name: ['full_name', 'avatar_url'] })

  const mutation = useMutation({
    mutationFn: (values: AccountValues) =>
      usersApi.updateMe({
        full_name: values.full_name,
        phone: emptyToNull(values.phone),
        avatar_url: emptyToNull(values.avatar_url),
        date_of_birth: emptyToNull(values.date_of_birth),
        allow_scouting: values.allow_scouting,
      }),
    meta: { silent: true },
    onSuccess: (updated) => {
      queryClient.setQueryData(meQueryKey, updated)
      toast.success('Account updated')
    },
    onError: (error) => setFormError(applyApiErrors(error, setError, ACCOUNT_FIELDS)),
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Account details</CardTitle>
        <CardDescription>Your email and username are fixed. Everything else can be changed here.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-5 flex flex-wrap items-center gap-4 rounded-lg bg-muted/60 p-4">
          <UserAvatar name={watchedName || user.full_name} src={watchedAvatar || null} className="size-14 text-base" />
          <div className="min-w-0 flex-1 text-sm">
            <p className="truncate font-semibold">{user.email}</p>
            <p className="text-muted-foreground">@{user.username} · last sign-in {formatDateTime(user.last_login_at)}</p>
            <div className="mt-1.5 flex flex-wrap gap-1">
              {user.roles.map((role) => (
                <RoleBadge key={role} role={role} />
              ))}
            </div>
          </div>
        </div>

        <form
          onSubmit={handleSubmit((values) => {
            setFormError(null)
            mutation.mutate(values)
          })}
          noValidate
          className="space-y-4"
        >
          <FormAlert message={formError} />
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Full name" htmlFor="acc-full_name" error={errors.full_name?.message} required>
              <Input {...register('full_name')} {...fieldA11y('acc-full_name', errors.full_name?.message)} autoComplete="name" />
            </Field>
            <Field label="Phone" htmlFor="acc-phone" error={errors.phone?.message}>
              <Input {...register('phone')} {...fieldA11y('acc-phone', errors.phone?.message)} type="tel" autoComplete="tel" />
            </Field>
            <Field label="Date of birth" htmlFor="acc-dob" error={errors.date_of_birth?.message}>
              <Input {...register('date_of_birth')} {...fieldA11y('acc-dob', errors.date_of_birth?.message)} type="date" max={today()} />
            </Field>
            <Field label="Avatar URL" htmlFor="acc-avatar" error={errors.avatar_url?.message} hint="Link to a square image">
              <Input {...register('avatar_url')} {...fieldA11y('acc-avatar', errors.avatar_url?.message, 'hint')} type="url" placeholder="https://…" />
            </Field>
          </div>

          <div className="flex items-start justify-between gap-4 rounded-lg border p-4">
            <div>
              <label htmlFor="acc-scouting" className="text-sm font-medium">
                Allow scouting
              </label>
              <p className="text-xs text-muted-foreground">Let coaches discover you and generate AI scouting reports. Off by default.</p>
            </div>
            <Controller
              control={control}
              name="allow_scouting"
              render={({ field }) => <Switch id="acc-scouting" checked={field.value} onCheckedChange={field.onChange} />}
            />
          </div>

          <div className="flex justify-end">
            <Button type="submit" loading={mutation.isPending} disabled={!isDirty}>
              Save changes
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

const passwordFormSchema = z
  .object({
    current_password: z.string().min(1, 'Enter your current password'),
    new_password: passwordSchema,
    confirm_password: z.string(),
  })
  .refine((values) => values.new_password === values.confirm_password, {
    path: ['confirm_password'],
    message: 'Passwords do not match',
  })
type PasswordValues = z.infer<typeof passwordFormSchema>

function PasswordForm() {
  const [formError, setFormError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm<PasswordValues>({ resolver: zodResolver(passwordFormSchema) })

  const mutation = useMutation({
    mutationFn: (values: PasswordValues) =>
      usersApi.changePassword({ current_password: values.current_password, new_password: values.new_password }),
    meta: { silent: true },
    onSuccess: () => {
      reset({ current_password: '', new_password: '', confirm_password: '' })
      toast.success('Password changed')
    },
    onError: (error) => setFormError(applyApiErrors(error, setError, ['current_password', 'new_password'])),
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Change password</CardTitle>
        <CardDescription>Use at least 8 characters with letters and digits.</CardDescription>
      </CardHeader>
      <CardContent>
        <form
          onSubmit={handleSubmit((values) => {
            setFormError(null)
            mutation.mutate(values)
          })}
          noValidate
          className="space-y-4"
        >
          <FormAlert message={formError} />
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="Current password" htmlFor="pw-current" error={errors.current_password?.message}>
              <Input {...register('current_password')} {...fieldA11y('pw-current', errors.current_password?.message)} type="password" autoComplete="current-password" />
            </Field>
            <Field label="New password" htmlFor="pw-new" error={errors.new_password?.message}>
              <Input {...register('new_password')} {...fieldA11y('pw-new', errors.new_password?.message)} type="password" autoComplete="new-password" />
            </Field>
            <Field label="Confirm new password" htmlFor="pw-confirm" error={errors.confirm_password?.message}>
              <Input {...register('confirm_password')} {...fieldA11y('pw-confirm', errors.confirm_password?.message)} type="password" autoComplete="new-password" />
            </Field>
          </div>
          <div className="flex justify-end">
            <Button type="submit" variant="outline" loading={mutation.isPending}>
              Update password
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

function DangerZone() {
  const { logout } = useAuth()
  const [open, setOpen] = useState(false)

  const mutation = useMutation({
    mutationFn: usersApi.deleteMe,
    onSuccess: () => {
      setOpen(false)
      logout({ silent: true })
      toast.info('Account deleted', 'Your personal data has been anonymised.')
    },
  })

  return (
    <Card className="border-destructive/30">
      <CardHeader>
        <CardTitle className="text-destructive">Delete account</CardTitle>
        <CardDescription>
          Your personal data is anonymised and you are signed out for good. Match statistics stay in aggregate form. This cannot be undone.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button variant="destructive" onClick={() => setOpen(true)}>
          Delete my account
        </Button>
      </CardContent>
      <ConfirmDialog
        open={open}
        onOpenChange={setOpen}
        title="Delete your account?"
        description="You will be signed out immediately and will not be able to log in again."
        confirmLabel="Yes, delete it"
        destructive
        loading={mutation.isPending}
        onConfirm={() => mutation.mutate()}
      />
    </Card>
  )
}

export function AccountTab() {
  const { user } = useAuth()
  if (!user) return null
  return (
    <div className="space-y-6">
      <AccountForm user={user} />
      <PasswordForm />
      <DangerZone />
    </div>
  )
}
