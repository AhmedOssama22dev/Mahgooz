from urllib.parse import urlencode
import logging

import requests
from django.conf import settings

logger = logging.getLogger("payments.paymob")


class PaymobClientError(Exception):
    """Raised when Paymob cannot create an intention. Callers must not retry."""


class PaymobClient:
    """Server-only Intention API client. Secret Key never leaves this module."""

    def __init__(self):
        self.base_url = settings.PAYMOB_BASE_URL.rstrip("/")
        self.checkout_base_url = settings.PAYMOB_CHECKOUT_BASE_URL.rstrip("/")
        self.secret_key = (settings.PAYMOB_SECRET_KEY or "").strip()
        self.public_key = (settings.PAYMOB_PUBLIC_KEY or "").strip()
        self.timeout = settings.PAYMOB_TIMEOUT_SECONDS
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Token {self.secret_key}",
                "Content-Type": "application/json",
            }
        )

    def is_configured(self):
        return bool(self.secret_key and self.public_key and self.card_integration_id() is not None)

    def card_integration_id(self):
        raw = str(settings.PAYMOB_INTEGRATION_ID_CARD or "").strip()
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    def create_intention(self, payload):
        url = f"{self.base_url}/v1/intention/"
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
        except requests.Timeout as exc:
            logger.warning("Paymob intention timed out after %ss", self.timeout)
            raise PaymobClientError("Paymob request timed out") from exc
        except requests.RequestException as exc:
            logger.warning("Paymob intention request failed: %s", exc)
            raise PaymobClientError("Paymob request failed") from exc

        if response.status_code not in (200, 201):
            logger.warning(
                "Paymob intention failed HTTP %s: %s",
                response.status_code,
                (response.text or "")[:800],
            )
            raise PaymobClientError(
                f"Paymob intention failed with HTTP {response.status_code}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise PaymobClientError("Paymob returned a non-JSON body") from exc

        intention_id = data.get("id")
        client_secret = data.get("client_secret")
        if not intention_id or not client_secret:
            raise PaymobClientError("Paymob response missing id or client_secret")

        return {"id": str(intention_id), "client_secret": str(client_secret)}

    def checkout_url(self, client_secret):
        query = urlencode(
            {
                "publicKey": self.public_key,
                "clientSecret": client_secret,
            }
        )
        return f"{self.checkout_base_url}/?{query}"
