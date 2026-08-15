import { cn } from '@/lib/utils'

type StepProgressProps = {
  steps: string[]
  current: number
  className?: string
}

/** Booking wizard progress — filled dots for completed/current */
export function StepProgress({ steps, current, className }: StepProgressProps) {
  return (
    <div
      className={cn('flex w-full items-center', className)}
      role="list"
    >
      {steps.map((label, index) => {
        const active = index <= current
        return (
          <div
            key={label}
            className={cn(
              'flex items-center',
              index < steps.length - 1 && 'min-w-0 flex-1',
            )}
            role="listitem"
          >
            <span
              className={cn(
                'size-2.5 shrink-0 rounded-full',
                active ? 'bg-court-green' : 'bg-muted',
              )}
              title={label}
              aria-current={index === current ? 'step' : undefined}
            />
            {index < steps.length - 1 ? (
              <span
                className={cn(
                  'mx-2 h-px min-w-0 flex-1',
                  index < current ? 'bg-court-green' : 'bg-muted',
                )}
              />
            ) : null}
          </div>
        )
      })}
    </div>
  )
}
