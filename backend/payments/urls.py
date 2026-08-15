from django.urls import path

from .views import PaymobWebhookView

urlpatterns = [
    path("webhooks/paymob", PaymobWebhookView.as_view(), name="paymob-webhook"),
]
