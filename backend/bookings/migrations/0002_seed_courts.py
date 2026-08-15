from django.db import migrations

from bookings.seed import seed_courts


def forwards(apps, schema_editor):
    seed_courts(apps.get_model("bookings", "Court"))


def backwards(apps, schema_editor):
    Court = apps.get_model("bookings", "Court")
    Court.objects.filter(slug__in=["court-1", "court-2"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("bookings", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
