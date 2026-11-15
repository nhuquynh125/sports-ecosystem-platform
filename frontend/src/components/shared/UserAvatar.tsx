import { cn, initials } from '@/lib/utils'

export function UserAvatar({
  name,
  src,
  className,
}: {
  name: string
  src?: string | null
  className?: string
}) {
  return (
    <span
      className={cn(
        'inline-flex size-9 shrink-0 select-none items-center justify-center overflow-hidden rounded-full bg-primary/10 text-xs font-bold text-primary',
        className,
      )}
      aria-hidden
    >
      {src ? <img src={src} alt="" className="size-full object-cover" referrerPolicy="no-referrer" /> : initials(name)}
    </span>
  )
}
