import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

type StickyFooterCTAProps = {
  children: ReactNode
  className?: string
}

/** Thumb-zone primary action on booking steps. */
export function StickyFooterCTA({ children, className }: StickyFooterCTAProps) {
  return (
    <div
      className={cn(
        'sticky bottom-0 z-20 border-t border-border bg-background/95 p-4 pb-[max(1rem,env(safe-area-inset-bottom))] backdrop-blur',
        className,
      )}
    >
      {children}
    </div>
  )
}
