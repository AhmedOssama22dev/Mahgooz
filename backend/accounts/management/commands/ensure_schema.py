from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.exceptions import InconsistentMigrationHistory


class Command(BaseCommand):
    help = (
        "Apply migrations and seed courts. If this database was migrated with "
        "Django's default User before AUTH_USER_MODEL was set, reset the empty "
        "schema and migrate again."
    )

    def handle(self, *args, **options):
        try:
            call_command("migrate", interactive=False)
        except InconsistentMigrationHistory as exc:
            self.stderr.write(self.style.WARNING(str(exc)))
            self.stderr.write(
                self.style.WARNING(
                    "Railway DB was migrated before accounts.User existed. "
                    "Resetting public schema and migrating from scratch."
                )
            )
            self._reset_public_schema()
            call_command("migrate", interactive=False)

        call_command("seed_courts")
        try:
            call_command("seed_staff")
        except CommandError as exc:
            self.stdout.write(self.style.NOTICE(str(exc)))

    def _reset_public_schema(self):
        connection.rollback()
        with connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA public CASCADE")
            cursor.execute("CREATE SCHEMA public")
            cursor.execute("GRANT ALL ON SCHEMA public TO public")
            cursor.execute("GRANT ALL ON SCHEMA public TO CURRENT_USER")
        connection.close()
