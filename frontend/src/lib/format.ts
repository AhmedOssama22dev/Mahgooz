/** Currency & date helpers — keep UI strings consistent */

export function formatEgp(amount: number): string {
  return `EGP ${amount.toLocaleString('en-EG')}`
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
