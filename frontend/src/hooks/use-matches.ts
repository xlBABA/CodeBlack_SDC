import { useRequest } from '@/hooks/use-request'
import { api } from '@/lib/api'
import type { StoredProfile } from '@/lib/profile-store'
import type { APIEnvelope, MatchPayload } from '@/types/api'

// One match call per analysed profile, shared by the dashboard, roles and role pages.
const cache = new Map<string, Promise<APIEnvelope<MatchPayload>>>()

function matchOnce(stored: StoredProfile) {
  let hit = cache.get(stored.analyzed_at)
  if (!hit) {
    hit = api.matchCareers({ profile: stored.profile, limit: 6 })
    hit.catch(() => cache.delete(stored.analyzed_at))
    cache.set(stored.analyzed_at, hit)
  }
  return hit
}

/** POST /careers/match for the stored profile (the API caps the list at 6 roles). */
export function useMatches(stored: StoredProfile | null) {
  const [state, retry] = useRequest(stored && `match:${stored.analyzed_at}`, () => matchOnce(stored!))
  const retryFresh = () => {
    if (stored) cache.delete(stored.analyzed_at)
    retry()
  }
  return [state, retryFresh] as const
}
