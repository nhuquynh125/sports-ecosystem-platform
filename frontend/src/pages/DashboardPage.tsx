import { ArrowRight, CalendarClock, ShieldCheck, UserCircle } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useMyProfiles } from '@/api/profiles'
import { PageHeader } from '@/components/shared/PageHeader'
import { RoleBadge } from '@/components/shared/RoleBadge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/hooks/use-auth'

function ActionCard({ to, icon: Icon, title, description }: { to: string; icon: LucideIcon; title: string; description: string }) {
  return (
    <Link to={to} className="group block rounded-lg">
      <Card className="h-full transition-shadow group-hover:shadow-lg">
        <CardHeader>
          <span className="mb-1 flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Icon className="size-5" aria-hidden />
          </span>
          <CardTitle className="flex items-center justify-between">
            {title}
            <ArrowRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-1" aria-hidden />
          </CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
      </Card>
    </Link>
  )
}

export function DashboardPage() {
  const { user, hasRole } = useAuth()
  const isPlayer = hasRole('player')
  const profiles = useMyProfiles(isPlayer)

  if (!user) return null

  return (
    <>
      <PageHeader title={`Hey, ${user.full_name.split(' ').slice(-1)[0]}`} description="Here's where to pick up your game." />

      <div className="mb-6 flex flex-wrap items-center gap-2">
        <span className="text-sm text-muted-foreground">Signed in as</span>
        {user.roles.map((role) => (
          <RoleBadge key={role} role={role} />
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <ActionCard to="/profile" icon={UserCircle} title="My profile" description="Update your account details and password." />
        {isPlayer && (
          <ActionCard
            to="/profile?tab=players"
            icon={UserCircle}
            title="Sport profiles"
            description={
              profiles.data
                ? profiles.data.length === 0
                  ? 'Create your first profile so others can find you.'
                  : `You have ${profiles.data.length} sport profile${profiles.data.length === 1 ? '' : 's'}.`
                : 'Positions, skill levels and where you play.'
            }
          />
        )}
        {isPlayer && (
          <ActionCard to="/profile?tab=availability" icon={CalendarClock} title="Weekly availability" description="Tell others when you're free to play." />
        )}
        {hasRole('admin') && (
          <ActionCard to="/admin/users" icon={ShieldCheck} title="Manage users" description="Search, lock or unlock accounts and edit roles." />
        )}
      </div>

      <Card className="mt-8 bg-accent/40 shadow-none">
        <CardContent className="p-5 text-sm text-accent-foreground">
          Courts, teams, tournaments and scouting arrive in the next steps. They already appear, greyed out, in the sidebar for the roles that will use them.
        </CardContent>
      </Card>
    </>
  )
}
