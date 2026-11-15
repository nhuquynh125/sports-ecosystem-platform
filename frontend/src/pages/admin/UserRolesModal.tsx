import { useState } from 'react'
import { useSetUserRoles } from '@/api/admin'
import type { User } from '@/api/types'
import { Modal, ModalActions } from '@/components/shared/Modal'
import { Button } from '@/components/ui/button'
import { ROLES, ROLE_DESCRIPTIONS, ROLE_LABELS, type Role } from '@/config/roles'
import { toast } from '@/lib/toast'

function RolesForm({ user, onDone }: { user: User; onDone: () => void }) {
  const [selected, setSelected] = useState<Role[]>(user.roles)
  const mutation = useSetUserRoles()

  function toggle(role: Role) {
    setSelected((current) => (current.includes(role) ? current.filter((r) => r !== role) : [...current, role]))
  }

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault()
        mutation.mutate(
          { userId: user.id, roles: ROLES.filter((role) => selected.includes(role)) },
          {
            onSuccess: () => {
              toast.success('Roles updated', `${user.full_name} was notified.`)
              onDone()
            },
          },
        )
      }}
    >
      <fieldset className="space-y-2">
        <legend className="sr-only">Roles</legend>
        {ROLES.map((role) => (
          <label
            key={role}
            className="flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors hover:bg-muted/50 has-[:checked]:border-primary/50 has-[:checked]:bg-accent/50"
          >
            <input
              type="checkbox"
              checked={selected.includes(role)}
              onChange={() => toggle(role)}
              className="mt-0.5 size-4 accent-[hsl(var(--primary))]"
            />
            <span>
              <span className="block text-sm font-semibold">{ROLE_LABELS[role]}</span>
              <span className="block text-xs text-muted-foreground">{ROLE_DESCRIPTIONS[role]}</span>
            </span>
          </label>
        ))}
      </fieldset>
      {selected.length === 0 && <p className="mt-3 text-xs font-medium text-destructive">Select at least one role.</p>}
      <ModalActions>
        <Button type="button" variant="outline" onClick={onDone} disabled={mutation.isPending}>
          Cancel
        </Button>
        <Button type="submit" loading={mutation.isPending} disabled={selected.length === 0}>
          Save roles
        </Button>
      </ModalActions>
    </form>
  )
}

export function UserRolesModal({ user, onClose }: { user: User | null; onClose: () => void }) {
  return (
    <Modal
      open={user !== null}
      onOpenChange={(open) => !open && onClose()}
      title="Edit roles"
      description={user ? `${user.full_name} (@${user.username})` : undefined}
      size="sm"
    >
      {user && <RolesForm key={user.id} user={user} onDone={onClose} />}
    </Modal>
  )
}
