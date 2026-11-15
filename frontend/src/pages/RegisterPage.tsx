import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { authApi } from '@/api/auth'
import { AuthLayout } from '@/components/shared/AuthLayout'
import { Field } from '@/components/shared/Field'
import { FormAlert } from '@/components/shared/FormAlert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { ROLE_DESCRIPTIONS, ROLE_LABELS, SELF_ASSIGNABLE_ROLES } from '@/config/roles'
import { fieldA11y } from '@/lib/field'
import { applyApiErrors, passwordSchema } from '@/lib/forms'
import { toast } from '@/lib/toast'

const schema = z
  .object({
    full_name: z.string().trim().min(1, 'Full name is required').max(150, 'At most 150 characters'),
    username: z
      .string()
      .trim()
      .min(3, 'At least 3 characters')
      .max(50, 'At most 50 characters')
      .regex(/^[A-Za-z0-9_.-]+$/, "Only letters, digits, '_', '.' and '-'"),
    email: z.string().trim().min(1, 'Email is required').email('Enter a valid email address'),
    role: z.enum(SELF_ASSIGNABLE_ROLES),
    password: passwordSchema,
    confirm_password: z.string(),
  })
  .refine((values) => values.password === values.confirm_password, {
    path: ['confirm_password'],
    message: 'Passwords do not match',
  })
type FormValues = z.infer<typeof schema>

const SERVER_FIELDS = ['full_name', 'username', 'email', 'role', 'password'] as const

export function RegisterPage() {
  const navigate = useNavigate()
  const [formError, setFormError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    setError,
    control,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { role: 'player' },
  })

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      authApi.register({
        email: values.email,
        username: values.username,
        full_name: values.full_name,
        password: values.password,
        role: values.role,
      }),
    meta: { silent: true },
    onSuccess: (_user, values) => {
      toast.success('Account created', 'You can sign in now.')
      navigate('/login', { replace: true, state: { registeredEmail: values.email } })
    },
    onError: (error) => setFormError(applyApiErrors(error, setError, SERVER_FIELDS)),
  })

  const role = useWatch({ control, name: 'role' })

  return (
    <AuthLayout title="Create account" subtitle="Join the platform in under a minute.">
      <form
        onSubmit={handleSubmit((values) => {
          setFormError(null)
          mutation.mutate(values)
        })}
        noValidate
        className="space-y-4"
      >
        <FormAlert message={formError} />

        <Field label="Full name" htmlFor="full_name" error={errors.full_name?.message} required>
          <Input {...register('full_name')} {...fieldA11y('full_name', errors.full_name?.message)} autoComplete="name" autoFocus />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Username" htmlFor="username" error={errors.username?.message} required>
            <Input {...register('username')} {...fieldA11y('username', errors.username?.message)} autoComplete="username" />
          </Field>
          <Field label="I am a…" htmlFor="role" error={errors.role?.message} hint={ROLE_DESCRIPTIONS[role]}>
            <Select {...register('role')} {...fieldA11y('role', errors.role?.message, ROLE_DESCRIPTIONS[role])}>
              {SELF_ASSIGNABLE_ROLES.map((value) => (
                <option key={value} value={value}>
                  {ROLE_LABELS[value]}
                </option>
              ))}
            </Select>
          </Field>
        </div>
        <Field label="Email" htmlFor="email" error={errors.email?.message} required>
          <Input {...register('email')} {...fieldA11y('email', errors.email?.message)} type="email" autoComplete="email" />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Password" htmlFor="password" error={errors.password?.message} hint="8+ characters with letters and digits" required>
            <Input {...register('password')} {...fieldA11y('password', errors.password?.message, 'hint')} type="password" autoComplete="new-password" />
          </Field>
          <Field label="Confirm password" htmlFor="confirm_password" error={errors.confirm_password?.message} required>
            <Input {...register('confirm_password')} {...fieldA11y('confirm_password', errors.confirm_password?.message)} type="password" autoComplete="new-password" />
          </Field>
        </div>

        <Button type="submit" className="w-full" size="lg" loading={mutation.isPending}>
          Create account
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{' '}
        <Link to="/login" className="font-semibold text-primary underline-offset-4 hover:underline">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  )
}
