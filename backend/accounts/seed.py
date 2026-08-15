from django.conf import settings

from .models import User
from .phones import InvalidPhone, normalize_phone


def seed_staff_user():
    """Create or promote the demo staff account from env. Safe to run more than once."""
    raw_phone = (settings.STAFF_PHONE or "").strip()
    password = settings.STAFF_PASSWORD or ""
    name = (settings.STAFF_NAME or "Staff").strip() or "Staff"
    if not raw_phone or not password:
        return None
    try:
        phone = normalize_phone(raw_phone)
    except InvalidPhone as exc:
        raise ValueError(str(exc)) from exc
    user, created = User.objects.get_or_create(
        phone=phone,
        defaults={"name": name, "is_staff": True},
    )
    if created:
        user.set_password(password)
        user.save(update_fields=["password"])
        return user
    changed = []
    if not user.is_staff:
        user.is_staff = True
        changed.append("is_staff")
    if name and user.name != name:
        user.name = name
        changed.append("name")
    if changed:
        user.save(update_fields=changed)
    return user
