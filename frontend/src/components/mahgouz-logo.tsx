import { cn } from '@/lib/utils'

export function MahgouzLogo({ className }: { className?: string }) {
  return (
    <img
      src="/mahgouz-logo-badge.png"
      alt="Mahgouz"
      width={56}
      height={56}
      className={cn('size-14 shrink-0 object-contain', className)}
    />
  )
}
