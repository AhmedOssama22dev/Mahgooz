import { Link, createFileRoute } from '@tanstack/react-router'

import { AppShell } from '@/components/app-shell'
import { EmptyState, Spinner } from '@/components/empty-state'
import { PassCode, PassQr } from '@/components/pass-ticket'
import { StatusBadge, bookingStatusToKind } from '@/components/status-badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { useSession } from '@/hooks/use-session'
import { $api } from '@/lib/api/client'
import { formatBookingDay, formatEgp, parseSlotStart } from '@/lib/format'
import { apiStatusToUi } from '@/lib/slot-states'

export const Route = createFileRoute('/pass/$code')({
  component: PassPage,
})

function PassPage() {
  const { code } = Route.useParams()
  const { loggedIn } = useSession()
  const pass = $api.useQuery('get', '/passes/{booking_code}', {
    params: { path: { booking_code: code } },
  })

  if (pass.isLoading) {
    return (
      <AppShell>
        <Spinner label="Loading pass…" />
      </AppShell>
    )
  }

  if (pass.error || !pass.data?.booking_code) {
    return (
      <AppShell>
        <EmptyState
          title="Pass not found"
          description="No paid booking for this code."
          action={
            <Button asChild>
              <Link to="/">Back to home</Link>
            </Button>
          }
        />
      </AppShell>
    )
  }

  const data = pass.data
  const status = apiStatusToUi(data.status)
  const start = parseSlotStart(data.date ?? '', data.start_time ?? '00:00')
  const players = data.attendee_names?.length ?? 1
  const qrValue =
    data.qr_payload ??
    (typeof window !== 'undefined' ? window.location.href : code)
  const redeemedAt =
    typeof data.redeemed_at === 'string' ? data.redeemed_at : undefined

  const banner =
    status === 'redeemed' && redeemedAt
      ? `Already checked in · ${new Date(redeemedAt).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false })}`
      : status === 'expired'
        ? 'Slot time passed'
        : undefined

  return (
    <AppShell>
      {loggedIn ? (
        <Button
          variant="ghost"
          size="sm"
          className="self-start text-muted-foreground"
          asChild
        >
          <Link to="/bookings">← Back to my bookings</Link>
        </Button>
      ) : null}

      <Card className="mx-auto w-full max-w-md">
        <CardContent className="flex flex-col items-center gap-5 py-6">
          <StatusBadge status={bookingStatusToKind(status)} label={banner} />
          <PassQr value={qrValue} />
          <PassCode code={data.booking_code ?? code} />
          <Separator />
          <div className="w-full text-center">
            <p className="font-display text-lg font-semibold">
              {data.court?.name ?? 'Court'}
            </p>
            <p className="mt-1 text-sm">{formatBookingDay(start)}</p>
            <p className="text-sm tabular-nums">
              {data.start_time} – {data.end_time}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              {data.booker_name} · {players}{' '}
              {players === 1 ? 'player' : 'players'}
            </p>
            {data.price_egp != null ? (
              <p className="mt-1 text-sm tabular-nums">
                Paid · {formatEgp(data.price_egp)}
              </p>
            ) : null}
          </div>
          <p className="text-sm text-muted-foreground">
            Show this to staff on arrival
          </p>
        </CardContent>
      </Card>
    </AppShell>
  )
}
