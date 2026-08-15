/** Slot + booking states the UI must reflect. Held is never bookable. */

export type SlotState = 'available' | 'held' | 'booked' | 'selected'

export type Period = 'morning' | 'afternoon' | 'evening'

export type BookingStatus =
  | 'pending_payment'
  | 'paid'
  | 'redeemed'
  | 'expired'
  | 'cancelled'
  | 'failed'

export type StaffBookingKind =
  | 'ready'
  | 'upcoming'
  | 'redeemed'
  | 'no-show'
  | 'expired'

export const HOLD_TTL_MS = 10 * 60 * 1000
export const POLL_INTERVAL_MS = 2_000
export const POLL_TIMEOUT_MS = 60_000
export const BOOK_AHEAD_DAYS = 14
export const SLOT_MINUTES = 60
export const OPERATING_HOURS = { start: 8, end: 22 } as const

export const PERIOD_META: Record<
  Period,
  { label: string; startHour: number; endHour: number }
> = {
  morning: { label: 'Morning', startHour: 8, endHour: 12 },
  afternoon: { label: 'Afternoon', startHour: 12, endHour: 17 },
  evening: { label: 'Evening', startHour: 17, endHour: 22 },
}

export function canTapSlot(state: SlotState): boolean {
  return state === 'available' || state === 'selected'
}

export function slotAriaLabel(time: string, state: SlotState): string {
  if (state === 'held') return `${time}, someone is checking out`
  if (state === 'booked') return `${time}, booked`
  if (state === 'selected') return `${time}, selected`
  return time
}

export function periodFromHour(hour: number): Period {
  if (hour < PERIOD_META.afternoon.startHour) return 'morning'
  if (hour < PERIOD_META.evening.startHour) return 'afternoon'
  return 'evening'
}

/** Staff row kind. No-show is UI-only: paid + past slot end. */
export function staffKind(args: {
  status: BookingStatus
  slotStart: Date
  slotEnd: Date
  now: Date
}): StaffBookingKind {
  if (args.status === 'redeemed') return 'redeemed'
  if (args.status === 'expired' || args.status === 'cancelled' || args.status === 'failed') {
    return 'expired'
  }
  if (args.status === 'paid' && args.now > args.slotEnd) return 'no-show'
  const readyFrom = new Date(args.slotStart.getTime() - 15 * 60 * 1000)
  if (args.status === 'paid' && args.now >= readyFrom) return 'ready'
  return 'upcoming'
}
