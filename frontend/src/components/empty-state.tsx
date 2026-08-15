import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

type EmptyStateProps = {
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export function EmptyState({
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center gap-3 rounded-[12px] border border-dashed border-border bg-card px-6 py-10 text-center',
        className,
      )}
    >
      <p className="font-display text-lg font-semibold">{title}</p>
      {description ? (
        <p className="max-w-xs text-sm text-muted-foreground">{description}</p>
      ) : null}
      {action}
    </div>
  )
}

type SpinnerProps = {
  label?: string
  className?: string
}

export function Spinner({ label, className }: SpinnerProps) {
  return (
    <div
      role="status"
      className={cn('flex flex-col items-center gap-3', className)}
    >
      <span
        className="size-8 animate-spin rounded-full border-2 border-muted border-t-court-green"
        aria-hidden
      />
      {label ? <p className="text-sm text-muted-foreground">{label}</p> : null}
      <span className="sr-only">{label ?? 'Loading'}</span>
    </div>
  )
}
