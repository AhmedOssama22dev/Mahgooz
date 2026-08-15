from django.core.management.base import BaseCommand

from bookings.expiry import expire_elapsed_holds


class Command(BaseCommand):
    help = "Expire unpaid holds past their TTL and release their slots."

    def handle(self, *args, **options):
        count = expire_elapsed_holds()
        if count:
            self.stdout.write(self.style.SUCCESS(f"Expired {count} unpaid hold(s)."))
        else:
            self.stdout.write("No unpaid holds to expire.")
