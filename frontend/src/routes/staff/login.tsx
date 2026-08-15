import { createFileRoute, redirect } from '@tanstack/react-router'

import { getAccessToken, getSessionUser } from '@/lib/api/auth'

export const Route = createFileRoute('/staff/login')({
  beforeLoad: () => {
    if (getAccessToken() && getSessionUser()?.role === 'staff') {
      throw redirect({ to: '/staff/bookings' })
    }
    throw redirect({
      to: '/login',
      search: { redirect: '/staff/bookings' },
    })
  },
  component: () => null,
})
