import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useEffect, useRef } from 'react'

import { CustomerLayout } from '@/components/customer-layout'
import { Spinner } from '@/components/empty-state'
import { Card, CardContent } from '@/components/ui/card'
import { $api } from '@/lib/api/client'
import { requireCustomer } from '@/lib/guards'
import { POLL_INTERVAL_MS, POLL_TIMEOUT_MS } from '@/lib/slot-states'

type PendingSearch = {
  bookingId: string
}

export const Route = createFileRoute('/book/pending')({
  validateSearch: (search: Record<string, unknown>): PendingSearch => ({
    bookingId: typeof search.bookingId === 'string' ? search.bookingId : '',
  }),
  beforeLoad: ({ location }) => {
    requireCustomer(`${location.pathname}${location.searchStr}`)
  },
  component: BookPendingPage,
})

function BookPendingPage() {
  const navigate = useNavigate()
  const { bookingId } = Route.useSearch()
  const started = useRef(Date.now())

  const detail = $api.useQuery(
    'get',
    '/bookings/{booking_id}',
    { params: { path: { booking_id: bookingId } } },
    { enabled: Boolean(bookingId) },
  )

  const status = $api.useQuery(
    'get',
    '/bookings/{booking_id}/status',
    { params: { path: { booking_id: bookingId } } },
    {
      enabled: Boolean(bookingId),
      refetchInterval: (query) => {
        const value = query.state.data?.status
        if (
          value === 'confirmed' ||
          value === 'failed' ||
          value === 'cancelled' ||
          value === 'expired'
        ) {
          return false
        }
        if (Date.now() - started.current > POLL_TIMEOUT_MS) return false
        return POLL_INTERVAL_MS
      },
    },
  )

  useEffect(() => {
    if (!bookingId) {
      void navigate({ to: '/book' })
      return
    }
    const value = status.data?.status
    const code =
      typeof status.data?.booking_code === 'string'
        ? status.data.booking_code
        : undefined
    if (value === 'confirmed' && code) {
      void navigate({ to: '/pass/$code', params: { code } })
      return
    }
    if (value === 'failed' || value === 'cancelled' || value === 'expired') {
      void navigate({ to: '/book/failed' })
    }
  }, [bookingId, navigate, status.data])

  useEffect(() => {
    const id = window.setTimeout(() => {
      void navigate({ to: '/book/failed' })
    }, POLL_TIMEOUT_MS)
    return () => window.clearTimeout(id)
  }, [navigate])

  const court = detail.data?.court?.name
  const time = detail.data?.start_time
  const end = detail.data?.end_time

  return (
    <CustomerLayout>
      <Card className="mx-auto w-full max-w-md">
        <CardContent className="flex flex-col items-center gap-4 py-10 text-center">
          <Spinner label="Confirming payment…" />
          <p className="text-sm text-muted-foreground">
            Don&apos;t close this page. Usually takes a few seconds.
          </p>
          {court && time ? (
            <p className="font-display font-semibold">
              {court} · {time}
              {end ? `–${end}` : ''}
            </p>
          ) : null}
        </CardContent>
      </Card>
    </CustomerLayout>
  )
}
