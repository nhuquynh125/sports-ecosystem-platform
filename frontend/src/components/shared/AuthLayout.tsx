import { CalendarCheck, LineChart, Trophy } from 'lucide-react'
import type { ReactNode } from 'react'
import { BrandLogo } from '@/components/shared/BrandLogo'

const HIGHLIGHTS = [
  { icon: CalendarCheck, text: 'Book courts with zero double-bookings' },
  { icon: Trophy, text: 'Build a team and enter tournaments' },
  { icon: LineChart, text: 'Track your rating and get scouted' },
]

export function AuthLayout({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
      <aside className="relative hidden overflow-hidden bg-sidebar p-12 text-sidebar-foreground lg:flex lg:flex-col lg:justify-between">
        <svg className="pointer-events-none absolute -bottom-24 -right-24 size-[28rem] text-primary/20" viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="1.2" aria-hidden>
          <circle cx="50" cy="50" r="40" />
          <circle cx="50" cy="50" r="8" />
          <path d="M50 10v80M10 50h80" />
          <rect x="22" y="22" width="56" height="56" rx="2" />
        </svg>
        <BrandLogo inverted />
        <div className="relative max-w-md">
          <h2 className="text-5xl font-bold uppercase leading-[1.05] tracking-wide">
            Your whole game,
            <br />
            <span className="text-highlight">one platform.</span>
          </h2>
          <ul className="mt-8 space-y-4">
            {HIGHLIGHTS.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-sidebar-foreground/90">
                <span className="flex size-9 items-center justify-center rounded-full bg-primary/25 text-primary-foreground">
                  <Icon className="size-[18px]" aria-hidden />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-xs text-sidebar-muted">Sports Ecosystem &amp; AI Platform · Đồ án Cơ sở 2</p>
      </aside>

      <main className="flex items-center justify-center px-4 py-10 sm:px-8">
        <div className="w-full max-w-md">
          <BrandLogo className="mb-8 lg:hidden" />
          <h1 className="text-4xl font-semibold uppercase tracking-wide">{title}</h1>
          <p className="mb-7 mt-1 text-sm text-muted-foreground">{subtitle}</p>
          {children}
        </div>
      </main>
    </div>
  )
}
