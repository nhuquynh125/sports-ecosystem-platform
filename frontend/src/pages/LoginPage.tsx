import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { AuthLayout } from '@/components/shared/AuthLayout'
import { Field } from '@/components/shared/Field'
import { FormAlert } from '@/components/shared/FormAlert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/hooks/use-auth'
import { fieldA11y } from '@/lib/field'
import { getErrorMessage } from '@/api/client'
import { toast } from '@/lib/toast'

const schema = z.object({
  email: z.string().trim().min(1, 'Email is required').email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})
type FormValues = z.infer<typeof schema>

// Accounts created by `python scripts/seed.py` (development only).
const DEMO_ACCOUNTS = [
  { label: 'Admin', email: 'admin@example.com' },
  { label: 'Player', email: 'player@example.com' },
  { label: 'Coach', email: 'coach@example.com' },
  { label: 'Organizer', email: 'organizer@example.com' },
  { label: 'Owner', email: 'owner@example.com' },
]

interface LocationState {
  from?: string
  registeredEmail?: string
}

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const state = (useLocation().state ?? {}) as LocationState

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: state.registeredEmail ?? '', password: '' },
  })

  const mutation = useMutation({
    mutationFn: (values: FormValues) => login(values.email, values.password),
    meta: { silent: true },
    onSuccess: (user) => {
      toast.success(`Welcome back, ${user.full_name.split(' ')[0]}!`)
      const target = state.from && state.from !== '/login' ? state.from : '/'
      navigate(target, { replace: true })
    },
  })

  return (
    <AuthLayout title="Sign in" subtitle="Welcome back. Enter your details to continue.">
      <form onSubmit={handleSubmit((values) => mutation.mutate(values))} noValidate className="space-y-4">
        {state.registeredEmail && !mutation.isError && (
          <p role="status" className="rounded-md border border-primary/25 bg-accent px-3 py-2.5 text-sm text-accent-foreground">
            Account created. Sign in to continue.
          </p>
        )}
        <FormAlert message={mutation.isError ? getErrorMessage(mutation.error) : null} />

        <Field label="Email" htmlFor="email" error={errors.email?.message} required>
          <Input {...register('email')} {...fieldA11y('email', errors.email?.message)} type="email" autoComplete="username" autoFocus />
        </Field>
        <Field label="Password" htmlFor="password" error={errors.password?.message} required>
          <Input {...register('password')} {...fieldA11y('password', errors.password?.message)} type="password" autoComplete="current-password" />
        </Field>

        <Button type="submit" className="w-full" size="lg" loading={mutation.isPending}>
          Sign in
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        New here?{' '}
        <Link to="/register" className="font-semibold text-primary underline-offset-4 hover:underline">
          Create an account
        </Link>
      </p>

      {import.meta.env.DEV && (
        <div className="mt-8 rounded-lg border border-dashed p-3">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Dev only · seeded demo logins (password Password123!)
          </p>
          <div className="flex flex-wrap gap-1.5">
            {DEMO_ACCOUNTS.map((account) => (
              <Button
                key={account.email}
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => {
                  setValue('email', account.email, { shouldValidate: true })
                  setValue('password', 'Password123!', { shouldValidate: true })
                }}
              >
                {account.label}
              </Button>
            ))}
          </div>
        </div>
      )}
    </AuthLayout>
  )
}
