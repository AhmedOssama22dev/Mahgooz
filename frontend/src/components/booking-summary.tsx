import { formatBookingDay, formatEgp, formatSlotRange } from '@/lib/format'
import { cn } from '@/lib/utils'

type BookingSummaryProps = {
  courtName: string
  start: Date
  end: Date
  amount: number
  playerName?: string
  phone?: string
  className?: string
}

export function BookingSummary({
  courtName,
  start,
  end,
  amount,
  playerName,
  phone,
  className,
}: BookingSummaryProps) {
  const hours = Math.max(1, Math.round((end.getTime() - start.getTime()) / 3_600_000))

  return (
    <div className={cn('flex flex-col gap-4 rounded-[12px] border border-border bg-card p-4', className)}>
      <div>
        <p className="text-sm text-muted-foreground">Your booking</p>
        <p className="mt-1 font-display text-lg font-semibold">{courtName}</p>
        <p className="mt-1 text-sm text-foreground">
          {formatBookingDay(start)} · {formatSlotRange(start, end)}
        </p>
        <p className="text-sm text-muted-foreground">
          {hours} {hours === 1 ? 'hour' : 'hours'}
        </p>
      </div>
      <div className="flex items-center justify-between border-t border-border pt-4">
        <span className="text-sm text-muted-foreground">Total</span>
        <span className="font-medium tabular-nums">{formatEgp(amount)}</span>
      </div>
      {playerName || phone ? (
        <div className="text-sm">
          {playerName ? <p>{playerName}</p> : null}
          {phone ? <p className="text-muted-foreground">{phone}</p> : null}
        </div>
      ) : null}
    </div>
  )
}
