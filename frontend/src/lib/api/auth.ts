export type TokenKind = 'customer' | 'staff'

export type CustomerUser = {
  id?: string
  name: string
  phone: string
}

const ACCESS_KEY = 'mahgouz-access-token'
const REFRESH_KEY = 'mahgouz-refresh-token'
const STAFF_KEY = 'mahgouz-staff-token'
const USER_KEY = 'mahgouz-user'
const SESSION_EVENT = 'mahgouz-session'

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

function emitSession() {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new Event(SESSION_EVENT))
}

export function subscribeSession(onChange: () => void) {
  window.addEventListener(SESSION_EVENT, onChange)
  window.addEventListener('storage', onChange)
  return () => {
    window.removeEventListener(SESSION_EVENT, onChange)
    window.removeEventListener('storage', onChange)
  }
}

export function sessionSnapshot() {
  return JSON.stringify({
    access: getAccessToken() ?? null,
    staff: getStaffToken() ?? null,
    user: getCustomerUser() ?? null,
  })
}

export function setCustomerSession(tokens: {
  access: string
  refresh: string
  user?: CustomerUser
}) {
  localStorage.setItem(ACCESS_KEY, tokens.access)
  localStorage.setItem(REFRESH_KEY, tokens.refresh)
  if (tokens.user) {
    localStorage.setItem(USER_KEY, JSON.stringify(tokens.user))
  }
  emitSession()
}

export function setStaffSession(access: string) {
  localStorage.setItem(STAFF_KEY, access)
  emitSession()
}

export function getCustomerUser(): CustomerUser | undefined {
  const raw = read(USER_KEY)
  if (!raw) return undefined
  try {
    const parsed: unknown = JSON.parse(raw)
    if (
      parsed &&
      typeof parsed === 'object' &&
      'name' in parsed &&
      'phone' in parsed &&
      typeof parsed.name === 'string' &&
      typeof parsed.phone === 'string'
    ) {
      return parsed as CustomerUser
    }
  } catch {
    return undefined
  }
  return undefined
}

export function clearCustomerSession() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(USER_KEY)
  emitSession()
}

export function clearStaffSession() {
  localStorage.removeItem(STAFF_KEY)
  emitSession()
}

export function tokenForPath(schemaPath: string): string | undefined {
  const kind = tokenKindForPath(schemaPath)
  if (kind === 'staff') return getStaffToken()
  if (kind === 'customer') return getAccessToken()
  return undefined
}

export function saveAuthTokens(data: {
  access?: string
  refresh?: string
  user?: { id?: string; name?: string; phone?: string }
}) {
  if (!data.access || !data.refresh) {
    throw new Error('Login did not return tokens')
  }
  setCustomerSession({
    access: data.access,
    refresh: data.refresh,
    user:
      data.user?.name && data.user.phone
        ? { id: data.user.id, name: data.user.name, phone: data.user.phone }
        : undefined,
  })
}
