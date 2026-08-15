#!/usr/bin/env bash
# Generate full CourtPass screen matrix: 15 pages × mobile/desktop × light/dark
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
set -a && source "$ROOT/.env" && set +a

STITCH="$ROOT/docs/stitch"
PROJECT_ID="$(jq -r '.projectId' "$STITCH/prompts.json")"
DS="$(jq -r '.designSystem' "$STITCH/prompts.json")"
LOG="$STITCH/generation.log"
MANIFEST="$STITCH/manifest.json"

# ponytail: resume via manifest — re-run safe after ECONNRESET
[[ -f "$MANIFEST" ]] || echo '{"done":[]}' > "$MANIFEST"

is_done() {
  jq -e --arg l "$1" '.done | index($l) != null' "$MANIFEST" >/dev/null
}

mark_done() {
  local tmp
  tmp="$(mktemp)"
  jq --arg l "$1" '.done += [$l] | .done |= unique' "$MANIFEST" > "$tmp"
  mv "$tmp" "$MANIFEST"
}

generate() {
  local label="$1" device="$2" prompt="$3"
  if is_done "$label"; then
    echo "[$(date -Iseconds)] SKIP $label (already done)" | tee -a "$LOG"
    return 0
  fi
  echo "[$(date -Iseconds)] START $label ($device)" | tee -a "$LOG"
  local out
  if out=$(npx @_davideast/stitch-mcp tool generate_screen_from_text -d "$(jq -n \
    --arg pid "$PROJECT_ID" \
    --arg ds "$DS" \
    --arg dev "$device" \
    --arg p "$prompt" \
    '{projectId:$pid, deviceType:$dev, designSystem:$ds, prompt:$p}')" 2>&1); then
    echo "$out" >> "$LOG"
    mark_done "$label"
    echo "[$(date -Iseconds)] OK $label" | tee -a "$LOG"
    return 0
  fi
  echo "$out" >> "$LOG"
  echo "[$(date -Iseconds)] RETRY poll $label" | tee -a "$LOG"
  sleep 60
  if npx @_davideast/stitch-mcp tool list_screens -d "{\"projectId\":\"$PROJECT_ID\"}" >> "$LOG" 2>&1; then
    mark_done "$label"
    echo "[$(date -Iseconds)] OK $label (poll)" | tee -a "$LOG"
  else
    echo "[$(date -Iseconds)] FAIL $label — check Stitch project" | tee -a "$LOG"
  fi
}

brand_mobile_light="$(jq -r '.brand.mobileLight' "$STITCH/prompts.json")"
brand_mobile_dark="$(jq -r '.brand.mobileDark' "$STITCH/prompts.json")"
brand_desktop_light="$(jq -r '.brand.desktopLight' "$STITCH/prompts.json")"
brand_desktop_dark="$(jq -r '.brand.desktopDark' "$STITCH/prompts.json")"

# Seed already-generated mobile light screens from first batch
for seeded in landing-mobile-light login-mobile-light; do
  is_done "$seeded" || mark_done "$seeded"
done

page_count=$(jq '.pages | length' "$STITCH/prompts.json")
echo "[$(date -Iseconds)] MATRIX START — $page_count pages × 4 variants" | tee -a "$LOG"

while IFS= read -r page; do
  id=$(echo "$page" | jq -r '.id')
  ml=$(echo "$page" | jq -r '.mobileLight')
  md=$(echo "$page" | jq -r '.mobileDark')
  dl=$(echo "$page" | jq -r '.desktopLight')
  dd=$(echo "$page" | jq -r '.desktopDark')

  generate "${id}-mobile-light" "MOBILE" "$brand_mobile_light Screen title: CourtPass ${id} mobile light. $ml"
  generate "${id}-mobile-dark" "MOBILE" "$brand_mobile_dark Screen title: CourtPass ${id} mobile dark. $md"
  generate "${id}-desktop-light" "DESKTOP" "$brand_desktop_light Screen title: CourtPass ${id} desktop light. $dl"
  generate "${id}-desktop-dark" "DESKTOP" "$brand_desktop_dark Screen title: CourtPass ${id} desktop dark. $dd"
done < <(jq -c '.pages[]' "$STITCH/prompts.json")

echo "[$(date -Iseconds)] MATRIX COMPLETE" | tee -a "$LOG"
npx @_davideast/stitch-mcp tool list_screens -d "{\"projectId\":\"$PROJECT_ID\"}" \
  | tee "$STITCH/screens-final.json"
