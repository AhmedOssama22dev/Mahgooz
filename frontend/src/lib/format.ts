/** Currency & date helpers — keep UI strings consistent */

export function formatEgp(amount: number): string {
  return `EGP ${amount.toLocaleString('en-EG')}`
}

/** Hold countdown `m:ss` (never negative). */
export function formatHoldRemaining(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000))
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function formatSlotRange(start: Date, end: Date): string {
  const opts: Intl.DateTimeFormatOptions = {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }
  return `${start.toLocaleTimeString('en-GB', opts)}–${end.toLocaleTimeString('en-GB', opts)}`
}

export function formatBookingDay(date: Date): string {
  return date.toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  })
}
