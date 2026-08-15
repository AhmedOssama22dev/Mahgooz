import type { ReactNode } from 'react'

import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

type FieldProps = {
  label: string
  htmlFor: string
  error?: string
  children: ReactNode
  className?: string
  hint?: string
}

/** Label + control + error — use with TanStack Form field state */
export function Field({
  label,
  htmlFor,
  error,
  children,
  className,
  hint,
}: FieldProps) {
  return (
    <div className={cn('flex flex-col gap-2', className)}>
      <Label htmlFor={htmlFor} className="text-sm font-medium">
        {label}
      </Label>
      {children}
      {hint && !error ? (
        <p className="text-sm text-muted-foreground">{hint}</p>
      ) : null}
      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  )
}
