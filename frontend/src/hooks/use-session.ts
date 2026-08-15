import { useSyncExternalStore } from 'react'

import {
  getAccessToken,
  getCustomerUser,
  getStaffToken,
  sessionSnapshot,
  subscribeSession,
} from '@/lib/api/auth'
import type { CustomerUser } from '@/lib/api/auth'

export function useSession(): {
  loggedIn: boolean
  staffLoggedIn: boolean
  user: CustomerUser | undefined
} {
  const snap = useSyncExternalStore(
    subscribeSession,
    sessionSnapshot,
    () => '{}',
  )
  const parsed = JSON.parse(snap) as {
    access: string | null
    staff: string | null
    user: CustomerUser | null
  }
  return {
    loggedIn: Boolean(parsed.access ?? getAccessToken()),
    staffLoggedIn: Boolean(parsed.staff ?? getStaffToken()),
    user: parsed.user ?? getCustomerUser(),
  }
}
