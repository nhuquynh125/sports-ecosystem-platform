import { ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'
import { EmptyState } from '@/components/shared/EmptyState'
import { Button } from '@/components/ui/button'

export function ForbiddenPage() {
  return (
    <div className="mx-auto max-w-lg py-16">
      <EmptyState
        icon={ShieldAlert}
        title="403 · Access denied"
        description="Your account doesn't have the role required to view this page."
        action={
          <Button asChild>
            <Link to="/">Back to dashboard</Link>
          </Button>
        }
      />
    </div>
  )
}
