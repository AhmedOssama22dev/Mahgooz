import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { MoonLinear, MxIcon, SunLinear } from '@/lib/icons'

export function ThemeToggle() {
  const [isDark, setIsDark] = useState(() =>
    document.documentElement.classList.contains('dark'),
  )

  useEffect(() => {
    setIsDark(document.documentElement.classList.contains('dark'))
  }, [])

  function toggleTheme() {
    const next = document.documentElement.classList.toggle('dark')
    localStorage.setItem('mahgouz-theme', next ? 'dark' : 'light')
    setIsDark(next)
  }

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon-sm"
      className="text-muted-foreground"
      onClick={toggleTheme}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      <MxIcon icon={SunLinear} size={16} className="dark:hidden" />
      <MxIcon icon={MoonLinear} size={16} className="hidden dark:block" />
    </Button>
  )
}
