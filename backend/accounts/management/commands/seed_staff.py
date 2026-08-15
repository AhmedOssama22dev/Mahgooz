from django.core.management.base import BaseCommand, CommandError

from accounts.seed import seed_staff_user


class Command(BaseCommand):
    help = "Idempotently seed a staff user from STAFF_PHONE / STAFF_PASSWORD / STAFF_NAME."

    def handle(self, *args, **options):
        try:
            user = seed_staff_user()
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        if user is None:
            raise CommandError(
                "Set STAFF_PHONE and STAFF_PASSWORD in the environment to seed a staff account."
            )
        self.stdout.write(
            self.style.SUCCESS(f"Staff account ready: {user.phone} ({user.name})")
        )
