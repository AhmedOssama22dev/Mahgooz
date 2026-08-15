import { tokenKindForPath } from './auth.ts'
import type { Period } from '../slot-states.ts'
import {
  HOLD_TTL_MS,
  MAX_HOLD_SLOTS,
  OPERATING_HOURS,
  SLOT_MINUTES,
  addHours,
  areConsecutiveHours,
  hourFromTime,
  periodFromHour,
  uniqueSortedTimes,
} from '../slot-states.ts'

export type MockReq = {
  method: string
  path: string
  query: URLSearchParams
  body?: unknown
  authorization?: string
}

export type MockRes = { status: number; body: unknown }

type BookingStatus =
  | 'held'
  | 'pending_payment'
  | 'confirmed'
  | 'redeemed'
  | 'cancelled'
  | 'failed'
  | 'expired'

type Court = { id: string; name: string; slug: string }

type Booking = {
  id: string
  status: BookingStatus
  court: { id: string; name: string }
  date: string
  start_times: string[]
  start_time: string
  end_time: string
  booker_name: string
  booker_phone: string
  attendee_names: string[]
  price_egp: number
  price_cents: number
  hold_expires_at: string | null
  booking_code: string | null
  qr_payload: string | null
  created_at: string
  paid_at: string | null
  redeemed_at: string | null
  paymob_transaction_id: number | null
}

const COURT_1: Court = {
  id: '11111111-1111-4111-8111-111111111111',
  name: 'Court 1',
  slug: 'court-1',
}
const COURT_2: Court = {
  id: '22222222-2222-4222-8222-222222222222',
  name: 'Court 2',
  slug: 'court-2',
}
const COURTS = [COURT_1, COURT_2]

const ACCESS = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access'
const REFRESH = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh'

const CUSTOMER_USER = {
  id: '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d',
  name: 'Ahmed Hassan',
  phone: '01012345678',
  role: 'customer' as const,
}
const STAFF_USER = {
  id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  name: 'Mostafa',
  phone: '01000000000',
  role: 'staff' as const,
}

const PRICE: Record<Period, { price_egp: number; price_cents: number }> = {
  morning: { price_egp: 200, price_cents: 20000 },
  afternoon: { price_egp: 280, price_cents: 28000 },
  evening: { price_egp: 350, price_cents: 35000 },
}

const ROUTES: Array<{ method: string; pattern: string }> = [
  { method: 'GET', pattern: '/health' },
  { method: 'GET', pattern: '/courts' },
  { method: 'GET', pattern: '/slots' },
  { method: 'GET', pattern: '/passes/{booking_code}' },
  { method: 'POST', pattern: '/auth/register' },
  { method: 'POST', pattern: '/auth/login' },
  { method: 'POST', pattern: '/auth/refresh' },
  { method: 'GET', pattern: '/auth/me' },
  { method: 'POST', pattern: '/bookings/hold' },
  { method: 'DELETE', pattern: '/bookings/{booking_id}' },
  { method: 'GET', pattern: '/bookings/{booking_id}' },
  { method: 'POST', pattern: '/bookings/{booking_id}/checkout' },
  { method: 'GET', pattern: '/bookings/{booking_id}/status' },
  { method: 'GET', pattern: '/bookings' },
  { method: 'GET', pattern: '/staff/bookings' },
  { method: 'POST', pattern: '/staff/passes/{booking_code}/redeem' },
  { method: 'GET', pattern: '/staff/passes/{booking_code}' },
  { method: 'POST', pattern: '/webhooks/paymob' },
]

let user = seedUser()
let bookings = new Map<string, Booking>()

function seedUser() {
  return { ...CUSTOMER_USER }
}

function hhmm(hour: number) {
  return `${String(hour).padStart(2, '0')}:00`
}

function todayCairo() {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Africa/Cairo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date())
}

function passUrl(code: string) {
  return `https://mahgooz.app/pass/${code}`
}

function err(status: number, code: string, message: string): MockRes {
  return { status, body: { error: { code, message } } }
}

function ok(body: unknown, status = 200): MockRes {
  return { status, body }
}

function matchPath(
  pattern: string,
  path: string,
): Record<string, string> | null {
  const pp = pattern.split('/').filter(Boolean)
  const sp = path.split('/').filter(Boolean)
  if (pp.length !== sp.length) return null
  const params: Record<string, string> = {}
  for (let i = 0; i < pp.length; i++) {
    const p = pp[i]!
    const s = sp[i]!
    if (p.startsWith('{') && p.endsWith('}')) {
      params[p.slice(1, -1)] = decodeURIComponent(s)
    } else if (p !== s) {
      return null
    }
  }
  return params
}

function courtById(id: string | undefined) {
  return COURTS.find((c) => c.id === id) ?? COURT_1
}

function priceAt(start: string) {
  const hour = Number(start.slice(0, 2))
  return PRICE[periodFromHour(hour)]
}

function occupying(courtId: string, date: string, start: string) {
  return [...bookings.values()].find(
    (b) =>
      b.court.id === courtId &&
      b.date === date &&
      b.start_times.includes(start) &&
      !['cancelled', 'failed', 'expired'].includes(b.status),
  )
}

function parseHoldSlots(
  body: Record<string, unknown>,
): { court_id: string; date: string; start_times: string[] } | MockRes {
  const raw = Array.isArray(body.slots) ? body.slots : null
  if (!raw) {
    return err(400, 'VALIDATION_ERROR', 'This field is required.')
  }
  const items = raw.filter(
    (item): item is Record<string, unknown> =>
      typeof item === 'object' && item !== null,
  )
  const times = uniqueSortedTimes(
    items
      .map((item) => item.start_time)
      .filter((t): t is string => typeof t === 'string'),
  )
  const hourOk = times.every((t) => {
    const hour = hourFromTime(t)
    return (
      /^\d{2}:00$/.test(t) &&
      hour >= OPERATING_HOURS.start &&
      hour < OPERATING_HOURS.end
    )
  })
  if (
    times.length < 1 ||
    times.length > MAX_HOLD_SLOTS ||
    !hourOk ||
    !areConsecutiveHours(times)
  ) {
    return err(
      400,
      'VALIDATION_ERROR',
      'Provide 1–4 consecutive hour starts (e.g. 18:00, 19:00).',
    )
  }
  return {
    court_id: str(items[0]?.court_id),
    date: str(items[0]?.date, todayCairo()),
    start_times: times,
  }
}

function slotState(courtId: string, date: string, start: string) {
  const b = occupying(courtId, date, start)
  if (!b) return 'available'
  if (b.status === 'held' || b.status === 'pending_payment') return 'held'
  return 'booked'
}

function buildSlots(court: Court, date: string) {
  const slots = []
  const hours = OPERATING_HOURS.end - OPERATING_HOURS.start
  for (let i = 0; i < hours; i++) {
    const hour = OPERATING_HOURS.start + i
    const start_time = hhmm(hour)
    const period = periodFromHour(hour)
    const { price_egp, price_cents } = PRICE[period]
    slots.push({
      start_time,
      end_time: hhmm(hour + 1),
      state: slotState(court.id, date, start_time),
      period,
      price_egp,
      price_cents,
      label: period === 'morning' ? 'Morning available' : null,
    })
  }
  return slots
}

function tokens() {
  return {
    access: ACCESS,
    refresh: REFRESH,
    token_type: 'Bearer' as const,
    expires_in: 3600,
    user,
  }
}

function asObject(body: unknown): Record<string, unknown> {
  return body !== null && typeof body === 'object' && !Array.isArray(body)
    ? (body as Record<string, unknown>)
    : {}
}

function str(v: unknown, fallback = '') {
  return typeof v === 'string' ? v : fallback
}

function strings(v: unknown): string[] {
  return Array.isArray(v) ? v.filter((x) => typeof x === 'string') : []
}

function bookingCode() {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  let code = 'MGZ-'
  for (let i = 0; i < 5; i++) {
    code += alphabet[Math.floor(Math.random() * alphabet.length)]
  }
  return code
}

function byCode(code: string) {
  return [...bookings.values()].find((b) => b.booking_code === code)
}

function confirm(b: Booking) {
  if (b.status === 'confirmed' || b.status === 'redeemed') return b
  const code = b.booking_code ?? bookingCode()
  b.status = 'confirmed'
  b.booking_code = code
  b.qr_payload = passUrl(code)
  b.hold_expires_at = null
  b.paid_at = new Date().toISOString()
  b.paymob_transaction_id = b.paymob_transaction_id ?? 289187034
  return b
}

function publicPass(b: Booking) {
  return {
    booking_code: b.booking_code,
    status: b.status,
    court: b.court,
    date: b.date,
    start_times: b.start_times,
    start_time: b.start_time,
    end_time: b.end_time,
    booker_name: b.booker_name,
    attendee_names: b.attendee_names,
    price_egp: b.price_egp,
    qr_payload: b.qr_payload,
    redeemed_at: b.redeemed_at,
  }
}

function customerDetail(b: Booking) {
  return {
    id: b.id,
    status: b.status,
    court: b.court,
    date: b.date,
    start_times: b.start_times,
    start_time: b.start_time,
    end_time: b.end_time,
    booker_name: b.booker_name,
    attendee_names: b.attendee_names,
    price_egp: b.price_egp,
    price_cents: b.price_cents,
    hold_expires_at: b.hold_expires_at,
    booking_code: b.booking_code,
    qr_payload: b.qr_payload,
    redeemed_at: b.redeemed_at,
    created_at: b.created_at,
    paid_at: b.paid_at,
  }
}

function listItem(b: Booking) {
  return {
    id: b.id,
    status: b.status,
    court_name: b.court.name,
    date: b.date,
    start_times: b.start_times,
    start_time: b.start_time,
    end_time: b.end_time,
    price_egp: b.price_egp,
    booking_code: b.booking_code,
    period: periodFromHour(Number(b.start_time.slice(0, 2))),
  }
}

function seedBookings() {
  const upcoming: Booking = {
    id: '3fa85f64-5717-4562-b3fc-2c963f66afa6',
    status: 'confirmed',
    court: { id: COURT_1.id, name: COURT_1.name },
    date: todayCairo(),
    start_times: ['18:00'],
    start_time: '18:00',
    end_time: '19:00',
    booker_name: 'Ahmed Hassan',
    booker_phone: '01012345678',
    attendee_names: [
      'Ahmed Hassan',
      'Omar Ali',
      'Youssef Nabil',
      'Karim Fathy',
    ],
    price_egp: 350,
    price_cents: 35000,
    hold_expires_at: null,
    booking_code: 'MGZ-7F42K',
    qr_payload: passUrl('MGZ-7F42K'),
    created_at: '2026-08-15T16:22:00+03:00',
    paid_at: '2026-08-15T16:24:11+03:00',
    redeemed_at: null,
    paymob_transaction_id: 289187034,
  }
  const past: Booking = {
    id: 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee',
    status: 'redeemed',
    court: { id: COURT_2.id, name: COURT_2.name },
    date: '2026-08-11',
    start_times: ['19:00'],
    start_time: '19:00',
    end_time: '20:00',
    booker_name: 'Ahmed Hassan',
    booker_phone: '01012345678',
    attendee_names: ['Ahmed Hassan'],
    price_egp: 350,
    price_cents: 35000,
    hold_expires_at: null,
    booking_code: 'MGZ-2K91P',
    qr_payload: passUrl('MGZ-2K91P'),
    created_at: '2026-08-11T18:00:00+03:00',
    paid_at: '2026-08-11T18:02:00+03:00',
    redeemed_at: '2026-08-11T18:58:00+03:00',
    paymob_transaction_id: 289187000,
  }
  bookings.set(upcoming.id, upcoming)
  bookings.set(past.id, past)
}

export function resetMock() {
  user = seedUser()
  bookings = new Map()
  seedBookings()
}

resetMock()

function handleRoute(
  pattern: string,
  params: Record<string, string>,
  req: MockReq,
): MockRes {
  const body = asObject(req.body)

  if (pattern === '/health') return ok({ status: 'ok' })
  if (pattern === '/courts') return ok(COURTS)

  if (pattern === '/slots') {
    const date = req.query.get('date') ?? todayCairo()
    const court = courtById(req.query.get('court_id') ?? undefined)
    return ok({
      date,
      court: { id: court.id, name: court.name },
      operating_hours: {
        open: hhmm(OPERATING_HOURS.start),
        close: hhmm(OPERATING_HOURS.end),
      },
      slot_minutes: SLOT_MINUTES,
      slots: buildSlots(court, date),
    })
  }

  if (pattern === '/passes/{booking_code}') {
    const b = byCode(params.booking_code ?? '')
    if (!b) return err(404, 'NOT_FOUND', 'Pass not found')
    return ok(publicPass(b))
  }

  if (pattern === '/auth/register') {
    const name = str(body.name, CUSTOMER_USER.name)
    const phone = str(body.phone, CUSTOMER_USER.phone)
    user = { ...CUSTOMER_USER, name, phone, role: 'customer' }
    return ok(tokens(), 201)
  }

  if (pattern === '/auth/login') {
    const phone = str(body.phone)
    if (phone === STAFF_USER.phone) {
      user = { ...STAFF_USER }
    } else if (phone) {
      user = { ...CUSTOMER_USER, phone }
    }
    return ok(tokens())
  }

  if (pattern === '/auth/refresh') {
    return ok({ access: ACCESS, token_type: 'Bearer', expires_in: 3600 })
  }

  if (pattern === '/auth/me') return ok(user)

  if (pattern === '/bookings/hold') {
    const parsed = parseHoldSlots(body)
    if ('status' in parsed) return parsed
    const court = courtById(parsed.court_id || undefined)
    const date = parsed.date
    const start_times = parsed.start_times
    const taken = start_times.find((t) => occupying(court.id, date, t))
    if (taken) {
      return err(409, 'SLOT_TAKEN', 'This slot is no longer available')
    }
    const attendees = strings(body.attendee_names)
    const now = new Date()
    const id = crypto.randomUUID()
    const start_time = start_times[0]!
    const prices = start_times.map(priceAt)
    const booking: Booking = {
      id,
      status: 'held',
      court: { id: court.id, name: court.name },
      date,
      start_times,
      start_time,
      end_time: addHours(start_times[start_times.length - 1]!, 1),
      booker_name: user.name,
      booker_phone: user.phone,
      attendee_names: attendees.length ? attendees : [user.name],
      price_egp: prices.reduce((sum, p) => sum + p.price_egp, 0),
      price_cents: prices.reduce((sum, p) => sum + p.price_cents, 0),
      hold_expires_at: new Date(now.getTime() + HOLD_TTL_MS).toISOString(),
      booking_code: null,
      qr_payload: null,
      created_at: now.toISOString(),
      paid_at: null,
      redeemed_at: null,
      paymob_transaction_id: null,
    }
    bookings.set(id, booking)
    return ok(customerDetail(booking), 201)
  }

  if (pattern === '/bookings') {
    const today = todayCairo()
    const upcoming = [...bookings.values()]
      .filter(
        (b) =>
          b.date >= today &&
          ['held', 'pending_payment', 'confirmed'].includes(b.status),
      )
      .map(listItem)
    const past = [...bookings.values()]
      .filter((b) => b.date < today || b.status === 'redeemed')
      .map(listItem)
    return ok({ upcoming, past })
  }

  if (pattern === '/bookings/{booking_id}') {
    const b = bookings.get(params.booking_id ?? '')
    if (!b) return err(404, 'NOT_FOUND', 'Booking not found')
    if (req.method === 'DELETE') {
      b.status = 'cancelled'
      b.hold_expires_at = null
      return ok({ id: b.id, status: 'cancelled', message: 'Slot released.' })
    }
    return ok(customerDetail(b))
  }

  if (pattern === '/bookings/{booking_id}/checkout') {
    const b = bookings.get(params.booking_id ?? '')
    if (!b) return err(404, 'NOT_FOUND', 'Booking not found')
    b.status = 'pending_payment'
    return ok({
      booking_id: b.id,
      status: b.status,
      amount_egp: b.price_egp,
      amount_cents: b.price_cents,
      currency: 'EGP',
      checkout_url:
        'https://accept.paymob.com/unifiedcheckout/?publicKey=egy_pk_test_xxxxxxxx&clientSecret=egy_csk_test_xxxxxxxx',
      paymob_intention_id: 'pi_test_8f3a1c2e',
    })
  }

  if (pattern === '/bookings/{booking_id}/status') {
    const b = bookings.get(params.booking_id ?? '')
    if (!b) return err(404, 'NOT_FOUND', 'Booking not found')
    // ponytail: mock skips Paymob — first poll confirms. Real webhook path is POST /webhooks/paymob.
    if (b.status === 'held' || b.status === 'pending_payment') confirm(b)
    return ok({
      id: b.id,
      status: b.status,
      booking_code: b.booking_code,
      pass_url: b.booking_code ? `/pass/${b.booking_code}` : null,
      hold_expires_at: b.hold_expires_at,
    })
  }

  if (pattern === '/staff/bookings') {
    const date = req.query.get('date') ?? todayCairo()
    return ok({
      date,
      bookings: [...bookings.values()]
        .filter(
          (b) =>
            b.date === date &&
            (b.status === 'confirmed' || b.status === 'redeemed'),
        )
        .map((b) => ({
          booking_code: b.booking_code,
          status: b.status,
          court_name: b.court.name,
          start_times: b.start_times,
          start_time: b.start_time,
          end_time: b.end_time,
          booker_name: b.booker_name,
          redeemed_at: b.redeemed_at,
        })),
    })
  }

  if (pattern === '/staff/passes/{booking_code}') {
    const b = byCode(params.booking_code ?? '')
    if (!b) return err(404, 'NOT_FOUND', 'Pass not found')
    return ok({
      booking_code: b.booking_code,
      status: b.status,
      can_redeem: b.status === 'confirmed',
      court: b.court,
      date: b.date,
      start_times: b.start_times,
      start_time: b.start_time,
      end_time: b.end_time,
      booker_name: b.booker_name,
      booker_phone: b.booker_phone,
      attendee_names: b.attendee_names,
      price_egp: b.price_egp,
      paymob_transaction_id: b.paymob_transaction_id,
      redeemed_at: b.redeemed_at,
    })
  }

  if (pattern === '/staff/passes/{booking_code}/redeem') {
    const b = byCode(params.booking_code ?? '')
    if (!b) return err(404, 'NOT_FOUND', 'Pass not found')
    b.status = 'redeemed'
    b.redeemed_at = new Date().toISOString()
    return ok({
      booking_code: b.booking_code,
      status: b.status,
      redeemed_at: b.redeemed_at,
      court: b.court,
      date: b.date,
      start_times: b.start_times,
      start_time: b.start_time,
      end_time: b.end_time,
      booker_name: b.booker_name,
      attendee_names: b.attendee_names,
    })
  }

  if (pattern === '/webhooks/paymob') {
    const obj = asObject(body.obj)
    const order = asObject(obj.order)
    const bookingId = str(order.merchant_order_id)
    const b = bookings.get(bookingId)
    if (!b) return err(404, 'NOT_FOUND', 'Booking not found')
    const already = b.status === 'confirmed' || b.status === 'redeemed'
    confirm(b)
    return ok({
      received: true,
      booking_id: b.id,
      status: b.status,
      booking_code: b.booking_code,
      ...(already ? { idempotent: true } : {}),
    })
  }

  return err(404, 'NOT_FOUND', 'Not found')
}

export function handleMock(req: MockReq): MockRes {
  const method = req.method.toUpperCase()
  const path = req.path.replace(/\/$/, '') || '/'
  const hit = ROUTES.find((r) => {
    if (r.method !== method) return false
    return matchPath(r.pattern, path) !== null
  })
  if (!hit) return err(404, 'NOT_FOUND', 'Not found')
  const params = matchPath(hit.pattern, path) ?? {}
  const kind = tokenKindForPath(hit.pattern)
  if (kind && !req.authorization) {
    return err(
      401,
      'UNAUTHENTICATED',
      'Authentication credentials were not provided.',
    )
  }
  return handleRoute(hit.pattern, params, req)
}
