import { Plus, Swords } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { getErrorMessage } from '@/api/client'
import { useMatches } from '@/api/sporthub'
import { useSports } from '@/api/sports'
import { SKILL_LEVELS } from '@/api/types'
import { EmptyState } from '@/components/shared/EmptyState'
import { PageHeader } from '@/components/shared/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { MatchCard } from './MatchCard'

export function MatchesPage() {
  const sports = useSports()
  const [sportId, setSportId] = useState('')
  const [skill, setSkill] = useState('')
  const [date, setDate] = useState('')
  const [areaInput, setAreaInput] = useState('')
  const [area, setArea] = useState('')
  const debounce = useRef<number | undefined>(undefined)
  useEffect(() => () => window.clearTimeout(debounce.current), [])

  const query = useMatches({
    sport_id: sportId ? Number(sportId) : undefined,
    area: area || undefined,
    skill_level: skill || undefined,
    match_date: date || undefined,
  })
  const items = query.data ?? []

  return (
    <>
      <PageHeader
        title="Find a match"
        description="Open pickup games near you. Join one or host your own."
        actions={
          <>
            <Button asChild variant="outline">
              <Link to="/matches/me">My matches</Link>
            </Button>
            <Button asChild>
              <Link to="/matches/create">
                <Plus aria-hidden />
                Create match
              </Link>
            </Button>
          </>
        }
      />

      <div className="mb-6 flex flex-wrap gap-3">
        <Select value={sportId} onChange={(e) => setSportId(e.target.value)} aria-label="Filter by sport" className="w-[160px]">
          <option value="">All sports</option>
          {(sports.data ?? []).map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </Select>
        <Select value={skill} onChange={(e) => setSkill(e.target.value)} aria-label="Filter by skill level" className="w-[160px]">
          <option value="">Any level</option>
          {SKILL_LEVELS.map((l) => (
            <option key={l} value={l} className="capitalize">
              {l}
            </option>
          ))}
        </Select>
        <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} aria-label="Filter by date" className="w-[170px]" />
        <Input
          type="search"
          value={areaInput}
          placeholder="Area, e.g. Hải Châu"
          aria-label="Filter by area"
          className="w-[210px]"
          onChange={(e) => {
            setAreaInput(e.target.value)
            window.clearTimeout(debounce.current)
            debounce.current = window.setTimeout(() => setArea(e.target.value.trim()), 350)
          }}
        />
      </div>

      {query.isPending ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-44" />
          ))}
        </div>
      ) : query.isError ? (
        <EmptyState
          icon={Swords}
          title="Could not load matches"
          description={getErrorMessage(query.error)}
          action={<Button variant="outline" onClick={() => void query.refetch()}>Try again</Button>}
        />
      ) : items.length === 0 ? (
        <EmptyState
          icon={Swords}
          title="No matches found"
          description="Try different filters, or host the first game."
          action={<Button asChild><Link to="/matches/create">Create match</Link></Button>}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map((m) => (
            <MatchCard key={m.id} match={m} />
          ))}
        </div>
      )}
    </>
  )
}