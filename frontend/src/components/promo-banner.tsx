import type { ReactNode } from 'react'

import { MxIcon, SunLinear } from '@/lib/icons'
import { cn } from '@/lib/utils'

type PromoBannerProps = {
  title?: string
  subtitle?: string
  badge?: ReactNode
  className?: string
}

/** Morning deal banner — clay orange tokens from branding.md */
export function PromoBanner({
  title = 'Quiet mornings, lower price',
  subtitle = 'Before 12 PM — 30% off',
  badge,
  className,
}: PromoBannerProps) {
  return (
    <section
      className={cn(
        'rounded-[12px] border border-clay-orange/20 bg-promo-banner p-4',
        className,
      )}
    >
      <div className="flex items-start gap-3">
        <MxIcon
          icon={SunLinear}
          size={20}
          className="mt-0.5 text-clay-orange"
        />
        <div className="min-w-0 flex-1">
          <p className="font-display text-base font-semibold text-foreground">
            {title}
          </p>
          <p className="mt-1 text-sm text-clay-orange">{subtitle}</p>
        </div>
        {badge}
      </div>
    </section>
  )
}
