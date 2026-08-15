/** Normalize staff pass schedule from flat fields or `slots[]` (live API). */

export type StaffPassSlot = {
  court?: { name?: string }
  date?: string
  start_time?: string
  end_time?: string
}

export type StaffPassScheduleInput = {
  court?: { name?: string }
  date?: string
  start_time?: string
  end_time?: string
  slots?: StaffPassSlot[]
}

export type StaffPassSchedule = {
  courtName: string
  date: string
  startTime: string
  endTime: string
}

export function staffPassSchedule(
  data: StaffPassScheduleInput,
): StaffPassSchedule | null {
  if (data.date && data.start_time) {
    return {
      courtName: data.court?.name ?? 'Court',
      date: data.date,
      startTime: data.start_time,
      endTime: data.end_time ?? '',
    }
  }

  const slots = data.slots ?? []
  const first = slots[0]
  const last = slots[slots.length - 1]
  if (!first?.date || !first.start_time) return null

  return {
    courtName: first.court?.name ?? data.court?.name ?? 'Court',
    date: first.date,
    startTime: first.start_time,
    endTime: last?.end_time ?? first.end_time ?? '',
  }
}
