import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/staff/login')({
  component: StaffLoginPage,
})

function StaffLoginPage() {
  return null
}
