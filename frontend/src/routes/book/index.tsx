import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/book/')({
  component: BookPage,
})

function BookPage() {
  return null
}
