import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/book/pending')({
  component: BookPendingPage,
})

function BookPendingPage() {
  return null
}
