import { Delete } from 'lucide-react'
import { useEffect, useState, type ButtonHTMLAttributes, type ReactNode } from 'react'

import { cn } from '@/lib/utils'

const KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9'] as const

type PinPadProps = {
  length?: number
  error?: boolean
  onSubmit: (pin: string) => void
  className?: string
}

/** Staff 4-digit PIN. Submit with ✓ — wrong PIN should set `error`. */
export function PinPad({
  length = 4,
  error = false,
  onSubmit,
  className,
}: PinPadProps) {
  const [value, setValue] = useState('')

  useEffect(() => {
    if (error) setValue('')
  }, [error])

  function push(digit: string) {
    setValue((prev) => (prev.length >= length ? prev : prev + digit))
  }

  function backspace() {
    setValue((prev) => prev.slice(0, -1))
  }

  function submit() {
    if (value.length === length) onSubmit(value)
  }

  return (
    <div className={cn('flex flex-col items-center gap-6', className)}>
      <div
        className={cn('flex gap-3', error && 'animate-shake')}
        aria-label="PIN"
      >
        {Array.from({ length }, (_, i) => (
          <span
            key={i}
            className={cn(
              'size-4 rounded-full border-2',
              i < value.length
                ? 'border-court-green bg-court-green'
                : 'border-border bg-transparent',
            )}
          />
        ))}
      </div>
      {error ? (
        <p className="text-sm text-destructive" role="alert">
          Incorrect PIN
        </p>
      ) : null}
      <div className="grid grid-cols-3 gap-3">
        {KEYS.map((key) => (
          <KeyButton key={key} onClick={() => push(key)}>
            {key}
          </KeyButton>
        ))}
        <KeyButton onClick={backspace} aria-label="Delete">
          <Delete className="size-5" />
        </KeyButton>
        <KeyButton onClick={() => push('0')}>0</KeyButton>
        <KeyButton
          onClick={submit}
          aria-label="Submit PIN"
          className="bg-court-green text-white hover:bg-court-green-dark"
        >
          ✓
        </KeyButton>
      </div>
    </div>
  )
}

function KeyButton({
  children,
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode }) {
  return (
    <button
      type="button"
      className={cn(
        'flex size-16 items-center justify-center rounded-[12px] border border-border bg-card font-display text-xl font-semibold focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none',
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}
