import { formatHoldRemaining } from './format.ts'
import {
  apiStatusToUi,
  areConsecutiveHours,
  canTapSlot,
  periodFromHour,
  slotAriaLabel,
  staffKind,
  toggleConsecutiveHour,
} from './slot-states.ts'

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
check(
  staffKind({ ...paid, now: new Date('2026-08-20T10:00:00') }) === 'upcoming',
  'upcoming',
)
check(
  staffKind({ ...paid, now: new Date('2026-08-20T17:50:00') }) === 'ready',
  'ready window',
)
check(
  staffKind({ ...paid, now: new Date('2026-08-20T19:01:00') }) === 'no-show',
  'no-show',
)
check(
  staffKind({
    ...paid,
    status: 'redeemed',
    now: new Date('2026-08-20T19:01:00'),
  }) === 'redeemed',
  'redeemed wins over no-show',
)

check(apiStatusToUi('confirmed') === 'paid', 'confirmed maps to paid')
check(apiStatusToUi('held') === 'pending_payment', 'held maps to pending')

check(areConsecutiveHours(['18:00']) === true, 'one hour')
check(areConsecutiveHours(['18:00', '19:00']) === true, 'two adjacent')
check(areConsecutiveHours(['19:00', '18:00']) === true, 'unsorted adjacent')
check(areConsecutiveHours(['18:00', '20:00']) === false, 'gap')
check(
  toggleConsecutiveHour(['18:00'], '19:00').join() === '18:00,19:00',
  'extend',
)
check(toggleConsecutiveHour(['18:00'], '20:00').join() === '20:00', 'new block')
check(toggleConsecutiveHour(['18:00', '19:00'], '18:00').join() === '19:00', 'deselect')

check(formatHoldRemaining(0) === '0:00', 'zero hold')
check(formatHoldRemaining(9 * 60_000 + 42_000) === '9:42', '9:42 hold')
check(formatHoldRemaining(-1000) === '0:00', 'negative hold')

console.log('slot-states check ok')
