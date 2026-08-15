import { Link } from '@tanstack/react-router'

import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'

type AccountMenuProps = {
  name?: string
  triggerLabel?: string
}

/** Header account menu: My bookings + Log out. */
export function AccountMenu({
  name,
  triggerLabel = 'Account',
}: AccountMenuProps) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm">
          {name ?? triggerLabel}
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-72">
        <SheetHeader>
          <SheetTitle className="font-display">
            {name ?? 'Account'}
          </SheetTitle>
        </SheetHeader>
        <div className="flex flex-col gap-2 px-4">
          <Button variant="outline" asChild>
            <Link to="/bookings">My bookings</Link>
          </Button>
          <Button variant="ghost" asChild>
            <Link to="/">Log out</Link>
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}
