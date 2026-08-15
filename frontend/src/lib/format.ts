/** Currency & date helpers — keep UI strings consistent */

export function formatEgp(amount: number): string {
  return `EGP ${amount.toLocaleString('en-EG')}`
}

export function todayKey(timeZone = 'Africa/Cairo'): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date())
}

export function dateKey(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function parseSlotStart(date: string, time: string): Date {
  return new Date(`${date}T${time}:00`)
}

export function formatClock(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
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
