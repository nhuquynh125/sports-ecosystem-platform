/**
 * Tiny external toast store, so non-React code (the React Query caches, the API client) can raise
 * toasts too. `ToastProvider` (components/shared/Toast.tsx) renders it.
 */
export type ToastKind = 'success' | 'error' | 'info'

export interface ToastItem {
  id: number
  kind: ToastKind
  title: string
  description?: string
}

let items: ToastItem[] = []
let nextId = 1
const listeners = new Set<() => void>()

function emit() {
  listeners.forEach((listener) => listener())
}

function push(kind: ToastKind, title: string, description?: string): number {
  const id = nextId++
  // Keep the stack short: drop the oldest beyond four.
  items = [...items, { id, kind, title, description }].slice(-4)
  emit()
  window.setTimeout(() => dismiss(id), kind === 'error' ? 7000 : 4500)
  return id
}

export function dismiss(id: number) {
  items = items.filter((item) => item.id !== id)
  emit()
}

export const toast = {
  success: (title: string, description?: string) => push('success', title, description),
  error: (title: string, description?: string) => push('error', title, description),
  info: (title: string, description?: string) => push('info', title, description),
  dismiss,
}

export function subscribeToasts(listener: () => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

export function getToasts(): ToastItem[] {
  return items
}
