import { useSyncExternalStore } from 'react'

import {
  getAccessToken,
  getSessionUser,
  sessionSnapshot,
  subscribeSession,
} from '@/lib/api/auth'
import type { AuthUser } from '@/lib/api/auth'

export function useSession(): {
  loggedIn: boolean
  isStaff: boolean
  user: AuthUser | undefined
} {
  const snap = useSyncExternalStore(
    subscribeSession,
    sessionSnapshot,
    () => '{}',
  )
  const parsed = JSON.parse(snap) as {
    access: string | null
    user: AuthUser | null
  }
  const user = parsed.user ?? getSessionUser()
  return {
    loggedIn: Boolean(parsed.access ?? getAccessToken()),
    isStaff: user?.role === 'staff',
    user,
  }
}
