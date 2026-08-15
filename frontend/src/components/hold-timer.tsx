import { useEffect, useRef, useState } from 'react'

import { formatHoldRemaining } from '@/lib/format'
import { cn } from '@/lib/utils'

type HoldTimerProps = {
  expiresAt: Date | number
  onExpire?: () => void
  className?: string
}

/** 10-minute hold countdown on confirm. */
export function HoldTimer({ expiresAt, onExpire, className }: HoldTimerProps) {
  const deadline = typeof expiresAt === 'number' ? expiresAt : expiresAt.getTime()
  const [remaining, setRemaining] = useState(() => deadline - Date.now())
  const onExpireRef = useRef(onExpire)
  onExpireRef.current = onExpire

  useEffect(() => {
    setRemaining(deadline - Date.now())
    const id = window.setInterval(() => {
      const next = deadline - Date.now()
      setRemaining(next)
      if (next <= 0) {
        window.clearInterval(id)
        onExpireRef.current?.()
      }
    }, 1000)
    return () => window.clearInterval(id)
  }, [deadline])

  const expired = remaining <= 0

  return (
    <p
      className={cn(
        'text-sm font-medium tabular-nums',
        expired || remaining < 60_000
          ? 'text-destructive'
          : 'text-slot-held-text',
        className,
      )}
      role="timer"
      aria-live="polite"
    >
      {expired
        ? 'Hold expired — pick another slot'
        : `⏱ Slot held · ${formatHoldRemaining(remaining)} left`}
    </p>
  )
}
