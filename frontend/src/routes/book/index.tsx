import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { startOfDay } from 'date-fns'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { CustomerLayout } from '@/components/customer-layout'
import { BookingSummary } from '@/components/booking-summary'
import { CourtCard } from '@/components/court-card'
import { DateStrip } from '@/components/date-strip'
import { Field } from '@/components/field'
import { HoldTimer } from '@/components/hold-timer'
import { Spinner } from '@/components/empty-state'
import { StepProgress } from '@/components/step-progress'
import { StickyFooterCTA } from '@/components/sticky-footer-cta'
import { SlotGrid } from '@/components/slot-grid'
import type { SlotBand } from '@/components/slot-grid'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useSession } from '@/hooks/use-session'
import { $api } from '@/lib/api/client'
import { dateKey, formatEgp, parseSlotStart } from '@/lib/format'
import { requireCustomer } from '@/lib/guards'
import {
  addHours,
  periodFromHour,
  toggleConsecutiveHour,
} from '@/lib/slot-states'
import type { Period, SlotState } from '@/lib/slot-states'
import { apiErrorMessage } from '@/lib/utils'

const STEPS = ['Date', 'Court', 'Time', 'Confirm']

type BookSearch = {
  period?: 'morning'
}

export const Route = createFileRoute('/book/')({
  validateSearch: (search: Record<string, unknown>): BookSearch => ({
    period: search.period === 'morning' ? 'morning' : undefined,
  }),
  beforeLoad: ({ location }) => {
    requireCustomer(`${location.pathname}${location.searchStr}`)
  },
  component: BookPage,
})

function BookPage() {
  const navigate = useNavigate()
  const { period } = Route.useSearch()
  const { user } = useSession()
  const me = $api.useQuery('get', '/auth/me')
  const booker = me.data ?? user

  const [step, setStep] = useState(0)
  const [date, setDate] = useState(() => startOfDay(new Date()))
  const [courtId, setCourtId] = useState<string>()
  const [courtName, setCourtName] = useState<string>()
  const [selectedTimes, setSelectedTimes] = useState<string[]>([])
  const [players, setPlayers] = useState(4)
  const [hold, setHold] = useState<{
    id: string
    expiresAt: string
    endTime: string
    price: number
    name: string
    phone: string
  }>()

  const dateStr = dateKey(date)
  const courts = $api.useQuery('get', '/courts')
  const courtA = courts.data?.[0]
  const courtB = courts.data?.[1]
  const slotsA = $api.useQuery(
    'get',
    '/slots',
    { params: { query: { date: dateStr, court_id: courtA?.id } } },
    { enabled: Boolean(courtA?.id) && step >= 1 },
  )
  const slotsB = $api.useQuery(
    'get',
    '/slots',
    { params: { query: { date: dateStr, court_id: courtB?.id } } },
    { enabled: Boolean(courtB?.id) && step >= 1 },
  )
  const slots = $api.useQuery(
    'get',
    '/slots',
    { params: { query: { date: dateStr, court_id: courtId } } },
    { enabled: Boolean(courtId) && step >= 2 },
  )

  const holdSlot = $api.useMutation('post', '/bookings/hold')
  const checkout = $api.useMutation('post', '/bookings/{booking_id}/checkout')
  const release = $api.useMutation('delete', '/bookings/{booking_id}')

  const bands = useMemo(
    () => bandsFromSlots(slots.data?.slots ?? [], selectedTimes),
    [slots.data?.slots, selectedTimes],
  )
  const selectedTotal = useMemo(
    () => priceForTimes(slots.data?.slots ?? [], selectedTimes),
    [slots.data?.slots, selectedTimes],
  )

  async function pickCourt(id: string, name: string) {
    setCourtId(id)
    setCourtName(name)
    setSelectedTimes([])
    setStep(2)
  }

  function toggleSlot(time: string) {
    setSelectedTimes((current) => toggleConsecutiveHour(current, time))
  }

  async function holdSelected() {
    if (!courtId || selectedTimes.length === 0) return
    const name = booker?.name ?? 'Guest'
    try {
      const booking = await holdSlot.mutateAsync({
        body: {
          court_id: courtId,
          date: dateStr,
          start_times: selectedTimes,
          attendee_names: [name],
        },
      })
      if (!booking.id || !booking.hold_expires_at) {
        toast.error('Could not hold this slot')
        return
      }
      setHold({
        id: booking.id,
        expiresAt: booking.hold_expires_at,
        endTime: booking.end_time ?? addHours(selectedTimes[selectedTimes.length - 1]!, 1),
        price: booking.price_egp ?? 0,
        name: booking.booker_name ?? name,
        phone: booker?.phone ?? '',
      })
      setStep(3)
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Slot just taken — pick another'))
      void slots.refetch()
    }
  }

  async function cancelHold() {
    if (hold) {
      try {
        await release.mutateAsync({
          params: { path: { booking_id: hold.id } },
        })
      } catch {
        // Slot may already be expired — still go back.
      }
    }
    setHold(undefined)
    setStep(2)
    void slots.refetch()
  }

  async function pay() {
    if (!hold) return
    try {
      const result = await checkout.mutateAsync({
        params: { path: { booking_id: hold.id } },
        body: {},
      })
      if (shouldOpenPaymob(result.checkout_url)) {
        window.location.assign(result.checkout_url!)
        return
      }
      await navigate({
        to: '/book/pending',
        search: { bookingId: result.booking_id ?? hold.id },
      })
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Could not start checkout'))
    }
  }

  const title =
    step === 0
      ? 'When do you want to play?'
      : step === 1
        ? date.toLocaleDateString('en-GB', {
            weekday: 'short',
            day: 'numeric',
            month: 'short',
          })
        : `${courtName} · ${date.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })}`

  return (
    <CustomerLayout
      width="wide"
      showBottomNav={false}
      footer={
        step === 0 ? (
          <StickyFooterCTA>
            <Button className="w-full" onClick={() => setStep(1)}>
              Next
            </Button>
          </StickyFooterCTA>
        ) : step === 2 ? (
          <StickyFooterCTA>
            <Button
              className="w-full"
              disabled={selectedTimes.length === 0 || holdSlot.isPending}
              onClick={() => void holdSelected()}
            >
              {holdSlot.isPending
                ? 'Holding…'
                : selectedTimes.length === 0
                  ? 'Pick a time'
                  : `Hold ${selectedTimes[0]} – ${addHours(selectedTimes[selectedTimes.length - 1]!, 1)} · ${formatEgp(selectedTotal)}`}
            </Button>
          </StickyFooterCTA>
        ) : step === 3 && hold ? (
          <StickyFooterCTA>
            <div className="mx-auto flex w-full max-w-lg flex-col gap-2">
              <Button
                className="w-full"
                onClick={() => void pay()}
                disabled={checkout.isPending}
              >
                {checkout.isPending ? 'Starting checkout…' : 'Pay with Paymob'}
              </Button>
              <Button
                variant="ghost"
                className="w-full"
                onClick={() => void cancelHold()}
              >
                Cancel releases your slots
              </Button>
            </div>
          </StickyFooterCTA>
        ) : undefined
      }
    >
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between gap-3">
          {step > 0 ? (
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground"
              onClick={() => {
                if (step === 3) {
                  void cancelHold()
                  return
                }
                setStep((s) => s - 1)
              }}
            >
              ← Back
            </Button>
          ) : (
            <span />
          )}
          <h1 className="font-display text-xl font-semibold">Book a court</h1>
          <span className="w-16" />
        </div>
        <StepProgress steps={STEPS} current={step} />
      </div>

      {step === 0 ? (
        <section className="flex flex-col gap-4">
          <h2 className="font-display text-lg font-semibold">{title}</h2>
          {period === 'morning' ? (
            <p className="text-sm text-clay-orange">
              Quiet mornings, lower price — pick a slot before 12 PM
            </p>
          ) : null}
          <DateStrip value={date} onChange={setDate} />
        </section>
      ) : null}

      {step === 1 ? (
        <section className="flex flex-col gap-4">
          <h2 className="font-display text-lg font-semibold">{title}</h2>
          {courts.isLoading ? (
            <Spinner label="Loading courts…" />
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {courts.data?.map((court, index) => {
                const grid = index === 0 ? slotsA.data : slotsB.data
                const available =
                  grid?.slots?.filter((s) => s.state === 'available').length ??
                  0
                return (
                  <CourtCard
                    key={court.id}
                    name={court.name ?? `Court ${index + 1}`}
                    slotsAvailable={available}
                    selected={courtId === court.id}
                    onSelect={() =>
                      void pickCourt(
                        court.id ?? '',
                        court.name ?? `Court ${index + 1}`,
                      )
                    }
                  />
                )
              })}
            </div>
          )}
        </section>
      ) : null}

      {step === 2 ? (
        <section className="flex flex-col gap-4">
          <h2 className="font-display text-lg font-semibold">{title}</h2>
          {slots.isLoading ? (
            <Spinner label="Loading slots…" />
          ) : (
            <SlotGrid
              bands={bands}
              onSelect={(time) => {
                if (holdSlot.isPending) return
                toggleSlot(time)
              }}
            />
          )}
        </section>
      ) : null}

      {step === 3 && hold && selectedTimes[0] ? (
        <section className="grid gap-6 md:grid-cols-2">
          <BookingSummary
            courtName={courtName ?? 'Court'}
            start={parseSlotStart(dateStr, selectedTimes[0])}
            end={parseSlotStart(dateStr, hold.endTime)}
            amount={hold.price}
            playerName={hold.name}
            phone={hold.phone}
          />
          <div className="flex flex-col gap-4 rounded-[12px] border border-border bg-card p-4">
            <Field label="Players" htmlFor="players">
              <Select
                value={String(players)}
                onValueChange={(value) => setPlayers(Number(value))}
              >
                <SelectTrigger id="players">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectGroup>
                    <SelectItem value="1">1</SelectItem>
                    <SelectItem value="2">2</SelectItem>
                    <SelectItem value="3">3</SelectItem>
                    <SelectItem value="4">4</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </Field>
            <HoldTimer
              expiresAt={new Date(hold.expiresAt)}
              onExpire={() => {
                toast.error('Hold expired — pick another slot')
                void cancelHold()
              }}
            />
          </div>
        </section>
      ) : null}
    </CustomerLayout>
  )
}

function shouldOpenPaymob(url: string | undefined) {
  if (!url || !import.meta.env.VITE_API_BASE_URL) return false
  try {
    return new URL(url).hostname.includes('paymob')
  } catch {
    return false
  }
}

function bandsFromSlots(
  slots: Array<{
    start_time?: string
    state?: string
    period?: string
    price_egp?: number
  }>,
  selected: string[],
): SlotBand[] {
  const picked = new Set(selected)
  const byPeriod = new Map<Period, SlotBand>()
  for (const slot of slots) {
    const time = slot.start_time ?? ''
    const hour = Number(time.slice(0, 2))
    const period = (slot.period as Period | undefined) ?? periodFromHour(hour)
    let band = byPeriod.get(period)
    if (!band) {
      band = { period, price: slot.price_egp ?? 0, slots: [] }
      byPeriod.set(period, band)
    }
    const raw = slot.state
    const state: SlotState =
      raw === 'held' || raw === 'booked' || raw === 'available' ? raw : 'booked'
    band.slots.push({
      time,
      state: picked.has(time) && state === 'available' ? 'selected' : state,
    })
  }
  return (['morning', 'afternoon', 'evening'] as const)
    .map((period) => byPeriod.get(period))
    .filter((band): band is SlotBand => Boolean(band))
}

function priceForTimes(
  slots: Array<{ start_time?: string; price_egp?: number }>,
  times: string[],
) {
  return times.reduce((sum, time) => {
    const slot = slots.find((s) => s.start_time === time)
    return sum + (slot?.price_egp ?? 0)
  }, 0)
}
