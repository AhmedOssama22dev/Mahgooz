import { Link, createFileRoute, useNavigate } from '@tanstack/react-router'
import { addDays, format, parseISO } from 'date-fns'
import { useMemo, useState } from 'react'

import { StatusBadge, staffKindToBadge } from '@/components/status-badge'
import { FilterChips, StatsRow } from '@/components/staff-ops'
import type { StaffFilter } from '@/components/staff-ops'
import { StaffShell } from '@/components/staff-shell'
import { Button } from '@/components/ui/button'
import { $api } from '@/lib/api/client'
import { clearStaffSession } from '@/lib/api/auth'
import { parseSlotStart, todayKey } from '@/lib/format'
import { requireStaff } from '@/lib/guards'
import { staffKind } from '@/lib/slot-states'
import type { StaffBookingKind } from '@/lib/slot-states'

type StaffBookingsSearch = {
  date?: string
}

export const Route = createFileRoute('/staff/bookings')({
  validateSearch: (search: Record<string, unknown>): StaffBookingsSearch => ({
    date: typeof search.date === 'string' ? search.date : undefined,
  }),
  beforeLoad: () => {
    requireStaff()
  },
  component: StaffBookingsPage,
})

type Row = {
  code: string
  courtName: string
  startTime: string
  endTime: string
  bookerName: string
  kind: StaffBookingKind
  canRedeem: boolean
}

function StaffBookingsPage() {
  const navigate = useNavigate()
  const { date: dateParam } = Route.useSearch()
  const date = dateParam ?? todayKey()
  const [filter, setFilter] = useState<StaffFilter>('all')
  const list = $api.useQuery('get', '/staff/bookings', {
    params: { query: { date } },
  })

  const rows = useMemo<Row[]>(() => {
    const now = new Date()
    return (list.data?.bookings ?? [])
      .filter((b) => b.booking_code)
      .map((b) => {
        const start = parseSlotStart(date, b.start_time ?? '00:00')
        const end = parseSlotStart(date, b.end_time ?? '00:00')
        const kind = staffKind({
          status: b.status === 'redeemed' ? 'redeemed' : 'paid',
          slotStart: start,
          slotEnd: end,
          now,
        })
        return {
          code: b.booking_code!,
          courtName: b.court_name ?? 'Court',
          startTime: b.start_time ?? '',
          endTime: b.end_time ?? '',
          bookerName: b.booker_name ?? '',
          kind,
          canRedeem: kind === 'ready',
        }
      })
      .sort((a, b) => a.startTime.localeCompare(b.startTime))
  }, [date, list.data?.bookings])

  const filtered = rows.filter((row) => matchesFilter(row, filter))
  const stats = {
    booked: rows.length,
    checkedIn: rows.filter((r) => r.kind === 'redeemed').length,
    upcoming: rows.filter((r) => r.kind === 'upcoming' || r.kind === 'ready')
      .length,
    noShow: rows.filter((r) => r.kind === 'no-show').length,
  }

  const label = format(parseISO(date), 'EEE d MMM')

  function shift(days: number) {
    const next = format(addDays(parseISO(date), days), 'yyyy-MM-dd')
    void navigate({ to: '/staff/bookings', search: { date: next } })
  }

  return (
    <StaffShell
      current="bookings"
      onLogout={() => {
        clearStaffSession()
        void navigate({ to: '/staff/login' })
      }}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-2xl font-bold">
          Today&apos;s bookings · {label}
        </h1>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => shift(-1)}>
            ‹
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              void navigate({
                to: '/staff/bookings',
                search: { date: todayKey() },
              })
            }
          >
            Today
          </Button>
          <Button variant="outline" size="sm" onClick={() => shift(1)}>
            ›
          </Button>
        </div>
      </div>

      <StatsRow
        booked={stats.booked}
        checkedIn={stats.checkedIn}
        upcoming={stats.upcoming}
        noShow={stats.noShow}
      />
      <FilterChips value={filter} onChange={setFilter} />

      <div className="flex flex-col gap-3 md:hidden">
        {filtered.map((row) => (
          <article
            key={row.code}
            className="flex flex-col gap-3 rounded-[12px] border border-border bg-card p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-display font-semibold">
                  {row.startTime}
                  {row.endTime ? `–${row.endTime}` : ''} · {row.courtName}
                </p>
                <p className="text-sm text-muted-foreground">
                  {row.bookerName}
                </p>
                <p className="font-mono text-xs tracking-wider">{row.code}</p>
              </div>
              <StatusBadge status={staffKindToBadge(row.kind)} />
            </div>
            <Button variant="outline" size="sm" asChild>
              <Link to="/staff/pass/$code" params={{ code: row.code }}>
                {row.canRedeem ? 'Redeem' : 'View'}
              </Link>
            </Button>
          </article>
        ))}
      </div>

      <div className="hidden overflow-x-auto md:block">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="border-b border-border text-muted-foreground">
            <tr>
              <th className="py-3 pr-4 font-medium">Time</th>
              <th className="py-3 pr-4 font-medium">Court</th>
              <th className="py-3 pr-4 font-medium">Customer</th>
              <th className="py-3 pr-4 font-medium">Status</th>
              <th className="py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <tr key={row.code} className="border-b border-border">
                <td className="py-3 pr-4 tabular-nums">
                  {row.startTime}
                  {row.endTime ? `–${row.endTime}` : ''}
                </td>
                <td className="py-3 pr-4">{row.courtName}</td>
                <td className="py-3 pr-4">{row.bookerName}</td>
                <td className="py-3 pr-4">
                  <StatusBadge status={staffKindToBadge(row.kind)} />
                </td>
                <td className="py-3">
                  <Button variant="outline" size="sm" asChild>
                    <Link to="/staff/pass/$code" params={{ code: row.code }}>
                      {row.canRedeem ? 'Redeem' : 'View'}
                    </Link>
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </StaffShell>
  )
}

function matchesFilter(row: Row, filter: StaffFilter) {
  if (filter === 'all') return true
  if (filter === 'court-1') return /1/.test(row.courtName)
  if (filter === 'court-2') return /2/.test(row.courtName)
  if (filter === 'paid') return row.kind === 'ready' || row.kind === 'upcoming'
  if (filter === 'redeemed') return row.kind === 'redeemed'
  return row.kind === 'no-show'
}
