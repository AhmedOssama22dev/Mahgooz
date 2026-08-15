export type TokenKind = 'session'
export type UserRole = 'customer' | 'staff'

export type AuthUser = {
  id?: string
  name: string
  phone: string
  role: UserRole
}

const ACCESS_KEY = 'mahgouz-access-token'
const REFRESH_KEY = 'mahgouz-refresh-token'
const LEGACY_STAFF_KEY = 'mahgouz-staff-token'
const USER_KEY = 'mahgouz-user'
const SESSION_EVENT = 'mahgouz-session'

const PUBLIC_EXACT = new Set([
  '/health',
  '/courts',
  '/slots',
  '/auth/register',
  '/auth/login',
  '/auth/refresh',
])

/** Which JWT (if any) a generated OpenAPI path needs. `schemaPath` keeps `{params}`. */
export function tokenKindForPath(schemaPath: string): TokenKind | null {
  if (PUBLIC_EXACT.has(schemaPath)) return null
  if (schemaPath.startsWith('/passes/')) return null
  if (schemaPath.startsWith('/webhooks/')) return null
  return 'session'
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
    user: getSessionUser() ?? null,
  })
}

export function parseRole(value: unknown): UserRole {
  return value === 'staff' ? 'staff' : 'customer'
}

export function defaultHomePath(role?: UserRole) {
  return role === 'staff' ? '/staff/bookings' : '/book'
}

export function setSession(tokens: {
  access: string
  refresh: string
  user?: AuthUser
}) {
  localStorage.setItem(ACCESS_KEY, tokens.access)
  localStorage.setItem(REFRESH_KEY, tokens.refresh)
  if (tokens.user) {
    localStorage.setItem(USER_KEY, JSON.stringify(tokens.user))
  }
  localStorage.removeItem(LEGACY_STAFF_KEY)
  emitSession()
}

export function getSessionUser(): AuthUser | undefined {
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
      const record = parsed as { id?: string; name: string; phone: string; role?: unknown }
      return {
        id: record.id,
        name: record.name,
        phone: record.phone,
        role: parseRole(record.role),
      }
    }
  } catch {
    return undefined
  }
  return undefined
}

export function clearSession() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(LEGACY_STAFF_KEY)
  emitSession()
}

export function tokenForPath(schemaPath: string): string | undefined {
  if (tokenKindForPath(schemaPath) === 'session') return getAccessToken()
  return undefined
}

export function saveAuthTokens(data: {
  access?: string
  refresh?: string
  user?: { id?: string; name?: string; phone?: string; role?: string }
}) {
  if (!data.access || !data.refresh) {
    throw new Error('Login did not return tokens')
  }
  setSession({
    access: data.access,
    refresh: data.refresh,
    user:
      data.user?.name && data.user.phone
        ? {
            id: data.user.id,
            name: data.user.name,
            phone: data.user.phone,
            role: parseRole(data.user.role),
          }
        : undefined,
  })
}
