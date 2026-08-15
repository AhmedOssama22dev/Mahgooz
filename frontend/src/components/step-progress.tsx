import { cn } from '@/lib/utils'

type StepProgressProps = {
  steps: string[]
  current: number
  className?: string
}

/** Booking wizard progress — filled dots for completed/current */
export function StepProgress({ steps, current, className }: StepProgressProps) {
  return (
    <div className={cn('flex items-center gap-2', className)} role="list">
      {steps.map((label, index) => {
        const active = index <= current
        return (
          <div key={label} className="flex items-center gap-2" role="listitem">
            <span
              className={cn(
                'size-2.5 rounded-full',
                active ? 'bg-court-green' : 'bg-muted',
              )}
              title={label}
              aria-current={index === current ? 'step' : undefined}
            />
            {index < steps.length - 1 ? (
              <span
                className={cn(
                  'h-px w-4 sm:w-6',
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
