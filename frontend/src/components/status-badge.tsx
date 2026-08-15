import { Badge } from '@/components/ui/badge'
import type { BookingStatus, StaffBookingKind } from '@/lib/slot-states'
import { cn } from '@/lib/utils'

export type StatusKind =
  | 'ready'
  | 'upcoming'
  | 'checked-in'
  | 'morning'
  | 'pending'
  | 'failed'
  | 'cancelled'
  | 'expired'
  | 'no-show'

const statusStyles: Record<StatusKind, string> = {
  ready:
    'border-transparent bg-slot-available text-court-green-dark dark:text-court-green',
  upcoming:
    'border-slot-held-text/40 bg-slot-held text-slot-held-text',
  'checked-in':
    'border-transparent bg-slot-booked text-redeemed',
  morning:
    'border-transparent bg-clay-orange-light text-clay-orange dark:bg-[rgba(232,106,42,0.12)]',
  pending: 'border-transparent bg-slot-held text-slot-held-text',
  failed: 'border-transparent bg-destructive/10 text-destructive',
  cancelled: 'border-transparent bg-destructive/10 text-destructive',
  expired: 'border-transparent bg-muted text-muted-foreground',
  'no-show':
    'border-transparent bg-[rgba(232,106,42,0.12)] text-clay-orange',
}

const statusLabels: Record<StatusKind, string> = {
  ready: 'Ready to play',
  upcoming: 'Upcoming',
  'checked-in': 'Checked in',
  morning: 'Morning deal',
  pending: 'Confirming…',
  failed: 'Failed',
  cancelled: 'Cancelled',
  expired: 'Past',
  'no-show': 'No-show risk',
}

export function bookingStatusToKind(status: BookingStatus): StatusKind {
  switch (status) {
    case 'paid':
      return 'ready'
    case 'redeemed':
      return 'checked-in'
    case 'pending_payment':
      return 'pending'
    case 'failed':
      return 'failed'
    case 'cancelled':
      return 'cancelled'
    case 'expired':
      return 'expired'
  }
}

export function staffKindToBadge(kind: StaffBookingKind): StatusKind {
  switch (kind) {
    case 'ready':
      return 'ready'
    case 'upcoming':
      return 'upcoming'
    case 'redeemed':
      return 'checked-in'
    case 'no-show':
      return 'no-show'
    case 'expired':
      return 'expired'
  }
}

type StatusBadgeProps = {
  status: StatusKind
  label?: string
  className?: string
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  return (
    <Badge
      className={cn(
        'rounded-[8px] px-2.5 py-1 text-xs font-medium',
        statusStyles[status],
        className,
      )}
    >
      {label ?? statusLabels[status]}
    </Badge>
  )
}
