import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export type StatusKind =
  | 'ready'
  | 'checked-in'
  | 'morning'
  | 'pending'
  | 'failed'
  | 'expired'

const statusStyles: Record<StatusKind, string> = {
  ready:
    'border-transparent bg-court-green-light text-court-green-dark dark:bg-[rgba(27,122,78,0.18)] dark:text-court-green',
  'checked-in':
    'border-transparent bg-[#E8EAEC] text-redeemed dark:bg-[#1E2A24]',
  morning:
    'border-transparent bg-clay-orange-light text-clay-orange dark:bg-[rgba(232,106,42,0.12)]',
  pending:
    'border-transparent bg-[#FFF3CD] text-[#856404] dark:bg-[rgba(133,100,4,0.22)] dark:text-[#D4A843]',
  failed: 'border-transparent bg-destructive/10 text-destructive',
  expired: 'border-transparent bg-muted text-muted-foreground',
}

const statusLabels: Record<StatusKind, string> = {
  ready: 'Ready to play',
  'checked-in': 'Checked in',
  morning: 'Morning deal',
  pending: 'Pending',
  failed: 'Failed',
  expired: 'Expired',
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
