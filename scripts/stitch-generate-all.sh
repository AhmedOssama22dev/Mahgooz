#!/usr/bin/env bash
# ponytail: batch-generate CourtPass screens in Stitch (light then dark)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
set -a && source "$ROOT/.env" && set +a

PROJECT_ID="7191702240633724843"
DS="assets/e03cc309c60b436bbc38e48fd719a96f"
STITCH="$ROOT/docs/stitch"
LOG="$STITCH/generation.log"
RESULTS="$STITCH/screens.json"

brand_light="Use CourtPass design system. LIGHT MODE only. Mobile 390px. Primary #1B7A4E, orange #E86A2A, bg #F4F7F5, white cards."
brand_dark="Use CourtPass design system. DARK MODE only. Mobile 390px. SAME accents #1B7A4E and #E86A2A. bg #0F1A14, cards #1A2620, text #F4F7F5. Subtle green glow on primary CTA only."

generate() {
  local label="$1" prompt="$2"
  echo "[$(date -Iseconds)] START $label" | tee -a "$LOG"
  local out
  if out=$(npx @_davideast/stitch-mcp tool generate_screen_from_text -d "$(jq -n \
    --arg pid "$PROJECT_ID" \
    --arg ds "$DS" \
    --arg p "$prompt" \
    '{projectId:$pid, deviceType:"MOBILE", designSystem:$ds, prompt:$p}')" 2>&1); then
    echo "$out" >> "$LOG"
    echo "[$(date -Iseconds)] OK $label" | tee -a "$LOG"
    return 0
  fi
  echo "$out" >> "$LOG"
  echo "[$(date -Iseconds)] RETRY poll $label" | tee -a "$LOG"
  sleep 45
  npx @_davideast/stitch-mcp tool list_screens -d "{\"projectId\":\"$PROJECT_ID\"}" >> "$LOG" 2>&1 || true
  echo "[$(date -Iseconds)] DONE $label (may need manual check)" | tee -a "$LOG"
}

echo '{"projectId":"'"$PROJECT_ID"'","screens":[]}' > "$RESULTS"

# --- LIGHT MODE ---
generate "landing-light" "$brand_light Landing page /: header logo+Log in, hero padel photo Book. Pay. Play., Sheikh Zayed 2 courts, Book a court CTA, how it works 3 steps, morning promo Before 12PM 30% off, today slot counts, footer."

generate "login-light" "$brand_light Login /login: Welcome back, phone 01xxxxxxxx, password, green Log in, Create account link."

generate "register-light" "$brand_light Register /register: Create your account, name phone password fields, green Create account, Log in link."

generate "book-date-light" "$brand_light Book step 1/4: progress bar, When do you want to play, 14-day date strip, Open calendar, Next."

generate "book-slots-light" "$brand_light Book step 3/4: Court 1 Wed 20 Aug, Morning/Afternoon/Evening slots EGP 200/280/350, available/held/booked/selected chips, legend."

generate "book-confirm-light" "$brand_light Book step 4/4: summary Court 1 18-19 EGP 350, name phone players, hold timer, Pay with Paymob, cancel note."

generate "pending-light" "$brand_light Payment pending: spinner, Confirming payment, Court 1 18:00."

generate "failed-light" "$brand_light Payment failed: X icon, slot released, Try another slot + Back home."

generate "bookings-light" "$brand_light My bookings: Upcoming cards Ready to play + View pass, Past Redeemed/Expired, + Book button."

generate "pass-light" "$brand_light Booking pass: QR code, CP-7X4K-29MN, court date time, payer 4 players EGP 350, show staff."

generate "staff-login-light" "$brand_light Staff login: 4-digit PIN pad, CourtPass Staff."

generate "staff-lookup-light" "$brand_light Staff lookup: search booking code, today list with status."

generate "staff-redeem-light" "$brand_light Staff redeem: PAID Ready, customer details, big REDEEM CHECK-IN button."

# --- DARK MODE ---
generate "landing-dark" "$brand_dark Landing page / dark mode — same layout as light landing."

generate "login-dark" "$brand_dark Login page dark mode — same fields as light login."

generate "register-dark" "$brand_dark Register page dark mode."

generate "book-date-dark" "$brand_dark Book date step dark mode."

generate "book-slots-dark" "$brand_dark Book slot grid dark mode with tinted chips."

generate "book-confirm-dark" "$brand_dark Book confirm + Paymob dark mode."

generate "pending-dark" "$brand_dark Payment pending dark mode."

generate "failed-dark" "$brand_dark Payment failed dark mode."

generate "bookings-dark" "$brand_dark My bookings list dark mode."

generate "pass-dark" "$brand_dark Booking pass QR dark mode."

generate "staff-login-dark" "$brand_dark Staff PIN login dark mode."

generate "staff-lookup-dark" "$brand_dark Staff lookup dark mode."

generate "staff-redeem-dark" "$brand_dark Staff redeem dark mode."

echo "[$(date -Iseconds)] ALL COMPLETE" | tee -a "$LOG"
npx @_davideast/stitch-mcp tool list_screens -d "{\"projectId\":\"$PROJECT_ID\"}" | tee "$STITCH/screens-final.json"
