COURT_SPECS = (
    {"slug": "court-1", "name": "Court 1", "sort_order": 1},
    {"slug": "court-2", "name": "Court 2", "sort_order": 2},
)


def seed_courts(court_model=None):
    """Create Court 1 and Court 2. Safe to run more than once."""
    if court_model is None:
        from bookings.models import Court as court_model

    courts = []
    for spec in COURT_SPECS:
        court, _created = court_model.objects.get_or_create(
            slug=spec["slug"],
            defaults={"name": spec["name"], "sort_order": spec["sort_order"]},
        )
        courts.append(court)
    return courts
