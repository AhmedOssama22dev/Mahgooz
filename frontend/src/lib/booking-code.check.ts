import { bookingCodeFromQr } from './booking-code.ts'

function check(cond: unknown, msg: string) {
  if (!cond) throw new Error(msg)
}

check(
  bookingCodeFromQr('https://mahgooz.app/pass/MGZ-7F42K') === 'MGZ-7F42K',
  'prod url',
)
check(
  bookingCodeFromQr('http://localhost:3000/pass/MGZ-7F42K') === 'MGZ-7F42K',
  'local url',
)
check(bookingCodeFromQr('/pass/MGZ-7F42K') === 'MGZ-7F42K', 'relative path')
check(
  bookingCodeFromQr('https://mahgooz.app/pass/MGZ-7F42K/') === 'MGZ-7F42K',
  'trailing slash',
)
check(
  bookingCodeFromQr('https://mahgooz.app/pass/MGZ-7F42K?x=1') === 'MGZ-7F42K',
  'query',
)
check(bookingCodeFromQr('MGZ-7F42K') === 'MGZ-7F42K', 'raw code')
check(bookingCodeFromQr('mgz-7f42k') === 'MGZ-7F42K', 'lowercase')
check(bookingCodeFromQr('  MGZ-7F42K  ') === 'MGZ-7F42K', 'trim')
check(bookingCodeFromQr('') === null, 'empty')
check(bookingCodeFromQr('https://example.com/other') === null, 'unrelated url')
check(bookingCodeFromQr('not-a-code') === null, 'garbage')

console.log('booking-code check ok')
