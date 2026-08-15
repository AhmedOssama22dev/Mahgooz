import type { ButtonHTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

export type SlotState = 'available' | 'held' | 'booked' | 'selected'

const slotStyles: Record<SlotState, string> = {
  available:
    'border-court-green bg-court-green-light text-foreground dark:bg-[rgba(27,122,78,0.18)] hover:bg-court-green hover:text-white',
  selected: 'border-transparent bg-court-green text-white',
  held: 'cursor-not-allowed border-transparent bg-[#FFF3CD] text-[#856404] dark:bg-[rgba(133,100,4,0.22)] dark:text-[#D4A843]',
  booked:
    'cursor-not-allowed border-transparent bg-[#E8EAEC] text-muted-foreground dark:bg-[#1E2A24]',
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
  const locked = state === 'held' || state === 'booked'
  return (
    <button
      type="button"
      disabled={disabled ?? locked}
      className={cn(
        'min-h-11 min-w-[4.5rem] rounded-[8px] border px-3 py-2 text-sm font-medium tabular-nums transition-colors',
        slotStyles[state],
        className,
      )}
      {...props}
    >
      {time}
    </button>
  )
}
