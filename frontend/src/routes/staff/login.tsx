import { createFileRoute, redirect, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'

import { MahgouzLogo } from '@/components/mahgouz-logo'
import { PinPad } from '@/components/pin-pad'
import { $api } from '@/lib/api/client'
import { getStaffToken, setStaffSession } from '@/lib/api/auth'

export const Route = createFileRoute('/staff/login')({
  beforeLoad: () => {
    if (getStaffToken()) {
      throw redirect({ to: '/staff/bookings' })
    }
  },
  component: StaffLoginPage,
})

function StaffLoginPage() {
  const navigate = useNavigate()
  const login = $api.useMutation('post', '/staff/login')
  const [error, setError] = useState(false)

  async function onSubmit(pin: string) {
    setError(false)
    try {
      const data = await login.mutateAsync({ body: { pin } })
      if (!data.access) {
        setError(true)
        return
      }
      setStaffSession(data.access)
      await navigate({ to: '/staff/bookings' })
    } catch {
      setError(true)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4 text-foreground">
      <div className="flex w-full max-w-[360px] flex-col items-center gap-8">
        <div className="flex flex-col items-center gap-1">
          <MahgouzLogo />
          <p className="text-sm text-muted-foreground">Staff</p>
        </div>
        <h1 className="font-display text-xl font-semibold">Enter PIN</h1>
        <PinPad error={error} onSubmit={(pin) => void onSubmit(pin)} />
      </div>
    </div>
  )
}
