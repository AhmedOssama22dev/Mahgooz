import { formatHoldRemaining } from './format.ts'
import { canTapSlot, periodFromHour, slotAriaLabel, staffKind } from './slot-states.ts'

function check(cond: unknown, msg: string) {
  if (!cond) throw new Error(msg)
}

check(canTapSlot('available') === true, 'available is tappable')
check(canTapSlot('selected') === true, 'selected is tappable')
check(canTapSlot('held') === false, 'held is not tappable')
check(canTapSlot('booked') === false, 'booked is not tappable')

check(periodFromHour(8) === 'morning', '8 is morning')
check(periodFromHour(12) === 'afternoon', '12 is afternoon')
check(periodFromHour(17) === 'evening', '17 is evening')

check(slotAriaLabel('18:00', 'held').includes('checking out'), 'held label')

const paid = {
  status: 'paid' as const,
  slotStart: new Date('2026-08-20T18:00:00'),
  slotEnd: new Date('2026-08-20T19:00:00'),
}
check(staffKind({ ...paid, now: new Date('2026-08-20T10:00:00') }) === 'upcoming', 'upcoming')
check(staffKind({ ...paid, now: new Date('2026-08-20T17:50:00') }) === 'ready', 'ready window')
check(staffKind({ ...paid, now: new Date('2026-08-20T19:01:00') }) === 'no-show', 'no-show')
check(
  staffKind({ ...paid, status: 'redeemed', now: new Date('2026-08-20T19:01:00') }) ===
    'redeemed',
  'redeemed wins over no-show',
)

check(formatHoldRemaining(0) === '0:00', 'zero hold')
check(formatHoldRemaining(9 * 60_000 + 42_000) === '9:42', '9:42 hold')
check(formatHoldRemaining(-1000) === '0:00', 'negative hold')

console.log('slot-states check ok')
