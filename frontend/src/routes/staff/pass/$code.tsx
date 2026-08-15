import { Link, createFileRoute, useNavigate } from '@tanstack/react-router'
import { toast } from 'sonner'

import { EmptyState, Spinner } from '@/components/empty-state'
import { RedeemButton } from '@/components/staff-ops'
import { StaffShell } from '@/components/staff-shell'
import { StatusBadge, bookingStatusToKind } from '@/components/status-badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { $api } from '@/lib/api/client'
import { clearSession } from '@/lib/api/auth'
import {
  formatBookingDay,
  formatClock,
  formatEgp,
  parseSlotStart,
  todayKey,
} from '@/lib/format'
import { requireStaff } from '@/lib/guards'
import { staffPassSchedule } from '@/lib/staff-pass'
import { apiStatusToUi } from '@/lib/slot-states'
import { apiErrorMessage } from '@/lib/utils'

export const Route = createFileRoute('/staff/pass/$code')({
  beforeLoad: ({ location }) => {
    requireStaff(`${location.pathname}${location.searchStr}`)
  },
  component: StaffPassPage,
})

function StaffPassPage() {
  const { code } = Route.useParams()
  const navigate = useNavigate()
  const pass = $api.useQuery('get', '/staff/passes/{booking_code}', {
    params: { path: { booking_code: code } },
  })
  const redeem = $api.useMutation('post', '/staff/passes/{booking_code}/redeem')

  async function onRedeem() {
    try {
      await redeem.mutateAsync({
        params: { path: { booking_code: code } },
        body: {},
      })
      toast.success('Checked in')
      await pass.refetch()
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Could not redeem this pass'))
    }
  }

  return (
    <StaffShell
      current="lookup"
      onLogout={() => {
        clearSession()
        void navigate({ to: '/login' })
      }}
    >
      <Button
        variant="ghost"
        size="sm"
        className="self-start text-muted-foreground"
        asChild
      >
        <Link to="/staff">← Lookup</Link>
      </Button>

      {pass.isLoading ? <Spinner label="Looking up pass…" /> : null}

      {pass.error || (!pass.isLoading && !pass.data?.booking_code) ? (
        <EmptyState
          title="No booking for this code"
          action={
            <Button asChild>
              <Link to="/staff">Try another code</Link>
            </Button>
          }
        />
      ) : null}

      {pass.data?.booking_code ? (
        <PassDetail
          data={pass.data}
          onRedeem={() => void onRedeem()}
          redeeming={redeem.isPending}
        />
      ) : null}
    </StaffShell>
  )
}

type StaffPass = {
  booking_code?: string
  status?: string
  can_redeem?: boolean
  court?: { id?: string; name?: string }
  date?: string
  start_time?: string
  end_time?: string
  slots?: Array<{
    court?: { name?: string }
    date?: string
    start_time?: string
    end_time?: string
  }>
  booker_name?: string
  booker_phone?: string
  attendee_names?: string[]
  price_egp?: number
  total_price_egp?: number
  paymob_transaction_id?: number
  redeemed_at?: unknown
}

function PassDetail({
  data,
  onRedeem,
  redeeming,
}: {
  data: StaffPass
  onRedeem: () => void
  redeeming: boolean
}) {
  const status = apiStatusToUi(data.status)
  const schedule = staffPassSchedule(data)
  const start = schedule
    ? parseSlotStart(schedule.date, schedule.startTime)
    : null
  const today = todayKey()
  const wrongDay = Boolean(schedule?.date && schedule.date !== today)
  const redeemedAt =
    typeof data.redeemed_at === 'string' ? data.redeemed_at : undefined
  const players = data.attendee_names?.length ?? 1
  const canRedeem = Boolean(data.can_redeem) && !redeeming
  const priceEgp = data.price_egp ?? data.total_price_egp

  let message: string | undefined
  if (status === 'pending_payment' || data.status === 'held') {
    message = 'Payment not confirmed yet'
  } else if (wrongDay && schedule) {
    message = `This pass is for ${formatBookingDay(
      parseSlotStart(schedule.date, '12:00'),
    )}, not today`
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="font-mono text-2xl tracking-widest">
            {data.booking_code}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 text-sm">
          <p className="font-display text-lg font-semibold">
            {schedule?.courtName ?? data.court?.name ?? 'Court'}
          </p>
          <p>
            {schedule
              ? schedule.date === today
                ? 'Today'
                : start
                  ? formatBookingDay(start)
                  : schedule.date
              : '—'}{' '}
            · {schedule ? `${schedule.startTime}–${schedule.endTime}` : '—'}
          </p>
          <p>{data.booker_name}</p>
          <p className="text-muted-foreground">
            {data.booker_phone} · {players}{' '}
            {players === 1 ? 'player' : 'players'}
          </p>
          {priceEgp != null ? (
            <p className="tabular-nums">{formatEgp(priceEgp)}</p>
          ) : null}
          {data.paymob_transaction_id ? (
            <p className="text-muted-foreground">
              Paymob #{data.paymob_transaction_id}
            </p>
          ) : null}
        </CardContent>
      </Card>

      <div className="flex flex-col gap-4">
        <StatusBadge
          status={bookingStatusToKind(status)}
          label={
            status === 'paid' && !wrongDay
              ? 'PAID — Ready'
              : status === 'redeemed' && redeemedAt
                ? `REDEEMED at ${formatClock(redeemedAt)}`
                : undefined
          }
        />
        {message ? (
          <p className="text-sm text-muted-foreground">{message}</p>
        ) : null}
        {canRedeem || status === 'redeemed' ? (
          <RedeemButton
            redeemed={status === 'redeemed'}
            redeemedAt={redeemedAt ? formatClock(redeemedAt) : undefined}
            onRedeem={canRedeem ? onRedeem : undefined}
          />
        ) : (
          <Button disabled className="min-h-14 w-full">
            Cannot redeem
          </Button>
        )}
      </div>
    </div>
  )
}
