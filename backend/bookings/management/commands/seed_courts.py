from django.core.management.base import BaseCommand

from bookings.seed import seed_courts


class Command(BaseCommand):
    help = "Idempotently seed Court 1 and Court 2."

    def handle(self, *args, **options):
        courts = seed_courts()
        names = ", ".join(court.name for court in courts)
        self.stdout.write(self.style.SUCCESS(f"Seeded courts: {names}"))
