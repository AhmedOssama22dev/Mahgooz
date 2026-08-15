import { Link, createFileRoute } from '@tanstack/react-router'

import { AppShell } from '@/components/app-shell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export const Route = createFileRoute('/forgot-password')({
  component: ForgotPasswordPage,
})

function ForgotPasswordPage() {
  return (
    <AppShell>
      <Button
        variant="ghost"
        size="sm"
        className="self-start text-muted-foreground"
        asChild
      >
        <Link to="/login">← Log in</Link>
      </Button>
      <Card className="mx-auto w-full max-w-[400px]">
        <CardHeader>
          <CardTitle className="font-display text-2xl font-bold">
            Reset password
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            Ask Mostafa at the desk — he can reset your account in a minute.
          </p>
          <Button asChild>
            <Link to="/login">Back to log in</Link>
          </Button>
        </CardContent>
      </Card>
    </AppShell>
  )
}
