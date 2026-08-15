import { cn } from '@/lib/utils'

type CourtCardProps = {
  name: string
  detail?: string
  slotsAvailable: number
  selected?: boolean
  onSelect?: () => void
  className?: string
}

/** Court 1 / Court 2 picker — tap selects and pages auto-advance. */
export function CourtCard({
  name,
  detail = 'Outdoor · 4 players',
  slotsAvailable,
  selected = false,
  onSelect,
  className,
}: CourtCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={cn(
        'flex w-full flex-col items-start rounded-[12px] border bg-card p-4 text-left shadow-[0_1px_3px_rgba(15,26,20,0.06)] transition-colors focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none dark:shadow-none',
        selected
          ? 'border-court-green ring-2 ring-court-green/30'
          : 'border-border hover:border-court-green/40',
        className,
      )}
    >
      <p className="font-display text-[17px] font-semibold">{name}</p>
      <p className="mt-1 text-sm text-muted-foreground">{detail}</p>
      <p className="mt-3 text-sm font-medium text-primary">
        {slotsAvailable} {slotsAvailable === 1 ? 'slot' : 'slots'} available
      </p>
    </button>
  )
}
