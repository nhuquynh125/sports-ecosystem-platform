import { Bell, BellRing, CheckCheck, ShieldCheck, UserCog, type LucideIcon } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMarkAllRead, useMarkRead, useNotifications, useUnreadCount } from '@/api/notifications'
import type { AppNotification } from '@/api/types'
import { getErrorMessage } from '@/api/client'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/hooks/use-auth'
import { cn, formatRelative } from '@/lib/utils'

const TYPE_ICONS: Record<string, LucideIcon> = {
  welcome: BellRing,
  roles_changed: UserCog,
  account_unlocked: ShieldCheck,
}

export function NotificationBell() {
  const navigate = useNavigate()
  const { refetchUser } = useAuth()
  const [open, setOpen] = useState(false)

  const unread = useUnreadCount(true)
  const list = useNotifications(open)
  const markRead = useMarkRead()
  const markAll = useMarkAllRead()

  const count = unread.data ?? 0
  const items = list.data?.items ?? []

  function handleOpenChange(next: boolean) {
    setOpen(next)
    // Opening the bell is a natural moment to pick up role changes made by an admin.
    if (next) refetchUser()
  }

  function openNotification(item: AppNotification) {
    if (!item.is_read) markRead.mutate(item.id)
    const link = item.data?.deep_link
    if (typeof link === 'string' && link.startsWith('/')) {
      setOpen(false)
      navigate(link)
    }
  }

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          aria-label={count > 0 ? `Notifications, ${count} unread` : 'Notifications'}
        >
          <Bell className="!size-5" aria-hidden />
          {count > 0 && (
            <span
              className="absolute right-1 top-1 flex min-w-[18px] items-center justify-center rounded-full bg-highlight px-1 text-[10px] font-bold leading-[18px] text-highlight-foreground"
              aria-hidden
            >
              {count > 99 ? '99+' : count}
            </span>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent className="w-[min(24rem,calc(100vw-1.5rem))]">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h2 className="font-display text-lg font-semibold uppercase tracking-wide">Notifications</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => markAll.mutate()}
            disabled={count === 0}
            loading={markAll.isPending}
          >
            <CheckCheck aria-hidden />
            Mark all read
          </Button>
        </div>

        <div className="max-h-[22rem] overflow-y-auto">
          {list.isPending ? (
            <div className="space-y-3 p-4">
              {[0, 1, 2].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : list.isError ? (
            <div className="p-6 text-center text-sm">
              <p className="text-destructive">{getErrorMessage(list.error)}</p>
              <Button variant="outline" size="sm" className="mt-3" onClick={() => void list.refetch()}>
                Try again
              </Button>
            </div>
          ) : items.length === 0 ? (
            <div className="px-6 py-10 text-center text-sm text-muted-foreground">
              <Bell className="mx-auto mb-2 size-7 opacity-40" aria-hidden />
              You're all caught up.
            </div>
          ) : (
            <ul className="divide-y">
              {items.map((item) => {
                const Icon = TYPE_ICONS[item.type] ?? Bell
                return (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => openNotification(item)}
                      className={cn(
                        'flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-muted/60',
                        !item.is_read && 'bg-accent/50',
                      )}
                    >
                      <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                        <Icon className="size-4" aria-hidden />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="flex items-start justify-between gap-2">
                          <span className={cn('text-sm', !item.is_read ? 'font-semibold' : 'font-medium')}>{item.title}</span>
                          {!item.is_read && (
                            <>
                              <span className="mt-1.5 size-2 shrink-0 rounded-full bg-highlight" aria-hidden />
                              <span className="sr-only">Unread</span>
                            </>
                          )}
                        </span>
                        {item.body && <span className="mt-0.5 line-clamp-2 block text-xs text-muted-foreground">{item.body}</span>}
                        <span className="mt-1 block text-[11px] text-muted-foreground">{formatRelative(item.created_at)}</span>
                      </span>
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}
