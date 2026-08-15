import { Link } from '@tanstack/react-router'
import type { ReactNode } from 'react'

import { CourtPassLogo } from '@/components/courtpass-logo'
import { ThemeToggle } from '@/components/theme-toggle'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type AppShellProps = {
  children: ReactNode
  /** Narrow mobile shell (auth, book, pass). Landing uses `wide`. */
  width?: 'narrow' | 'wide'
  headerRight?: ReactNode
  showThemeToggle?: boolean
  className?: string
}

/**
 * Shared page chrome: bg, gutters, max-width.
 * Use on every customer page so layout stays consistent.
 */
export function AppShell({
  children,
  width = 'narrow',
  headerRight,
  showThemeToggle = true,
  className,
}: AppShellProps) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div
        className={cn(
          'mx-auto flex min-h-screen flex-col',
          width === 'narrow' ? 'max-w-[480px]' : 'max-w-[480px] md:max-w-5xl',
          className,
        )}
      >
        <header className="flex items-center justify-between px-4 py-4 md:px-6">
          <Link to="/" className="shrink-0">
            <CourtPassLogo />
          </Link>
          <div className="flex items-center gap-1">
            {showThemeToggle ? <ThemeToggle /> : null}
            {headerRight}
          </div>
        </header>
        <main className="flex flex-1 flex-col gap-6 px-4 pb-8 md:px-6 md:pb-12">
          {children}
        </main>
      </div>
    </div>
  )
}

type PageHeaderProps = {
  title: string
  backTo?: string
  backLabel?: string
  className?: string
}

/** Auth / wizard top bar: optional back + page title */
export function PageHeader({
  title,
  backTo = '/',
  backLabel = 'Back',
  className,
}: PageHeaderProps) {
  return (
    <div className={cn('flex items-center gap-3', className)}>
      <Button variant="ghost" size="sm" className="text-muted-foreground" asChild>
        <Link to={backTo}>{backLabel}</Link>
      </Button>
      <h1 className="font-display text-xl font-semibold">{title}</h1>
    </div>
  )
}
