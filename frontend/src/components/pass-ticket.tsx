import { Copy } from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type PassQrProps = {
  value: string
  size?: number
  className?: string
}

export function PassQr({ value, size = 180, className }: PassQrProps) {
  return (
    <div
      className={cn(
        'flex items-center justify-center rounded-[12px] bg-white p-4',
        className,
      )}
    >
      <QRCodeSVG value={value} size={size} level="M" title={`QR code ${value}`} />
    </div>
  )
}

type PassCodeProps = {
  code: string
  className?: string
}

export function PassCode({ code, className }: PassCodeProps) {
  async function copy() {
    try {
      await navigator.clipboard.writeText(code)
      toast.success('Code copied')
    } catch {
      toast.error('Could not copy')
    }
  }

  return (
    <div className={cn('flex flex-col items-center gap-3', className)}>
      <p className="font-mono text-[28px] leading-[1.2] font-medium tracking-widest">
        {code}
      </p>
      <Button type="button" variant="outline" size="sm" onClick={copy}>
        <Copy className="size-4" />
        Copy code
      </Button>
    </div>
  )
}
