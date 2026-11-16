import { Star, Swords } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { getErrorMessage } from '@/api/client'
import { useMyMatches, type PickupMatch } from '@/api/sporthub'
import { EmptyState } from '@/components/shared/EmptyState'
import { PageHeader } from '@/components/shared/PageHeader'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAuth } from '@/hooks/use-auth'
import { MatchCard } from './MatchCard'
import { RatePlayersModal } from './RatePlayersModal'

export function MyMatchesPage() {
  const { user } = useAuth()
  const meId = user?.id ?? 0
  const query = useMyMatches(user?.id)
  const [rating, setRating] = useState<PickupMatch | null>(null)

  const all = query.data ?? []
  const upcoming = all.filter((m) => m.status !== 'completed' && m.status !== 'cancelled')
  const finished = all.filter((m) => m.status === 'completed' || m.status === 'cancelled')

  function grid(items: PickupMatch[], empty: string) {
    if (items.length === 0) {
      return (
        <EmptyState
          icon={Swords}
          title={empty}
          action={<Button asChild><Link to="/matches">Find a match</Link></Button>}
        />
      )
    }
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {items.map((m) => (
          <MatchCard
            key={m.id}
            match={m}
            footer={
              <div className="flex items-center justify-between gap-2">
                <Badge variant={m.host_id === meId ? 'highlight' : 'secondary'}>{m.host_id === meId ? 'Hosting' : 'Joined'}</Badge>
                {m.status === 'completed' && (
                  <Button size="sm" variant="outline" onClick={() => setRating(m)}>
                    <Star aria-hidden />
                    Rate players
                  </Button>
                )}
              </div>
            }
          />
        ))}
      </div>
    )
  }

  return (
    <>
      <PageHeader
        title="My matches"
        description="Games you host or have joined."
        actions={<Button asChild><Link to="/matches/create">Create match</Link></Button>}
      />
      {query.isPending ? (
        <Skeleton className="h-64" />
      ) : query.isError ? (
        <EmptyState
          icon={Swords}
          title="Could not load your matches"
          description={getErrorMessage(query.error)}
          action={<Button variant="outline" onClick={() => void query.refetch()}>Try again</Button>}
        />
      ) : (
        <Tabs defaultValue="upcoming">
          <TabsList>
            <TabsTrigger value="upcoming">Upcoming ({upcoming.length})</TabsTrigger>
            <TabsTrigger value="past">Past ({finished.length})</TabsTrigger>
          </TabsList>
          <TabsContent value="upcoming">{grid(upcoming, 'No upcoming matches')}</TabsContent>
          <TabsContent value="past">{grid(finished, 'No past matches yet')}</TabsContent>
        </Tabs>
      )}
      <RatePlayersModal match={rating} meId={meId} onClose={() => setRating(null)} />
    </>
  )
}