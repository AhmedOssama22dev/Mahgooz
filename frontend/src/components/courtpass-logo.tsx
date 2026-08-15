import { cn } from '@/lib/utils'

export function CourtPassLogo({
  className,
  variant = 'default',
}: {
  className?: string
  variant?: 'default' | 'on-dark'
}) {
  const iconClass =
    variant === 'on-dark' ? 'text-court-green' : 'text-court-green'
  const textClass =
    variant === 'on-dark'
      ? 'text-foreground'
      : 'text-foreground dark:text-foreground'

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <svg
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
        className={cn('size-6 shrink-0', iconClass)}
      >
        <ellipse
          cx="12"
          cy="8"
          rx="7"
          ry="5.5"
          stroke="currentColor"
          strokeWidth="1.75"
        />
        <path
          d="M12 13.5V21"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
        />
        <path
          d="M10 21H14"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
        />
      </svg>
      <span className={cn('font-display text-lg font-bold tracking-tight', textClass)}>
        CourtPass
      </span>
    </div>
  )
}
