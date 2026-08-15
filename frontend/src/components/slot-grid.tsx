import { SlotChip } from '@/components/slot-chip'
import { formatEgp } from '@/lib/format'
import {
  PERIOD_META,
  type Period,
  type SlotState,
} from '@/lib/slot-states'
import { cn } from '@/lib/utils'

export type SlotItem = {
  time: string
  state: SlotState
}

export type SlotBand = {
  period: Period
  price: number
  slots: SlotItem[]
}

type SlotGridProps = {
  bands: SlotBand[]
  onSelect: (time: string) => void
  className?: string
}

export function SlotGrid({ bands, onSelect, className }: SlotGridProps) {
  return (
    <div className={cn('flex flex-col gap-6', className)}>
      {bands.map((band) => (
        <section key={band.period} className="flex flex-col gap-3">
          <div className="flex items-baseline justify-between">
            <h2 className="font-display text-base font-semibold">
              {PERIOD_META[band.period].label}
            </h2>
            <p className="text-sm text-muted-foreground tabular-nums">
              {formatEgp(band.price)}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {band.slots.map((slot) => (
              <SlotChip
                key={slot.time}
                time={slot.time}
                state={slot.state}
                onClick={() => onSelect(slot.time)}
              />
            ))}
          </div>
        </section>
      ))}
      <SlotLegend />
    </div>
  )
}

export function SlotLegend({ className }: { className?: string }) {
  return (
    <p className={cn('text-xs text-muted-foreground', className)}>
      Legend: open · taken · paying
    </p>
  )
}
