import { addDays, format, isSameDay, startOfDay } from 'date-fns'
import { useMemo, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import { BOOK_AHEAD_DAYS } from '@/lib/slot-states'
import { cn } from '@/lib/utils'

type DateStripProps = {
  value?: Date
  onChange: (date: Date) => void
  /** Days ahead from today (spec: 14) */
  days?: number
  className?: string
}

/** Horizontal 14-day strip + optional month calendar in a sheet */
export function DateStrip({
  value,
  onChange,
  days = BOOK_AHEAD_DAYS,
  className,
}: DateStripProps) {
  const today = useMemo(() => startOfDay(new Date()), [])
  const range = useMemo(
    () => Array.from({ length: days }, (_, i) => addDays(today, i)),
    [days, today],
  )
  const [open, setOpen] = useState(false)
  const selected = value ?? today

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      <div className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1">
        {range.map((day) => {
          const active = isSameDay(day, selected)
          return (
            <button
              key={day.toISOString()}
              type="button"
              onClick={() => onChange(day)}
              className={cn(
                'flex min-h-14 min-w-14 shrink-0 flex-col items-center justify-center rounded-[12px] border px-2 py-2 text-center transition-colors focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none',
                active
                  ? 'border-court-green bg-court-green text-white'
                  : 'border-border bg-card text-foreground hover:border-court-green/40',
              )}
            >
              <span className="text-[11px] font-medium opacity-80">
                {format(day, 'EEE')}
              </span>
              <span className="font-display text-base font-semibold tabular-nums">
                {format(day, 'd')}
              </span>
            </button>
          )
        })}
      </div>

      <p className="text-sm text-muted-foreground">Book up to {days} days ahead</p>

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button variant="outline" className="w-full">
            Open calendar
          </Button>
        </SheetTrigger>
        <SheetContent side="bottom" className="rounded-t-[16px]">
          <SheetHeader>
            <SheetTitle className="font-display">Pick a date</SheetTitle>
          </SheetHeader>
          <div className="flex justify-center pb-6">
            <Calendar
              mode="single"
              selected={selected}
              onSelect={(date) => {
                if (!date) return
                onChange(startOfDay(date))
                setOpen(false)
              }}
              disabled={{ before: today, after: addDays(today, days - 1) }}
              className="rounded-[12px]"
            />
          </div>
        </SheetContent>
      </Sheet>
    </div>
  )
}
