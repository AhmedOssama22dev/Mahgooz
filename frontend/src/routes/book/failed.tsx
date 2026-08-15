import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/book/failed')({
  component: BookFailedPage,
})

function BookFailedPage() {
  return null
}
