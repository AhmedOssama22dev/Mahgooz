import { redirect } from '@tanstack/react-router'

import { getAccessToken, getStaffToken } from '@/lib/api/auth'

export function requireCustomer(from: string) {
  if (!getAccessToken()) {
    throw redirect({
      to: '/login',
      search: { redirect: from },
    })
  }
}

export function requireStaff() {
  if (!getStaffToken()) {
    throw redirect({ to: '/staff/login' })
  }
}
