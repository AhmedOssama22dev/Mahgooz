import { clsx } from 'clsx'
import type { ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function apiErrorMessage(
  err: unknown,
  fallback = 'Something went wrong',
): string {
  if (!err || typeof err !== 'object') {
    return err instanceof Error ? err.message : fallback
  }
  const body = err as { error?: { message?: string }; message?: string }
  return body.error?.message ?? body.message ?? fallback
}

/** Only in-app paths — blocks open redirects. */
export function safeRedirect(path: string | undefined, fallback: string) {
  if (path?.startsWith('/') && !path.startsWith('//')) return path
  return fallback
}
