import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/staff/pass/$code')({
  component: StaffPassPage,
})

function StaffPassPage() {
  return null
}
