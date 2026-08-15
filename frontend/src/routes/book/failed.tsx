import { Link, createFileRoute } from '@tanstack/react-router'

import { CustomerLayout } from '@/components/customer-layout'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { requireCustomer } from '@/lib/guards'

export const Route = createFileRoute('/book/failed')({
  beforeLoad: ({ location }) => {
    requireCustomer(`${location.pathname}${location.searchStr}`)
  },
  component: BookFailedPage,
})

function BookFailedPage() {
  return (
    <CustomerLayout>
      <Card className="mx-auto w-full max-w-md">
        <CardContent className="flex flex-col items-center gap-4 py-10 text-center">
          <span
            className="flex size-12 items-center justify-center rounded-full bg-destructive/10 text-2xl text-destructive"
            aria-hidden
          >
            ✕
          </span>
          <h1 className="font-display text-2xl font-bold">
            Payment didn&apos;t go through
          </h1>
          <p className="text-sm text-muted-foreground">
            Your slot has been released for others.
          </p>
          <Button className="w-full" asChild>
            <Link to="/book">Try another slot</Link>
          </Button>
          <Button variant="outline" className="w-full" asChild>
            <Link to="/">Back to home</Link>
          </Button>
        </CardContent>
      </Card>
    </CustomerLayout>
  )
}
