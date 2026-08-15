from django.urls import include, path

from config.views import HealthView

urlpatterns = [
    path("health", HealthView.as_view(), name="health"),
    path("auth/", include("accounts.urls")),
    path("", include("bookings.urls")),
    path("", include("payments.urls")),
]
