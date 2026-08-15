import { Link } from '@tanstack/react-router'

import { StatusBadge, staffKindToBadge } from '@/components/status-badge'
import { Button } from '@/components/ui/button'
import type { StaffBookingKind } from '@/lib/slot-states'
import { cn } from '@/lib/utils'

export type StaffFilter =
  | 'all'
  | 'court-1'
  | 'court-2'
  | 'paid'
  | 'redeemed'
  | 'no-show'

const FILTERS: { id: StaffFilter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'court-1', label: 'Court 1' },
  { id: 'court-2', label: 'Court 2' },
  { id: 'paid', label: 'Paid' },
  { id: 'redeemed', label: 'Redeemed' },
  { id: 'no-show', label: 'No-show' },
]

type FilterChipsProps = {
  value: StaffFilter
  onChange: (value: StaffFilter) => void
  className?: string
}

export function FilterChips({ value, onChange, className }: FilterChipsProps) {
  return (
    <div className={cn('-mx-1 flex gap-2 overflow-x-auto px-1 pb-1', className)}>
      {FILTERS.map((filter) => {
        const active = filter.id === value
        return (
          <button
            key={filter.id}
            type="button"
            onClick={() => onChange(filter.id)}
            aria-pressed={active}
            className={cn(
              'min-h-11 shrink-0 rounded-full border px-4 text-sm font-medium',
              active
                ? 'border-court-green bg-court-green text-white'
                : 'border-border bg-card text-foreground',
            )}
          >
            {filter.label}
          </button>
        )
      })}
    </div>
  )
}

type StatsRowProps = {
  booked: number
  checkedIn: number
  upcoming: number
  noShow: number
  className?: string
}

export function StatsRow({
  booked,
  checkedIn,
  upcoming,
  noShow,
  className,
}: StatsRowProps) {
  return (
    <p className={cn('text-sm text-muted-foreground', className)}>
      <span className="tabular-nums text-foreground">{booked}</span> booked
      {' · '}
      <span className="tabular-nums text-foreground">{checkedIn}</span> checked in
      {' · '}
      <span className="tabular-nums text-foreground">{upcoming}</span> upcoming
      {' · '}
      <span className="tabular-nums text-foreground">{noShow}</span> no-show
    </p>
  )
}

type ArrivalCardProps = {
  time: string
  courtName: string
  code: string
  kind: StaffBookingKind
  className?: string
}

export function ArrivalCard({
  time,
  courtName,
  code,
  kind,
  className,
}: ArrivalCardProps) {
  return (
    <article
      className={cn(
        'flex items-center justify-between gap-3 rounded-[12px] border border-border bg-card p-4',
        className,
      )}
    >
      <div>
        <p className="font-display font-semibold">
          {time} {courtName} · {code}
        </p>
        <div className="mt-2">
          <StatusBadge
            status={staffKindToBadge(kind)}
            label={kind === 'ready' ? 'Paid · not redeemed' : undefined}
          />
        </div>
      </div>
      <Button variant="outline" size="sm" asChild>
        <Link to="/staff/pass/$code" params={{ code }}>
          View
        </Link>
      </Button>
    </article>
  )
}

type RedeemButtonProps = {
  redeemed?: boolean
  redeemedAt?: string
  onRedeem?: () => void
  className?: string
}

export function RedeemButton({
  redeemed = false,
  redeemedAt,
  onRedeem,
  className,
}: RedeemButtonProps) {
  return (
    <div className={cn('flex flex-col gap-2', className)}>
      <Button
        type="button"
        className="min-h-14 w-full text-base tracking-wide uppercase"
        disabled={redeemed}
        onClick={onRedeem}
      >
        {redeemed ? 'Already checked in' : 'Redeem check-in'}
      </Button>
      {redeemed && redeemedAt ? (
        <p className="text-center text-sm text-muted-foreground">
          Redeemed at {redeemedAt}
        </p>
      ) : (
        <p className="text-center text-sm text-muted-foreground">
          Redeeming marks this pass as used. Cannot undo.
        </p>
      )}
    </div>
  )
}
