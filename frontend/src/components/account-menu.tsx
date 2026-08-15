import { Link } from '@tanstack/react-router'

import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'

type AccountMenuProps = {
  name?: string
  open: boolean
  onOpenChange: (open: boolean) => void
  onLogout: () => void
}

/** Header / bottom-nav account sheet: My bookings + Log out. */
export function AccountMenu({
  name,
  open,
  onOpenChange,
  onLogout,
}: AccountMenuProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-72">
        <SheetHeader>
          <SheetTitle className="font-display">{name ?? 'Account'}</SheetTitle>
        </SheetHeader>
        <div className="flex flex-col gap-2 px-4">
          <Button variant="outline" asChild>
            <Link to="/bookings" onClick={() => onOpenChange(false)}>
              My bookings
            </Link>
          </Button>
          <Button variant="ghost" onClick={onLogout}>
            Log out
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}
