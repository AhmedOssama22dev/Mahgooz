import { Link, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import type { ReactNode } from 'react'

import { AccountMenu } from '@/components/account-menu'
import { AppShell } from '@/components/app-shell'
import { CustomerBottomNav } from '@/components/customer-bottom-nav'
import { Button } from '@/components/ui/button'
import { useSession } from '@/hooks/use-session'
import { clearSession } from '@/lib/api/auth'

type CustomerLayoutProps = {
  children: ReactNode
  width?: 'narrow' | 'wide'
  footer?: ReactNode
  showBookCta?: boolean
  showBottomNav?: boolean
}

/** Auth-aware customer chrome: account menu, desktop nav, bottom tabs. */
export function CustomerLayout({
  children,
  width = 'narrow',
  footer,
  showBookCta = false,
  showBottomNav = true,
}: CustomerLayoutProps) {
  const { loggedIn, isStaff, user } = useSession()
  const [accountOpen, setAccountOpen] = useState(false)
  const navigate = useNavigate()

  function logout() {
    clearSession()
    setAccountOpen(false)
    void navigate({ to: '/' })
  }

  return (
    <>
      <AppShell
        width={width}
        footer={footer}
        bottomNav={
          loggedIn && showBottomNav ? (
            <CustomerBottomNav onAccount={() => setAccountOpen(true)} />
          ) : undefined
        }
        headerRight={
          <>
            {loggedIn ? (
              <Button
                variant="ghost"
                size="sm"
                className="hidden md:inline-flex"
                asChild
              >
                <Link to="/bookings">Bookings</Link>
              </Button>
            ) : null}
            {loggedIn ? (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setAccountOpen(true)}
              >
                {user?.name ?? 'Account'}
              </Button>
            ) : (
              <Button variant="link" className="text-primary" asChild>
                <Link to="/login">Log in</Link>
              </Button>
            )}
            {showBookCta ? (
              <Button className="hidden md:inline-flex" asChild>
                <Link to="/book">Book a court</Link>
              </Button>
            ) : null}
          </>
        }
      >
        {children}
      </AppShell>
      <AccountMenu
        name={user?.name}
        isStaff={isStaff}
        open={accountOpen}
        onOpenChange={setAccountOpen}
        onLogout={logout}
      />
    </>
  )
}
