import { handleMock, resetMock } from './mock.ts'

function check(cond: unknown, msg: string) {
  if (!cond) throw new Error(msg)
}

function call(
  method: string,
  path: string,
  opts?: { query?: string; body?: unknown; authorization?: string },
) {
  return handleMock({
    method,
    path,
    query: new URLSearchParams(opts?.query),
    body: opts?.body,
    authorization: opts?.authorization,
  })
}

resetMock()

check(call('GET', '/health').body, 'health')
const courts = call('GET', '/courts').body as Array<{ id: string }>
check(courts.length === 2, 'two courts')

const slots = call('GET', '/slots', {
  query: `date=2026-08-21&court_id=${courts[0]!.id}`,
}).body as { slots: Array<{ state: string }> }
check(slots.slots.length === 14, '08:00–22:00 grid')
check(
  slots.slots.every((s) => s.state === 'available'),
  'empty day is all available',
)

const authed = { authorization: 'Bearer test' }
check(call('GET', '/auth/me').status === 401, 'me requires jwt')
check(
  call('POST', '/auth/login', { body: { phone: '01012345678' } }).status ===
    200,
  'login',
)
check(call('GET', '/auth/me', authed).status === 200, 'me with jwt')

const hold = call('POST', '/bookings/hold', {
  ...authed,
  body: {
    court_id: courts[0]!.id,
    date: '2026-08-21',
    start_times: ['18:00'],
    attendee_names: ['Ahmed Hassan'],
  },
})
check(hold.status === 201, 'hold created')
const held = hold.body as {
  id: string
  status: string
  start_times: string[]
  end_time: string
  price_egp: number
}
check(held.status === 'held', 'hold status')
check(held.start_times.join() === '18:00', 'one start')
check(held.end_time === '19:00', 'one-hour end')

const taken = call('POST', '/bookings/hold', {
  ...authed,
  body: { court_id: courts[0]!.id, date: '2026-08-21', start_times: ['18:00'] },
})
check(taken.status === 409, 'second hold is slot taken')

const two = call('POST', '/bookings/hold', {
  ...authed,
  body: {
    court_id: courts[0]!.id,
    date: '2026-08-21',
    start_times: ['20:00', '21:00'],
    attendee_names: ['Ahmed Hassan'],
  },
})
check(two.status === 201, 'two-slot hold')
const heldTwo = two.body as {
  start_times: string[]
  end_time: string
  price_egp: number
}
check(heldTwo.start_times.join() === '20:00,21:00', 'two starts')
check(heldTwo.end_time === '22:00', 'two-hour end')
check(heldTwo.price_egp === 700, 'sum evening prices')

const gap = call('POST', '/bookings/hold', {
  ...authed,
  body: {
    court_id: courts[0]!.id,
    date: '2026-08-21',
    start_times: ['08:00', '10:00'],
  },
})
check(gap.status === 400, 'gap is rejected')

const overlap = call('POST', '/bookings/hold', {
  ...authed,
  body: {
    court_id: courts[0]!.id,
    date: '2026-08-21',
    start_times: ['21:00'],
  },
})
check(overlap.status === 409, 'overlap on second hour of two-slot hold')

const checkout = call('POST', `/bookings/${held.id}/checkout`, authed)
check(checkout.status === 200, 'checkout')
const status = call('GET', `/bookings/${held.id}/status`, authed)
const polled = status.body as { status: string; booking_code: string | null }
check(polled.status === 'confirmed', 'happy-path poll confirms')
check(!!polled.booking_code, 'booking code issued')

const pass = call('GET', `/passes/${polled.booking_code}`)
check(pass.status === 200, 'public pass')

const seedPass = call('GET', '/passes/MGZ-7F42K').body as { status: string }
check(seedPass.status === 'confirmed', 'seeded pass')

const staff = call('POST', '/auth/login', {
  body: { phone: '01000000000', password: 'staffpass' },
})
check(
  (staff.body as { user: { role: string } }).user.role === 'staff',
  'staff login role',
)
const staffToday = call('GET', '/staff/bookings', authed)
check(
  Array.isArray((staffToday.body as { bookings: unknown[] }).bookings) &&
    (staffToday.body as { bookings: unknown[] }).bookings.length >= 1,
  'staff bookings for today',
)
const redeem = call('POST', '/staff/passes/MGZ-7F42K/redeem', authed)
check(redeem.status === 200, 'redeem')
check(
  (redeem.body as { status: string }).status === 'redeemed',
  'redeemed status',
)

check(call('GET', '/nope').status === 404, 'unknown path')

console.log('api mock check ok')
