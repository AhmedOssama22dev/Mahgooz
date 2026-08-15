import { addDays, startOfDay } from 'date-fns'
import { useMemo } from 'react'

import { Calendar } from '@/components/ui/calendar'
import { BOOK_AHEAD_DAYS } from '@/lib/slot-states'
import { cn } from '@/lib/utils'

type DateStripProps = {
  value?: Date
  onChange: (date: Date) => void
  days?: number
  className?: string
}

/** Month calendar — book today through `days` ahead. */
export function DateStrip({
  value,
  onChange,
  days = BOOK_AHEAD_DAYS,
  className,
}: DateStripProps) {
  const today = useMemo(() => startOfDay(new Date()), [])
  const selected = value ?? today

  return (
    <Calendar
      mode="single"
      selected={selected}
      onSelect={(date) => {
        if (!date) return
        onChange(startOfDay(date))
      }}
      disabled={{ before: today, after: addDays(today, days - 1) }}
      className={cn(
        'w-full rounded-[12px] border border-border bg-card',
        className,
      )}
      classNames={{ root: 'w-full' }}
    />
  )
}
