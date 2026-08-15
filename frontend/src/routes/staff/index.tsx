import { Link, createFileRoute, useNavigate } from '@tanstack/react-router'
import { useMemo, useState } from 'react'

import { ArrivalCard } from '@/components/staff-ops'
import { StaffShell } from '@/components/staff-shell'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { $api } from '@/lib/api/client'
import { clearStaffSession } from '@/lib/api/auth'
import { parseSlotStart, todayKey } from '@/lib/format'
import { requireStaff } from '@/lib/guards'
import { staffKind } from '@/lib/slot-states'

export const Route = createFileRoute('/staff/')({
  beforeLoad: () => {
    requireStaff()
  },
  component: StaffLookupPage,
})

function StaffLookupPage() {
  const navigate = useNavigate()
  const [code, setCode] = useState('')
  const today = todayKey()
  const list = $api.useQuery('get', '/staff/bookings', {
    params: { query: { date: today } },
  })

  const nextArrivals = useMemo(() => {
    const now = new Date()
    return (list.data?.bookings ?? [])
      .filter((b) => b.status === 'confirmed' && b.booking_code)
      .sort((a, b) => (a.start_time ?? '').localeCompare(b.start_time ?? ''))
      .slice(0, 3)
      .map((b) => {
        const start = parseSlotStart(today, b.start_time ?? '00:00')
        const end = parseSlotStart(today, b.end_time ?? '00:00')
        return {
          code: b.booking_code!,
          time: b.start_time ?? '',
          courtName: b.court_name ?? 'Court',
          kind: staffKind({
            status: 'paid',
            slotStart: start,
            slotEnd: end,
            now,
          }),
        }
      })
  }, [list.data?.bookings, today])

  function search(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = code.trim().toUpperCase()
    if (!trimmed) return
    void navigate({ to: '/staff/pass/$code', params: { code: trimmed } })
  }

  return (
    <StaffShell
      current="lookup"
      onLogout={() => {
        clearStaffSession()
        void navigate({ to: '/staff/login' })
      }}
    >
      <div className="grid gap-8 md:grid-cols-[1fr_320px]">
        <section className="flex flex-col gap-4">
          <h1 className="font-display text-2xl font-bold">Look up a booking</h1>
          <form className="flex flex-col gap-3" onSubmit={search}>
            <Label htmlFor="code">Enter code</Label>
            <Input
              id="code"
              autoFocus
              placeholder="MGZ-7F42K"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="font-mono tracking-wider uppercase"
            />
            <Button type="submit">Search</Button>
          </form>
          <Button variant="outline" asChild>
            <Link to="/staff/bookings">View today&apos;s bookings →</Link>
          </Button>
        </section>
        <aside className="flex flex-col gap-3">
          <h2 className="font-display text-lg font-semibold">
            Next arrivals ({nextArrivals.length})
          </h2>
          {nextArrivals.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No upcoming arrivals.
            </p>
          ) : (
            nextArrivals.map((arrival) => (
              <ArrivalCard
                key={arrival.code}
                time={arrival.time}
                courtName={arrival.courtName}
                code={arrival.code}
                kind={arrival.kind}
              />
            ))
          )}
        </aside>
      </div>
    </StaffShell>
  )
}
