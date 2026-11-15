import { useSearchParams } from 'react-router-dom'
import { PageHeader } from '@/components/shared/PageHeader'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AccountTab } from './profile/AccountTab'
import { AvailabilityTab } from './profile/AvailabilityTab'
import { PlayerProfilesTab } from './profile/PlayerProfilesTab'

const TABS = ['account', 'players', 'availability'] as const
type Tab = (typeof TABS)[number]

export function ProfilePage() {
  const [params, setParams] = useSearchParams()
  const requested = params.get('tab')
  const tab: Tab = TABS.includes(requested as Tab) ? (requested as Tab) : 'account'

  function setTab(next: string) {
    setParams(next === 'account' ? {} : { tab: next }, { replace: true })
  }

  return (
    <>
      <PageHeader title="My profile" description="Manage your account, your sport profiles and when you're free to play." />
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="h-auto w-full justify-start overflow-x-auto sm:w-auto">
          <TabsTrigger value="account">Account</TabsTrigger>
          <TabsTrigger value="players">Player profiles</TabsTrigger>
          <TabsTrigger value="availability">Availability</TabsTrigger>
        </TabsList>
        <TabsContent value="account">
          <AccountTab />
        </TabsContent>
        <TabsContent value="players">
          <PlayerProfilesTab />
        </TabsContent>
        <TabsContent value="availability">
          <AvailabilityTab onGoToProfiles={() => setTab('players')} />
        </TabsContent>
      </Tabs>
    </>
  )
}
