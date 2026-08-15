import {
  Link,
  createFileRoute,
  redirect,
  useNavigate,
} from '@tanstack/react-router'
import { useState } from 'react'
import { toast } from 'sonner'

import { AppShell } from '@/components/app-shell'
import { Field } from '@/components/field'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { $api } from '@/lib/api/client'
import {
  defaultHomePath,
  getAccessToken,
  getSessionUser,
  parseRole,
  saveAuthTokens,
} from '@/lib/api/auth'
import { loginSchema } from '@/lib/schemas'
import { apiErrorMessage, safeRedirect } from '@/lib/utils'

type LoginSearch = {
  redirect?: string
}

export const Route = createFileRoute('/login')({
  validateSearch: (search: Record<string, unknown>): LoginSearch => ({
    redirect: typeof search.redirect === 'string' ? search.redirect : undefined,
  }),
  beforeLoad: ({ search }) => {
    if (getAccessToken()) {
      throw redirect({
        to: safeRedirect(
          search.redirect,
          defaultHomePath(getSessionUser()?.role),
        ),
      })
    }
  },
  component: LoginPage,
})

function LoginPage() {
  const navigate = useNavigate()
  const { redirect: next } = Route.useSearch()
  const login = $api.useMutation('post', '/auth/login')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [fieldErrors, setFieldErrors] = useState<{
    phone?: string
    password?: string
  }>({})

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const parsed = loginSchema.safeParse({ phone, password })
    if (!parsed.success) {
      const nextErrors: { phone?: string; password?: string } = {}
      for (const issue of parsed.error.issues) {
        const key = issue.path[0]
        if (key === 'phone' || key === 'password')
          nextErrors[key] = issue.message
      }
      setFieldErrors(nextErrors)
      return
    }
    setFieldErrors({})
    try {
      const data = await login.mutateAsync({ body: parsed.data })
      saveAuthTokens(data)
      await navigate({
        to: safeRedirect(next, defaultHomePath(parseRole(data.user?.role))),
      })
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Phone or password is incorrect'))
    }
  }

  return (
    <AppShell>
      <Button
        variant="ghost"
        size="sm"
        className="self-start text-muted-foreground"
        asChild
      >
        <Link to="/">← Home</Link>
      </Button>
      <Card className="mx-auto w-full max-w-[400px]">
        <CardHeader>
          <CardTitle className="font-display text-2xl font-bold">
            Welcome back
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-4" onSubmit={onSubmit}>
            <Field label="Phone" htmlFor="phone" error={fieldErrors.phone}>
              <Input
                id="phone"
                type="tel"
                inputMode="numeric"
                autoComplete="tel"
                placeholder="01xxxxxxxxx"
                value={phone}
                aria-invalid={Boolean(fieldErrors.phone)}
                onChange={(e) => setPhone(e.target.value)}
              />
            </Field>
            <Field
              label="Password"
              htmlFor="password"
              error={fieldErrors.password}
            >
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                aria-invalid={Boolean(fieldErrors.password)}
                onChange={(e) => setPassword(e.target.value)}
              />
            </Field>
            <Button type="submit" className="w-full" disabled={login.isPending}>
              {login.isPending ? 'Logging in…' : 'Log in'}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-muted-foreground">
            New here?{' '}
            <Link
              to="/register"
              search={next ? { redirect: next } : undefined}
              className="font-medium text-primary underline-offset-4 hover:underline"
            >
              Create account
            </Link>
          </p>
        </CardContent>
      </Card>
    </AppShell>
  )
}
