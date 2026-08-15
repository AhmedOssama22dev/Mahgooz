import { tokenKindForPath } from './auth.ts'

function check(cond: unknown, msg: string) {
  if (!cond) throw new Error(msg)
}

check(tokenKindForPath('/courts') === null, 'courts are public')
check(tokenKindForPath('/slots') === null, 'slots are public')
check(tokenKindForPath('/passes/{booking_code}') === null, 'public pass')
check(tokenKindForPath('/auth/login') === null, 'login is public')
check(tokenKindForPath('/auth/refresh') === null, 'refresh is public')
check(tokenKindForPath('/webhooks/paymob') === null, 'webhook is public')

check(tokenKindForPath('/auth/me') === 'session', 'me needs jwt')
check(tokenKindForPath('/bookings') === 'session', 'bookings list')
check(tokenKindForPath('/bookings/{booking_id}') === 'session', 'booking by id')
check(tokenKindForPath('/bookings/hold') === 'session', 'hold')

check(tokenKindForPath('/staff/bookings') === 'session', 'staff bookings')
check(
  tokenKindForPath('/staff/passes/{booking_code}') === 'session',
  'staff pass lookup',
)
check(
  tokenKindForPath('/staff/passes/{booking_code}/redeem') === 'session',
  'redeem',
)

console.log('api auth check ok')
