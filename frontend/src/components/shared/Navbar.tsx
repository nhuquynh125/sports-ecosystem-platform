import { ChevronDown, LogOut, Menu, UserCircle } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { BrandLogo } from '@/components/shared/BrandLogo'
import { NotificationBell } from '@/components/shared/NotificationBell'
import { RoleBadge } from '@/components/shared/RoleBadge'
import { UserAvatar } from '@/components/shared/UserAvatar'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth } from '@/hooks/use-auth'

export function Navbar({ onMenuClick }: { onMenuClick: () => void }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-2 border-b bg-background/90 px-4 backdrop-blur lg:px-8">
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={onMenuClick}
        aria-label="Open menu"
        aria-controls="app-sidebar"
      >
        <Menu className="!size-5" aria-hidden />
      </Button>
      <Link to="/" className="lg:hidden" aria-label="Sports Ecosystem home">
        <BrandLogo />
      </Link>

      <div className="flex-1" />

      <NotificationBell />

      {user && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-auto gap-2 px-2 py-1.5">
              <UserAvatar name={user.full_name} src={user.avatar_url} />
              <span className="hidden text-left sm:block">
                <span className="block text-sm font-semibold leading-tight">{user.full_name}</span>
                <span className="block text-xs font-normal text-muted-foreground">@{user.username}</span>
              </span>
              <ChevronDown className="hidden text-muted-foreground sm:block" aria-hidden />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64">
            <DropdownMenuLabel className="space-y-1.5">
              <span className="block truncate">{user.full_name}</span>
              <span className="block truncate text-xs font-normal text-muted-foreground">{user.email}</span>
              <span className="flex flex-wrap gap-1 pt-0.5">
                {user.roles.map((role) => (
                  <RoleBadge key={role} role={role} />
                ))}
              </span>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={() => navigate('/profile')}>
              <UserCircle aria-hidden />
              My profile
            </DropdownMenuItem>
            <DropdownMenuItem onSelect={() => logout()} className="text-destructive focus:text-destructive">
              <LogOut aria-hidden />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </header>
  )
}
