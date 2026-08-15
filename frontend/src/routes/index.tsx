import { Link, createFileRoute } from '@tanstack/react-router'

import { CustomerLayout } from '@/components/customer-layout'
import { PromoBanner } from '@/components/promo-banner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import {
  ArrowRightLinear,
  CalendarLinear,
  CardLinear,
  LocationLinear,
  MxIcon,
  ScanLinear,
} from '@/lib/icons'
import { $api } from '@/lib/api/client'
import { todayKey } from '@/lib/format'
import type { IconProps } from 'mx-icons'
import type { ComponentType } from 'react'

export const Route = createFileRoute('/')({
  component: LandingPage,
})

const HERO_IMAGE = '/hero-padel.jpg'

const STEPS: {
  step: number
  icon: ComponentType<IconProps>
  title: string
  description: string
}[] = [
  {
    step: 1,
    icon: CalendarLinear,
    title: 'Pick slot',
    description: 'Choose court & time',
  },
  {
    step: 2,
    icon: CardLinear,
    title: 'Pay',
    description: 'Secure via Paymob',
  },
  {
    step: 3,
    icon: ScanLinear,
    title: 'Pass',
    description: 'Show QR on arrival',
  },
]

function LandingPage() {
  const today = todayKey()
  const courts = $api.useQuery('get', '/courts')
  const courtA = courts.data?.[0]
  const courtB = courts.data?.[1]
  const slotsA = $api.useQuery(
    'get',
    '/slots',
    { params: { query: { date: today, court_id: courtA?.id } } },
    { enabled: Boolean(courtA?.id) },
  )
  const slotsB = $api.useQuery(
    'get',
    '/slots',
    { params: { query: { date: today, court_id: courtB?.id } } },
    { enabled: Boolean(courtB?.id) },
  )

  const availability = [
    {
      name: courtA?.name ?? 'Court 1',
      slots: countAvailable(slotsA.data?.slots),
    },
    {
      name: courtB?.name ?? 'Court 2',
      slots: countAvailable(slotsB.data?.slots),
    },
  ]

  return (
    <CustomerLayout width="wide" showBookCta>
      <section className="relative overflow-hidden rounded-[16px]">
        <img
          src={HERO_IMAGE}
          alt="Players on a blue padel court"
          className="aspect-4/3 w-full object-cover md:aspect-21/9 md:min-h-80"
        />
        <div className="hero-scrim absolute inset-0" />
        <div className="absolute inset-0 flex flex-col justify-end p-6 text-[#f4f7f5] md:p-10">
          <h1 className="font-display text-[32px] leading-[1.15] font-bold md:text-5xl">
            Book. Pay. Play.
          </h1>
          <p className="mt-2 text-base text-white/90 md:text-lg">
            Sheikh Zayed • 2 courts
          </p>
          <Button className="mt-6 w-full md:w-fit" size="lg" asChild>
            <Link to="/book">Book a court</Link>
          </Button>
        </div>
      </section>

      <section>
        <h2 className="font-display text-xl font-semibold">How it works</h2>
        <div className="mt-4 grid grid-cols-3 gap-3">
          {STEPS.map(({ step, icon, title, description }) => (
            <Card key={step} className="gap-3 py-4 shadow-sm">
              <CardContent className="flex flex-col items-center px-3 text-center">
                <span className="flex size-7 items-center justify-center rounded-full bg-muted text-xs font-medium text-muted-foreground">
                  {step}
                </span>
                <div className="mt-3 flex items-center justify-center gap-2 text-primary">
                  <MxIcon icon={icon} size={24} />
                  <p className="font-display text-[17px] leading-snug font-semibold text-foreground">
                    {title}
                  </p>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">
                  {description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <PromoBanner
        badge={
          <Badge className="shrink-0 bg-clay-orange px-2.5 py-1 text-xs font-semibold text-white hover:bg-clay-orange">
            30% OFF
          </Badge>
        }
        action={
          <Button variant="outline" className="mt-4 w-full" asChild>
            <Link to="/book" search={{ period: 'morning' }}>
              See morning slots
            </Link>
          </Button>
        }
      />

      <section>
        <h2 className="font-display text-xl font-semibold">
          Today at a glance
        </h2>
        <Card className="mt-4 gap-0 py-0">
          {availability.map((court, index) => (
            <div key={court.name}>
              {index > 0 ? <Separator /> : null}
              <Link
                to="/book"
                className="flex min-h-11 items-center gap-3 px-4 py-4 transition-colors hover:bg-muted/40"
              >
                <span className="size-2.5 shrink-0 rounded-full bg-court-green" />
                <div className="min-w-0 flex-1">
                  <p className="font-display font-semibold">{court.name}</p>
                  <p className="text-sm text-primary">
                    {court.slots == null
                      ? 'Checking…'
                      : `${court.slots} slots left`}
                  </p>
                </div>
                <MxIcon
                  icon={ArrowRightLinear}
                  size={20}
                  className="text-muted-foreground"
                />
              </Link>
            </div>
          ))}
        </Card>
      </section>

      <footer className="border-t border-border pt-6 text-sm text-muted-foreground">
        <div className="flex flex-col gap-3">
          <p className="flex items-center gap-2">
            <MxIcon icon={LocationLinear} size={16} />
            Sheikh Zayed, Egypt
          </p>
          <p>
            Need help?{' '}
            <a
              href="https://wa.me/"
              className="text-primary underline-offset-4 hover:underline"
            >
              WhatsApp Mostafa
            </a>
          </p>
          <Link
            to="/staff/login"
            className="text-xs text-muted-foreground underline-offset-4 hover:underline"
          >
            Staff login
          </Link>
        </div>
      </footer>
    </CustomerLayout>
  )
}

function countAvailable(slots: Array<{ state?: string }> | undefined) {
  if (!slots) return undefined
  return slots.filter((slot) => slot.state === 'available').length
}
