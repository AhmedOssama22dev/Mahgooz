/** Same alphabet as issued codes: no I/O/0/1. */
const CODE_RE = /MGZ-[A-HJ-NP-Z2-9]{5}/i

/** Pull `MGZ-XXXXX` from a scanned QR (pass URL or raw code). */
export function bookingCodeFromQr(raw: string): string | null {
  const text = raw.trim()
  if (!text) return null

  let candidate = text
  try {
    const url = new URL(text, 'https://mahgooz.app')
    const parts = url.pathname.split('/').filter(Boolean)
    const passAt = parts.findIndex((p) => p.toLowerCase() === 'pass')
    const fromPath = passAt >= 0 ? parts[passAt + 1] : undefined
    if (fromPath) candidate = decodeURIComponent(fromPath)
  } catch {
    /* raw code or non-URL */
  }

  const match = candidate.toUpperCase().replace(/\s+/g, '').match(CODE_RE)
  return match?.[0] ?? null
}
