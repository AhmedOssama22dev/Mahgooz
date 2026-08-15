import type { ComponentType } from 'react'
import type { IconProps } from 'mx-icons'
import { ArrowRightLinear } from 'mx-icons/components/arrow-right'
import { CalendarLinear } from 'mx-icons/components/calendar'
import { CardLinear } from 'mx-icons/components/card'
import { LocationLinear } from 'mx-icons/components/location'
import { MoonLinear } from 'mx-icons/components/moon'
import { ScanLinear } from 'mx-icons/components/scan'
import { SunLinear } from 'mx-icons/components/sun'

import { cn } from '@/lib/utils'

export {
  ArrowRightLinear,
  CalendarLinear,
  CardLinear,
  LocationLinear,
  MoonLinear,
  ScanLinear,
  SunLinear,
}

export function MxIcon({
  icon: Icon,
  className,
  size = 24,
}: {
  icon: ComponentType<IconProps>
  className?: string
  size?: number | string
}) {
  return (
    <Icon size={size} color="currentColor" className={cn('shrink-0', className)} />
  )
}
