import { Link, createFileRoute } from '@tanstack/react-router'

import { CustomerLayout } from '@/components/customer-layout'
import { BookingCard } from '@/components/booking-card'
import { EmptyState, Spinner } from '@/components/empty-state'
import { Button } from '@/components/ui/button'
import { $api } from '@/lib/api/client'
import { parseSlotStart } from '@/lib/format'
import { requireCustomer } from '@/lib/guards'
import { apiStatusToUi } from '@/lib/slot-states'

export const Route = createFileRoute('/bookings')({
  beforeLoad: ({ location }) => {
    requireCustomer(`${location.pathname}${location.searchStr}`)
  },
  component: BookingsPage,
})

function BookingsPage() {
  const list = $api.useQuery('get', '/bookings')

  return (
    <CustomerLayout width="wide">
      <div className="flex items-center justify-between gap-3">
        <h1 className="font-display text-2xl font-bold">My bookings</h1>
        <Button asChild>
          <Link to="/book">+ Book</Link>
        </Button>
      </div>

      {list.isLoading ? <Spinner label="Loading bookings…" /> : null}

      {!list.isLoading &&
      !(list.data?.upcoming?.length || list.data?.past?.length) ? (
        <EmptyState
          title="No bookings yet"
          description="Book your first court in under a minute."
          action={
            <Button asChild>
              <Link to="/book">Book a court</Link>
            </Button>
          }
        />
      ) : null}

      {list.data?.upcoming?.length ? (
        <section className="flex flex-col gap-3">
          <h2 className="font-display text-xl font-semibold">Upcoming</h2>
          <div className="grid gap-3 md:grid-cols-2">
            {list.data.upcoming.map((booking) => (
              <BookingCard
                key={booking.id}
                courtName={booking.court_name ?? 'Court'}
                start={parseSlotStart(
                  booking.date ?? '',
                  booking.start_time ?? '00:00',
                )}
                end={
                  booking.end_time
                    ? parseSlotStart(booking.date ?? '', booking.end_time)
                    : undefined
                }
                amount={booking.price_egp}
                status={apiStatusToUi(booking.status)}
                morningDeal={booking.period === 'morning'}
                code={booking.booking_code}
              />
            ))}
          </div>
        </section>
      ) : null}

      {list.data?.past?.length ? (
        <section className="flex flex-col gap-3">
          <h2 className="font-display text-xl font-semibold">Past</h2>
          <div className="grid gap-3 md:grid-cols-2">
            {list.data.past.map((booking) => (
              <BookingCard
                key={booking.id}
                courtName={booking.court_name ?? 'Court'}
                start={parseSlotStart(
                  booking.date ?? '',
                  booking.start_time ?? '00:00',
                )}
                end={
                  booking.end_time
                    ? parseSlotStart(booking.date ?? '', booking.end_time)
                    : undefined
                }
                amount={booking.price_egp}
                status={apiStatusToUi(booking.status)}
                morningDeal={booking.period === 'morning'}
                code={booking.booking_code}
              />
            ))}
          </div>
        </section>
      ) : null}
    </CustomerLayout>
  )
}
