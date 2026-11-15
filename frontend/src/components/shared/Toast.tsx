import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react'
import { useSyncExternalStore, type ReactNode } from 'react'
import { dismiss, getToasts, subscribeToasts, type ToastKind } from '@/lib/toast'
import { cn } from '@/lib/utils'

const STYLES: Record<ToastKind, { icon: typeof Info; accent: string }> = {
  success: { icon: CheckCircle2, accent: 'text-success border-l-success' },
  error: { icon: AlertCircle, accent: 'text-destructive border-l-destructive' },
  info: { icon: Info, accent: 'text-primary border-l-primary' },
}

/** Renders the toast stack. Raise toasts anywhere with `toast.success(...)` from '@/lib/toast'. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const toasts = useSyncExternalStore(subscribeToasts, getToasts, getToasts)

  return (
    <>
      {children}
      <div
        className="pointer-events-none fixed inset-x-0 bottom-0 z-[100] flex flex-col items-end gap-2 p-4 sm:bottom-4 sm:right-4 sm:left-auto sm:p-0"
        role="region"
        aria-label="Notifications"
      >
        {toasts.map((item) => {
          const { icon: Icon, accent } = STYLES[item.kind]
          return (
            <div
              key={item.id}
              role={item.kind === 'error' ? 'alert' : 'status'}
              className={cn(
                'pointer-events-auto flex w-full max-w-sm animate-toast-in items-start gap-3 rounded-lg border border-l-4 bg-card p-3.5 shadow-xl',
                accent,
              )}
            >
              <Icon className="mt-0.5 size-5 shrink-0" aria-hidden />
              <div className="min-w-0 flex-1 text-foreground">
                <p className="text-sm font-semibold">{item.title}</p>
                {item.description && <p className="mt-0.5 break-words text-sm text-muted-foreground">{item.description}</p>}
              </div>
              <button
                type="button"
                onClick={() => dismiss(item.id)}
                className="rounded p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                <X className="size-4" aria-hidden />
                <span className="sr-only">Dismiss</span>
              </button>
            </div>
          )
        })}
      </div>
    </>
  )
}
