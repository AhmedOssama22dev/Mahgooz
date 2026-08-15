import createFetchClient from 'openapi-fetch'
import createClient from 'openapi-react-query'
import type { Middleware } from 'openapi-fetch'

import { tokenForPath } from './auth.ts'
import type { paths } from './schema'

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

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
