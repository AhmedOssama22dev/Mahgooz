import { tokenKindForPath } from './auth.ts'

function check(cond: unknown, msg: string) {
  if (!cond) throw new Error(msg)
}

check(tokenKindForPath('/courts') === null, 'courts are public')
check(tokenKindForPath('/slots') === null, 'slots are public')
check(tokenKindForPath('/passes/{booking_code}') === null, 'public pass')
check(tokenKindForPath('/auth/login') === null, 'login is public')
check(tokenKindForPath('/auth/refresh') === null, 'refresh is public')
check(tokenKindForPath('/staff/login') === null, 'staff login is public')
check(tokenKindForPath('/webhooks/paymob') === null, 'webhook is public')

check(tokenKindForPath('/auth/me') === 'customer', 'me needs customer jwt')
check(tokenKindForPath('/bookings') === 'customer', 'bookings list')
check(tokenKindForPath('/bookings/{booking_id}') === 'customer', 'booking by id')
check(tokenKindForPath('/bookings/hold') === 'customer', 'hold')

check(tokenKindForPath('/staff/bookings') === 'staff', 'staff bookings')
check(
  tokenKindForPath('/staff/passes/{booking_code}') === 'staff',
  'staff pass lookup',
)
check(
  tokenKindForPath('/staff/passes/{booking_code}/redeem') === 'staff',
  'redeem',
)

console.log('api auth check ok')
