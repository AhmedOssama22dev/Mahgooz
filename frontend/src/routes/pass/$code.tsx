import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/pass/$code')({
  component: PassPage,
})

function PassPage() {
  return null
}
