import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/staff/')({
  component: StaffLookupPage,
})

function StaffLookupPage() {
  return null
}
