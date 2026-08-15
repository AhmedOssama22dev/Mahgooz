import { Link } from '@tanstack/react-router'
import type { ReactNode } from 'react'

import { StatusBadge, bookingStatusToKind } from '@/components/status-badge'
import { Button } from '@/components/ui/button'
import { formatBookingDay, formatEgp } from '@/lib/format'
import type { BookingStatus } from '@/lib/slot-states'
import { cn } from '@/lib/utils'

type BookingCardProps = {
  courtName: string
  start: Date
  amount?: number
  status: BookingStatus
  morningDeal?: boolean
  code?: string
  action?: ReactNode
  className?: string
}

export function BookingCard({
  courtName,
  start,
  amount,
  status,
  morningDeal,
  code,
  action,
  className,
}: BookingCardProps) {
  const kind = bookingStatusToKind(status)
  const canViewPass =
    Boolean(code) &&
    (status === 'paid' || status === 'redeemed' || status === 'expired')
  const bookAgain = status === 'cancelled' || status === 'failed'

  return (
    <article
      className={cn(
        'flex flex-col gap-3 rounded-[12px] border border-border bg-card p-4 shadow-[0_1px_3px_rgba(15,26,20,0.06)] dark:shadow-none',
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-display text-[17px] font-semibold">
            {formatBookingDay(start)}
            {' · '}
            {start.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false })}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">{courtName}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <StatusBadge status={kind} />
          {morningDeal ? <StatusBadge status="morning" /> : null}
        </div>
      </div>
      {amount != null ? (
        <p className="text-sm tabular-nums text-foreground">{formatEgp(amount)}</p>
      ) : null}
      {action}
      {!action && canViewPass && code ? (
        <Button variant="outline" className="w-full" asChild>
          <Link to="/pass/$code" params={{ code }}>
            {status === 'paid' ? 'View pass →' : 'View'}
          </Link>
        </Button>
      ) : null}
      {!action && bookAgain ? (
        <Button className="w-full" asChild>
          <Link to="/book">Book again</Link>
        </Button>
      ) : null}
    </article>
  )
}
