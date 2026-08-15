import type { ButtonHTMLAttributes } from 'react'

import { canTapSlot, slotAriaLabel, type SlotState } from '@/lib/slot-states'
import { cn } from '@/lib/utils'

export type { SlotState }

const slotStyles: Record<SlotState, string> = {
  available:
    'border-court-green bg-slot-available text-foreground hover:bg-court-green hover:text-white',
  selected: 'border-transparent bg-court-green text-white',
  held: 'cursor-not-allowed border-transparent bg-slot-held text-slot-held-text',
  booked:
    'cursor-not-allowed border-transparent bg-slot-booked text-muted-foreground',
}

type SlotChipProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  state?: SlotState
  time: string
}

/** Booking time chip — states from branding.md */
export function SlotChip({
  state = 'available',
  time,
  className,
  disabled,
  ...props
}: SlotChipProps) {
  const locked = !canTapSlot(state)
  return (
    <button
      type="button"
      disabled={disabled ?? locked}
      aria-pressed={state === 'selected'}
      aria-label={slotAriaLabel(time, state)}
      className={cn(
        'min-h-11 min-w-[4.5rem] rounded-[8px] border px-3 py-2 text-sm font-medium tabular-nums transition-colors focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none',
        slotStyles[state],
        className,
      )}
      {...props}
    >
      {time}
    </button>
  )
}
