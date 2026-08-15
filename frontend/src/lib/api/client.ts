import createFetchClient from 'openapi-fetch'
import createClient from 'openapi-react-query'
import type { Middleware } from 'openapi-fetch'

import { tokenForPath } from './auth.ts'
import type { paths } from './schema'

function resolveBaseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || '/api/v1'
  // Dev stays same-origin so Vite can mock or proxy to the backend.
  if (import.meta.env.DEV && /^https?:\/\//.test(raw)) {
    return new URL(raw).pathname.replace(/\/$/, '') || '/api/v1'
  }
  return raw
}

const baseUrl = resolveBaseUrl()

const authMiddleware: Middleware = {
  onRequest({ request, schemaPath }) {
    if (request.headers.has('Authorization')) return request
    const token = tokenForPath(schemaPath)
    if (!token) return undefined
    request.headers.set('Authorization', `Bearer ${token}`)
    return request
  },
}

export const fetchClient = createFetchClient<paths>({ baseUrl })

fetchClient.use(authMiddleware)

/** Typed TanStack Query hooks + `queryOptions` for route loaders. */
export const $api = createClient(fetchClient)
