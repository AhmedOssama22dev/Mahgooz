import { Link } from '@tanstack/react-router'

import { AppShell } from '@/components/app-shell'
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
import { createFileRoute } from '@tanstack/react-router'
import type { IconProps } from 'mx-icons'
import type { ComponentType } from 'react'

export const Route = createFileRoute('/')({
  component: LandingPage,
})

const HERO_IMAGE =
  'https://images.unsplash.com/photo-1554068865-24cecd4e34b8?auto=format&fit=crop&w=1200&q=80'

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

const COURTS = [
  { name: 'Court 1', slots: 3 },
  { name: 'Court 2', slots: 5 },
] as const

function LandingPage() {
  return (
    <AppShell
      width="wide"
      headerRight={
        <Button variant="link" className="text-primary" asChild>
          <Link to="/login">Log in</Link>
        </Button>
      }
    >
      <section className="relative overflow-hidden rounded-[16px]">
        <img
          src={HERO_IMAGE}
          alt="Padel court at golden hour"
          className="aspect-[4/3] w-full object-cover md:aspect-[21/9]"
        />
        <div className="hero-scrim absolute inset-0" />
        <div className="absolute inset-0 flex flex-col justify-end p-6 text-[#f4f7f5]">
          <h1 className="font-display text-[32px] leading-[1.15] font-bold">
            Book. Pay. Play.
          </h1>
          <p className="mt-2 text-base text-white/90">Sheikh Zayed • 2 courts</p>
          <Button className="mt-6 w-full" size="lg" asChild>
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
                <div className="mt-3 flex size-10 items-center justify-center text-primary">
                  <MxIcon icon={icon} size={24} />
                </div>
                <p className="mt-2 font-display text-[17px] font-semibold leading-snug">
                  {title}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">{description}</p>
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
      />

      <section>
        <h2 className="font-display text-xl font-semibold">Today at a glance</h2>
        <Card className="mt-4 gap-0 py-0">
          {COURTS.map((court, index) => (
            <div key={court.name}>
              {index > 0 ? <Separator /> : null}
              <Link
                to="/book"
                className="flex min-h-11 items-center gap-3 px-4 py-4 transition-colors hover:bg-muted/40"
              >
                <span className="size-2.5 shrink-0 rounded-full bg-court-green" />
                <div className="min-w-0 flex-1">
                  <p className="font-display font-semibold">{court.name}</p>
                  <p className="text-sm text-primary">{court.slots} slots left</p>
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
    </AppShell>
  )
}
