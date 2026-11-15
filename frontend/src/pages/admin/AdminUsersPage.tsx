import { Lock, LockOpen, UserCog } from 'lucide-react'
import { useState } from 'react'
import { useAdminUsers, useSetUserStatus } from '@/api/admin'
import { getErrorMessage } from '@/api/client'
import type { User } from '@/api/types'
import { DataTable, type DataTableColumn } from '@/components/shared/DataTable'
import { ConfirmDialog } from '@/components/shared/Modal'
import { PageHeader } from '@/components/shared/PageHeader'
import { RoleBadge } from '@/components/shared/RoleBadge'
import { UserAvatar } from '@/components/shared/UserAvatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { ROLES, ROLE_LABELS } from '@/config/roles'
import { useAuth } from '@/hooks/use-auth'
import { toast } from '@/lib/toast'
import { formatDate, formatDateTime } from '@/lib/utils'
import { UserRolesModal } from './UserRolesModal'

type StatusFilter = '' | 'active' | 'locked'

export function AdminUsersPage() {
  const { user: me } = useAuth()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [role, setRole] = useState('')
  const [status, setStatus] = useState<StatusFilter>('')

  const [lockTarget, setLockTarget] = useState<User | null>(null)
  const [rolesTarget, setRolesTarget] = useState<User | null>(null)

  const query = useAdminUsers({
    page,
    page_size: pageSize,
    q: search,
    role,
    is_active: status === '' ? undefined : status === 'active',
  })
  const setUserStatus = useSetUserStatus()

  const columns: DataTableColumn<User>[] = [
    {
      id: 'user',
      header: 'User',
      sortValue: (u) => u.full_name,
      cell: (u) => (
        <div className="flex items-center gap-3">
          <UserAvatar name={u.full_name} src={u.avatar_url} />
          <div className="min-w-0">
            <p className="truncate font-medium">{u.full_name}</p>
            <p className="truncate text-xs text-muted-foreground">@{u.username}</p>
          </div>
        </div>
      ),
    },
    { id: 'email', header: 'Email', sortValue: (u) => u.email, cell: (u) => <span className="text-muted-foreground">{u.email}</span> },
    {
      id: 'roles',
      header: 'Roles',
      cell: (u) => (
        <div className="flex flex-wrap gap-1">
          {u.roles.map((r) => (
            <RoleBadge key={r} role={r} />
          ))}
        </div>
      ),
    },
    {
      id: 'status',
      header: 'Status',
      sortValue: (u) => u.is_active,
      cell: (u) => <Badge variant={u.is_active ? 'success' : 'destructive'}>{u.is_active ? 'Active' : 'Locked'}</Badge>,
    },
    {
      id: 'last_login',
      header: 'Last sign-in',
      sortValue: (u) => u.last_login_at,
      cell: (u) => <span className="whitespace-nowrap text-muted-foreground">{formatDateTime(u.last_login_at)}</span>,
    },
    {
      id: 'created',
      header: 'Joined',
      sortValue: (u) => u.created_at,
      cell: (u) => <span className="whitespace-nowrap text-muted-foreground">{formatDate(u.created_at)}</span>,
    },
    {
      id: 'actions',
      header: <span className="sr-only">Actions</span>,
      className: 'text-right',
      cell: (u) => {
        const isSelf = u.id === me?.id
        return (
          <div className="flex justify-end gap-1">
            <Button variant="ghost" size="icon" onClick={() => setRolesTarget(u)} aria-label={`Edit roles of ${u.full_name}`} title="Edit roles">
              <UserCog aria-hidden />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className={u.is_active ? 'text-destructive hover:text-destructive' : 'text-primary'}
              onClick={() => (u.is_active ? setLockTarget(u) : unlock(u))}
              disabled={isSelf || (setUserStatus.isPending && setUserStatus.variables?.userId === u.id)}
              aria-label={`${u.is_active ? 'Lock' : 'Unlock'} ${u.full_name}`}
              title={isSelf ? 'You cannot lock your own account' : u.is_active ? 'Lock account' : 'Unlock account'}
            >
              {u.is_active ? <Lock aria-hidden /> : <LockOpen aria-hidden />}
            </Button>
          </div>
        )
      },
    },
  ]

  function unlock(target: User) {
    setUserStatus.mutate(
      { userId: target.id, isActive: true },
      { onSuccess: () => toast.success('Account unlocked', `${target.full_name} can sign in again.`) },
    )
  }

  function confirmLock() {
    if (!lockTarget) return
    const target = lockTarget
    setUserStatus.mutate(
      { userId: target.id, isActive: false },
      {
        onSuccess: () => {
          toast.success('Account locked', `${target.full_name} is signed out on their next request.`)
          setLockTarget(null)
        },
        onError: () => setLockTarget(null),
      },
    )
  }

  return (
    <>
      <PageHeader title="Users" description="Search accounts, lock or unlock access and manage roles." />

      <DataTable
        caption="Platform users"
        columns={columns}
        data={query.data?.items ?? []}
        getRowId={(u) => u.id}
        isLoading={query.isPending}
        isFetching={query.isFetching}
        error={query.isError && !query.data ? getErrorMessage(query.error) : null}
        onRetry={() => void query.refetch()}
        search={{
          value: search,
          placeholder: 'Search by name, username or email',
          onChange: (value) => {
            setSearch(value)
            setPage(1)
          },
        }}
        filters={
          <>
            <Select
              value={role}
              onChange={(event) => {
                setRole(event.target.value)
                setPage(1)
              }}
              aria-label="Filter by role"
              className="w-[160px]"
            >
              <option value="">All roles</option>
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {ROLE_LABELS[r]}
                </option>
              ))}
            </Select>
            <Select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value as StatusFilter)
                setPage(1)
              }}
              aria-label="Filter by status"
              className="w-[140px]"
            >
              <option value="">Any status</option>
              <option value="active">Active</option>
              <option value="locked">Locked</option>
            </Select>
          </>
        }
        pagination={{
          page,
          pageSize,
          total: query.data?.total ?? 0,
          onPageChange: setPage,
          onPageSizeChange: (size) => {
            setPageSize(size)
            setPage(1)
          },
        }}
        emptyTitle="No users found"
        emptyDescription="Try a different search or clear the filters."
      />

      <ConfirmDialog
        open={lockTarget !== null}
        onOpenChange={(open) => !open && setLockTarget(null)}
        title={`Lock ${lockTarget?.full_name ?? 'account'}?`}
        description="They will be unable to sign in, and their current session stops working immediately. You can unlock the account at any time."
        confirmLabel="Lock account"
        destructive
        loading={setUserStatus.isPending}
        onConfirm={confirmLock}
      />
      <UserRolesModal user={rolesTarget} onClose={() => setRolesTarget(null)} />
    </>
  )
}
