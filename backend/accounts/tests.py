from rest_framework.test import APITestCase

from accounts.models import User
from accounts.phones import InvalidPhone, normalize_phone


class HealthTests(APITestCase):
    def test_health_ok(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_old_health_path_gone(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 404)


class PhoneNormalizeTests(APITestCase):
    def test_local_format(self):
        self.assertEqual(normalize_phone("01012345678"), "01012345678")

    def test_plus_country_code(self):
        self.assertEqual(normalize_phone("+201012345678"), "01012345678")

    def test_country_code_without_plus(self):
        self.assertEqual(normalize_phone("201012345678"), "01012345678")

    def test_spaces_and_dashes(self):
        self.assertEqual(normalize_phone("010 1234-5678"), "01012345678")

    def test_invalid(self):
        with self.assertRaises(InvalidPhone):
            normalize_phone("12345")


class AuthTests(APITestCase):
    register_url = "/api/v1/auth/register"
    login_url = "/api/v1/auth/login"
    refresh_url = "/api/v1/auth/refresh"
    me_url = "/api/v1/auth/me"

    def _register(self, **overrides):
        payload = {
            "name": "Ahmed Hassan",
            "phone": "01012345678",
            "password": "secret12",
            **overrides,
        }
        return self.client.post(self.register_url, payload, format="json")

    def test_register_success(self):
        response = self._register()
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["token_type"], "Bearer")
        self.assertEqual(body["expires_in"], 3600)
        self.assertTrue(body["access"])
        self.assertTrue(body["refresh"])
        self.assertEqual(body["user"]["name"], "Ahmed Hassan")
        self.assertEqual(body["user"]["phone"], "01012345678")
        self.assertTrue(User.objects.filter(phone="01012345678").exists())

    def test_register_normalizes_plus_country_code(self):
        response = self._register(phone="+201012345678")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["user"]["phone"], "01012345678")
        self.assertEqual(User.objects.get().phone, "01012345678")

    def test_register_invalid_phone(self):
        response = self._register(phone="12345")
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("phone", body["error"]["details"])
        self.assertIn(
            "Enter an Egyptian mobile number like 01xxxxxxxxx.",
            body["error"]["details"]["phone"],
        )

    def test_register_short_password(self):
        response = self._register(password="ab")
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("password", body["error"]["details"])

    def test_register_duplicate_phone(self):
        self.assertEqual(self._register().status_code, 201)
        response = self._register()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "PHONE_TAKEN")

    def test_login_success(self):
        self._register()
        response = self.client.post(
            self.login_url,
            {"phone": "01012345678", "password": "secret12"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["access"])
        self.assertEqual(body["user"]["phone"], "01012345678")

    def test_login_missing_password(self):
        response = self.client.post(
            self.login_url,
            {"phone": "01012345678"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("password", body["error"]["details"])

    def test_login_bad_credentials(self):
        self._register()
        response = self.client.post(
            self.login_url,
            {"phone": "01012345678", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "INVALID_CREDENTIALS")

    def test_me_requires_auth(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "UNAUTHENTICATED")

    def test_me_success(self):
        tokens = self._register().json()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["name"], "Ahmed Hassan")
        self.assertEqual(body["phone"], "01012345678")
        self.assertEqual(set(body.keys()), {"id", "name", "phone"})

    def test_refresh_success(self):
        tokens = self._register().json()
        response = self.client.post(
            self.refresh_url,
            {"refresh": tokens["refresh"]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["access"])
        self.assertEqual(body["token_type"], "Bearer")
        self.assertEqual(body["expires_in"], 3600)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {body['access']}")
        self.assertEqual(self.client.get(self.me_url).status_code, 200)

    def test_refresh_invalid(self):
        response = self.client.post(
            self.refresh_url,
            {"refresh": "not-a-token"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "UNAUTHENTICATED")
