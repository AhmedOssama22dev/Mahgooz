import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/bookings')({
  component: BookingsPage,
})

function BookingsPage() {
  return null
}
