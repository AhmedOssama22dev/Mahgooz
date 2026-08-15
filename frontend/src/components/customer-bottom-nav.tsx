import { Link, useRouterState } from '@tanstack/react-router'
import { Calendar, Home, Ticket, User } from 'lucide-react'

import { cn } from '@/lib/utils'

const TABS = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/book', label: 'Book', icon: Calendar },
  { to: '/bookings', label: 'My bookings', icon: Ticket },
] as const

type CustomerBottomNavProps = {
  onAccount?: () => void
  className?: string
}

/** Fixed tab bar on logged-in customer pages. */
export function CustomerBottomNav({ onAccount, className }: CustomerBottomNavProps) {
  const pathname = useRouterState({ select: (s) => s.location.pathname })

  return (
    <nav
      className={cn(
        'sticky bottom-0 z-30 border-t border-border bg-card pb-[env(safe-area-inset-bottom)]',
        className,
      )}
      aria-label="Customer"
    >
      <ul className="grid grid-cols-4">
        {TABS.map(({ to, label, icon: Icon }) => {
          const active =
            to === '/'
              ? pathname === '/'
              : pathname === to || pathname.startsWith(`${to}/`)
          return (
            <li key={to}>
              <Link
                to={to}
                className={cn(
                  'flex min-h-14 flex-col items-center justify-center gap-1 text-xs',
                  active ? 'text-court-green' : 'text-muted-foreground',
                )}
              >
                <Icon className="size-5" aria-hidden />
                {label}
              </Link>
            </li>
          )
        })}
        <li>
          <button
            type="button"
            onClick={onAccount}
            className="flex min-h-14 w-full flex-col items-center justify-center gap-1 text-xs text-muted-foreground"
          >
            <User className="size-5" aria-hidden />
            Account
          </button>
        </li>
      </ul>
    </nav>
  )
}
