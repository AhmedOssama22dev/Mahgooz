import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/staff/bookings')({
  component: StaffBookingsPage,
})

function StaffBookingsPage() {
  return null
}
