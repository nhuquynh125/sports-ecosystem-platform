import { cn } from '@/lib/utils'

export function BrandLogo({ className, inverted = false }: { className?: string; inverted?: boolean }) {
  return (
    <span className={cn('inline-flex items-center gap-2.5', className)}>
      <svg viewBox="0 0 64 64" className="size-8" aria-hidden>
        <rect width="64" height="64" rx="14" fill={inverted ? '#16a34a' : '#0f1a2e'} />
        <circle cx="32" cy="32" r="18" fill="none" stroke={inverted ? '#ffffff' : '#22c55e'} strokeWidth="4" />
        <path d="M32 14v36M14 32h36" stroke={inverted ? '#ffffff' : '#22c55e'} strokeWidth="4" />
        <circle cx="32" cy="32" r="5" fill="#f97316" />
      </svg>
      <span className="font-display text-xl font-bold uppercase leading-none tracking-wider">
        Sports<span className="text-highlight">Eco</span>
      </span>
    </span>
  )
}
