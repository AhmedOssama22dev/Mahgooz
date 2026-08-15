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
import { registerSchema } from '@/lib/schemas'
import { apiErrorMessage, safeRedirect } from '@/lib/utils'

type RegisterSearch = {
  redirect?: string
}

export const Route = createFileRoute('/register')({
  validateSearch: (search: Record<string, unknown>): RegisterSearch => ({
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
  component: RegisterPage,
})

function RegisterPage() {
  const navigate = useNavigate()
  const { redirect: next } = Route.useSearch()
  const register = $api.useMutation('post', '/auth/register')
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [fieldErrors, setFieldErrors] = useState<{
    name?: string
    phone?: string
    password?: string
  }>({})

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const parsed = registerSchema.safeParse({ name, phone, password })
    if (!parsed.success) {
      const nextErrors: { name?: string; phone?: string; password?: string } =
        {}
      for (const issue of parsed.error.issues) {
        const key = issue.path[0]
        if (key === 'name' || key === 'phone' || key === 'password') {
          nextErrors[key] = issue.message
        }
      }
      setFieldErrors(nextErrors)
      return
    }
    setFieldErrors({})
    try {
      const data = await register.mutateAsync({ body: parsed.data })
      saveAuthTokens(data)
      await navigate({
        to: safeRedirect(next, defaultHomePath(parseRole(data.user?.role))),
      })
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Could not create account'))
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
      <Card className="mx-auto w-full max-w-[440px]">
        <CardHeader>
          <CardTitle className="font-display text-2xl font-bold">
            Create your account
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Book courts in seconds
          </p>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-4" onSubmit={onSubmit}>
            <Field label="Name" htmlFor="name" error={fieldErrors.name}>
              <Input
                id="name"
                autoComplete="name"
                value={name}
                aria-invalid={Boolean(fieldErrors.name)}
                onChange={(e) => setName(e.target.value)}
              />
            </Field>
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
                autoComplete="new-password"
                value={password}
                aria-invalid={Boolean(fieldErrors.password)}
                onChange={(e) => setPassword(e.target.value)}
              />
            </Field>
            <Button
              type="submit"
              className="w-full"
              disabled={register.isPending}
            >
              {register.isPending ? 'Creating…' : 'Create account'}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-muted-foreground">
            Already have one?{' '}
            <Link
              to="/login"
              search={next ? { redirect: next } : undefined}
              className="font-medium text-primary underline-offset-4 hover:underline"
            >
              Log in
            </Link>
          </p>
        </CardContent>
      </Card>
    </AppShell>
  )
}
