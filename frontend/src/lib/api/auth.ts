export type TokenKind = 'customer' | 'staff'

const ACCESS_KEY = 'mahgouz-access-token'
const REFRESH_KEY = 'mahgouz-refresh-token'
const STAFF_KEY = 'mahgouz-staff-token'

const PUBLIC_EXACT = new Set([
  '/health',
  '/courts',
  '/slots',
  '/auth/register',
  '/auth/login',
  '/auth/refresh',
  '/staff/login',
])

/** Which JWT (if any) a generated OpenAPI path needs. `schemaPath` keeps `{params}`. */
export function tokenKindForPath(schemaPath: string): TokenKind | null {
  if (PUBLIC_EXACT.has(schemaPath)) return null
  if (schemaPath.startsWith('/passes/')) return null
  if (schemaPath.startsWith('/webhooks/')) return null
  if (schemaPath.startsWith('/staff/')) return 'staff'
  return 'customer'
}

function read(key: string): string | undefined {
  if (typeof localStorage === 'undefined') return undefined
  return localStorage.getItem(key) ?? undefined
}

export function getAccessToken(): string | undefined {
  return read(ACCESS_KEY)
}

export function getRefreshToken(): string | undefined {
  return read(REFRESH_KEY)
}

export function getStaffToken(): string | undefined {
  return read(STAFF_KEY)
}

export function setCustomerSession(tokens: { access: string; refresh: string }) {
  localStorage.setItem(ACCESS_KEY, tokens.access)
  localStorage.setItem(REFRESH_KEY, tokens.refresh)
}

export function setStaffSession(access: string) {
  localStorage.setItem(STAFF_KEY, access)
}

export function clearCustomerSession() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export function clearStaffSession() {
  localStorage.removeItem(STAFF_KEY)
}

export function tokenForPath(schemaPath: string): string | undefined {
  const kind = tokenKindForPath(schemaPath)
  if (kind === 'staff') return getStaffToken()
  if (kind === 'customer') return getAccessToken()
  return undefined
}
