import { Link } from '@tanstack/react-router'
import type { ReactNode } from 'react'

import { MahgouzLogo } from '@/components/mahgouz-logo'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type StaffShellProps = {
  children: ReactNode
  current?: 'lookup' | 'bookings'
  onLogout?: () => void
  className?: string
}

/** Staff chrome — light-first, no customer theme toggle. */
export function StaffShell({
  children,
  current = 'lookup',
  onLogout,
  className,
}: StaffShellProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className={cn('mx-auto flex min-h-screen max-w-6xl flex-col', className)}>
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-4 md:px-6">
          <Link to="/staff" className="flex items-center gap-2">
            <MahgouzLogo />
            <span className="text-sm text-muted-foreground">Staff</span>
          </Link>
          <nav className="flex items-center gap-1">
            <Button
              variant={current === 'lookup' ? 'secondary' : 'ghost'}
              size="sm"
              asChild
            >
              <Link to="/staff">Lookup</Link>
            </Button>
            <Button
              variant={current === 'bookings' ? 'secondary' : 'ghost'}
              size="sm"
              asChild
            >
              <Link to="/staff/bookings">Today&apos;s bookings</Link>
            </Button>
            {onLogout ? (
              <Button variant="ghost" size="sm" onClick={onLogout}>
                Log out
              </Button>
            ) : null}
          </nav>
        </header>
        <main className="flex flex-1 flex-col gap-6 px-4 py-6 md:px-6">{children}</main>
      </div>
    </div>
  )
}
