import { redirect } from '@tanstack/react-router'

import { getAccessToken, getSessionUser } from '@/lib/api/auth'

export function requireCustomer(from: string) {
  if (!getAccessToken()) {
    throw redirect({
      to: '/login',
      search: { redirect: from },
    })
  }
}

export function requireStaff(from: string) {
  if (!getAccessToken()) {
    throw redirect({
      to: '/login',
      search: { redirect: from },
    })
  }
  if (getSessionUser()?.role !== 'staff') {
    throw redirect({ to: '/' })
  }
}
