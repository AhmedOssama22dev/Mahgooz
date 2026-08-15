"""Generate the Mahgooz Postman collection and local environment.

Run from backend/:  python postman/generate.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLLECTION_PATH = HERE / "Mahgooz_API.postman_collection.json"
ENVIRONMENT_PATH = HERE / "Mahgooz_Local.postman_environment.json"

COLLECTION_ID = "ab8467da-c17a-4d78-a2b6-65036cc4b11c"
ENVIRONMENT_ID = "f97b751c-c160-42bd-a27e-a4ba1c0d23b4"

COURT_1 = "11111111-1111-4111-8111-111111111111"
COURT_2 = "22222222-2222-4222-8222-222222222222"
BOOKING_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
BOOKING_CODE = "MGZ-7F42K"
SLOT_DATE = "2026-08-20"
JSON_HEADER = {"key": "Content-Type", "value": "application/json; charset=utf-8"}

STATUS = {
    200: "OK",
    201: "Created",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
}


def dumps(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)


def bearer():
    return {
        "type": "bearer",
        "bearer": [{"key": "token", "value": "{{access_token}}", "type": "string"}],
    }


def noauth():
    return {"type": "noauth"}


def auth_header():
    return {"key": "Authorization", "value": "Bearer {{access_token}}"}


def json_header():
    return {"key": "Content-Type", "value": "application/json"}


def raw_json(obj):
    return {
        "mode": "raw",
        "raw": dumps(obj),
        "options": {"raw": {"language": "json"}},
    }


def error(code, message, details=None, **extra):
    payload = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    payload["error"].update(extra)
    return payload


def slot_obj(start, end, price_egp=350, court_id=COURT_1, court_name="Court 1", period="evening"):
    return {
        "court": {"id": court_id, "name": court_name},
        "date": SLOT_DATE,
        "start_time": start,
        "end_time": end,
        "period": period,
        "price_egp": price_egp,
        "price_cents": price_egp * 100,
    }


HOLD_SLOTS = [
    {"court_id": "{{court_id}}", "date": "{{slot_date}}", "start_time": "18:00"},
    {"court_id": "{{court_id}}", "date": "{{slot_date}}", "start_time": "19:00"},
]
HOLD_ATTENDEES = ["Ahmed Hassan", "Omar Ali"]
HOLD_BODY = {"slots": HOLD_SLOTS, "attendee_names": HOLD_ATTENDEES}
MIXED_BODY = {
    "slots": [
        {"court_id": "{{court_id}}", "date": "{{slot_date}}", "start_time": "18:00"},
        {"court_id": COURT_2, "date": "{{slot_date}}", "start_time": "19:00"},
    ],
    "attendee_names": HOLD_ATTENDEES,
}
TWO_SLOTS = [slot_obj("18:00", "19:00"), slot_obj("19:00", "20:00")]


def hold_success(**overrides):
    payload = {
        "id": BOOKING_ID,
        "status": "held",
        "booker_name": "Ahmed Hassan",
        "attendee_names": HOLD_ATTENDEES,
        "slots": TWO_SLOTS,
        "total_price_egp": 700,
        "total_price_cents": 70000,
        "hold_expires_at": "2026-08-15T16:32:00+03:00",
        "booking_code": None,
        "qr_payload": None,
        "redeemed_at": None,
        "created_at": "2026-08-15T16:22:00+03:00",
    }
    payload.update(overrides)
    return payload


def public_pass(**overrides):
    payload = {
        "booking_code": BOOKING_CODE,
        "status": "confirmed",
        "court": {"id": COURT_1, "name": "Court 1"},
        "date": SLOT_DATE,
        "start_times": ["18:00", "19:00"],
        "start_time": "18:00",
        "end_time": "20:00",
        "booker_name": "Ahmed Hassan",
        "attendee_names": HOLD_ATTENDEES,
        "price_egp": 700,
        "qr_payload": f"http://localhost:3000/pass/{BOOKING_CODE}",
        "redeemed_at": None,
    }
    payload.update(overrides)
    return payload


def staff_pass(**overrides):
    payload = {
        "booking_code": BOOKING_CODE,
        "status": "confirmed",
        "can_redeem": True,
        "booker_name": "Ahmed Hassan",
        "booker_phone": "01012345678",
        "attendee_names": HOLD_ATTENDEES,
        "slots": TWO_SLOTS,
        "total_price_egp": 700,
        "total_price_cents": 70000,
        "paymob_transaction_id": "289187034",
        "redeemed_at": None,
    }
    payload.update(overrides)
    return payload


def tokens(role="customer"):
    return {
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access",
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh",
        "token_type": "Bearer",
        "expires_in": 3600,
        "user": {
            "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "name": "Mostafa" if role == "staff" else "Ahmed Hassan",
            "phone": "01000000000" if role == "staff" else "01012345678",
            "role": role,
        },
    }


def webhook_body(success=True):
    return {
        "type": "TRANSACTION",
        "obj": {
            "id": 289187034,
            "pending": False,
            "amount_cents": 70000,
            "success": success,
            "is_auth": False,
            "is_capture": False,
            "is_standalone_payment": True,
            "is_voided": False,
            "is_refunded": False,
            "is_3d_secure": True,
            "integration_id": 123456,
            "profile_id": 98765,
            "has_parent_transaction": False,
            "order": {"id": 998877, "merchant_order_id": BOOKING_ID},
            "created_at": "2026-08-15T13:24:11.123456",
            "currency": "EGP",
            "error_occured": False,
            "owner": 111222,
            "source_data": {"pan": "2346", "type": "card", "sub_type": "MasterCard"},
        },
        "hmac": "deadbeef" if not success else "REPLACE_WITH_COMPUTED_HMAC_SHA512",
    }


def req(method, url, description, *, auth=None, body=None, headers=None):
    item = {
        "method": method,
        "header": headers or [],
        "url": url,
        "description": description,
        "auth": auth if auth is not None else noauth(),
    }
    if body is not None:
        item["body"] = raw_json(body) if not isinstance(body, dict) or "mode" not in body else body
        if isinstance(body, dict) and "mode" not in body:
            item["body"] = raw_json(body)
    return item


def example(name, code, request, body):
    return {
        "name": name,
        "originalRequest": request,
        "status": STATUS[code],
        "code": code,
        "_postman_previewlanguage": "json",
        "header": [JSON_HEADER],
        "cookie": [],
        "body": dumps(body),
    }


def test_event(lines):
    return {
        "listen": "test",
        "script": {"type": "text/javascript", "exec": lines},
    }


def item(name, request, examples, events=None):
    payload = {"name": name, "request": request, "response": examples}
    if events:
        payload["event"] = events
    return payload


def folder(name, description, items, auth=None):
    payload = {"name": name, "description": description, "item": items}
    if auth is not None:
        payload["auth"] = auth
    return payload


SAVE_TOKENS = [
    "if (pm.response.code === 200 || pm.response.code === 201) {",
    "  const json = pm.response.json();",
    "  if (json.access) pm.collectionVariables.set('access_token', json.access);",
    "  if (json.refresh) pm.collectionVariables.set('refresh_token', json.refresh);",
    "}",
]

DESCRIPTION = """# Mahgooz padel booking — MVP v1

Django REST API for **Pay → Reserve → Redeem**.

## Base URL
`{{base_url}}` defaults to `http://localhost:8000/api/v1`.

## Auth
- **One JWT** (`Authorization: Bearer {{access_token}}`) from phone + password login.
- Role is on the user (`customer` or `staff`). Public register always creates customers; staff is granted in Django admin or `python manage.py seed_staff`.
- There is **no staff PIN** and no `/staff/login`. Staff use `POST /auth/login` with `{{staff_phone}}` / `{{staff_password}}`.
- Staff-only routes (`/staff/*`) return 403 for customer accounts.
- **Webhook** has no JWT; authenticity is HMAC-SHA512.
- Public pass, courts, slots, and health need no auth.

## Suggested run order
1. Health → List courts (saves `court_id`)
2. Register or Login (saves `access_token`)
3. List slots → Hold `slots[]` (saves `booking_id`)
4. Start checkout → open `checkout_url` in a browser with a Paymob test card
5. Poll payment status until `confirmed` (saves `booking_code`)
6. Get public pass
7. Log in as staff via `/auth/login` → Lookup → Redeem once

## Error shape
```json
{ "error": { "code": "SLOT_TAKEN", "message": "..." } }
```

Every request has saved **success and failure examples** in the Examples dropdown.

## Slot rules
- Two courts, 60-minute slots, 08:00–22:00, book 14 days ahead.
- Hold TTL **10 minutes**. Abandoned / failed / expired holds free every child slot.
- Unique active row per occupied hour: `court + date + start_time`.
- Hold one or more hours on the **same court and date** via `slots[]`. Mixed courts/dates → `400 MIXED_SLOTS`. One conflict rolls back the whole hold → `409 SLOT_TAKEN`.
- Pricing: morning EGP 200 (08–12), afternoon 280 (12–17), evening 350 (17–22).
- A booking is **paid only** after a verified Paymob webhook, never after the redirect page.
"""

HOLD_DESC = """Atomically hold one or more 60-minute slots for 10 minutes.

Send a `slots[]` array. Every entry must share the same `court_id` and `date`, with distinct `start_time` values. Price is the sum of each hour's band.

Creates one `held` parent booking plus a `BookingSlot` row per hour. Occupies every hour: unique on `court + date + start_time` while `released_at` is null.

**Attendee names** are required (1–4). Booker name is copied from the JWT user.

If any requested hour is taken: **409 SLOT_TAKEN** with `conflicting_slots`, and **none** of the requested slots are held.
"""

WEBHOOK_DESC = """**Source of truth for payment.** Paymob POSTs here; the browser redirect is ignored.

1. Verify HMAC-SHA512 with `PAYMOB_HMAC_SECRET` using Paymob's documented field order.
2. Reject mismatch with **401 INVALID_HMAC** — do not update the booking.
3. On `obj.success === true`: set parent status `confirmed`, issue one `booking_code` for all slots, store unique `paymob_transaction_id` (idempotent on retries).
4. On failure: set status `failed` and release every child slot.

`obj.order.merchant_order_id` / `special_reference` = booking UUID.

**The success body uses a placeholder hmac.** A live 200 requires a signature computed against your `PAYMOB_HMAC_SECRET`. Send the invalid-hmac example as-is to test rejection.
"""


def build_collection():
    health = req("GET", "{{base_url}}/health", "Liveness check for deploy/tunnel. No auth.")
    courts = req("GET", "{{base_url}}/courts", "Two seeded courts. Saves `court_id`.")
    slots = req(
        "GET",
        "{{base_url}}/slots?date={{slot_date}}&court_id={{court_id}}",
        "Generated 08:00–21:00 grid for one court and date.\n\n"
        "**States:** `available` | `held` | `booked`. Held slots of other customers are never selectable.\n\n"
        "Morning slots include `label: \"Morning available\"`.\n\n"
        "Book-ahead window: today through 14 days. Slot duration: 60 minutes.",
    )
    register = req(
        "POST",
        "{{base_url}}/auth/register",
        "Always creates `role: customer`. Returns JWT access + refresh.",
        body={"name": "Ahmed Hassan", "phone": "{{phone}}", "password": "{{password}}"},
        headers=[json_header()],
    )
    login = req(
        "POST",
        "{{base_url}}/auth/login",
        "Phone + password → JWT. Same endpoint for customers and staff; `user.role` is the only difference.",
        body={"phone": "{{phone}}", "password": "{{password}}"},
        headers=[json_header()],
    )
    staff_login = req(
        "POST",
        "{{base_url}}/auth/login",
        "Same login as customers. A staff account (`is_staff`) returns `user.role: staff`.\n\n"
        "No PIN and no `/staff/login`. Uses `{{staff_phone}}` / `{{staff_password}}`.",
        body={"phone": "{{staff_phone}}", "password": "{{staff_password}}"},
        headers=[json_header()],
    )
    refresh = req(
        "POST",
        "{{base_url}}/auth/refresh",
        "Rotate the access token.",
        body={"refresh": "{{refresh_token}}"},
        headers=[json_header()],
    )
    me = req(
        "GET",
        "{{base_url}}/auth/me",
        "Current profile. Requires a JWT. Includes `role` (`customer` or `staff`).",
        auth=bearer(),
        headers=[auth_header()],
    )
    hold = req(
        "POST",
        "{{base_url}}/bookings/hold",
        HOLD_DESC,
        auth=bearer(),
        body=HOLD_BODY,
        headers=[auth_header(), json_header()],
    )
    mixed = req(
        "POST",
        "{{base_url}}/bookings/hold",
        HOLD_DESC,
        auth=bearer(),
        body=MIXED_BODY,
        headers=[auth_header(), json_header()],
    )
    cancel = req(
        "DELETE",
        "{{base_url}}/bookings/{{booking_id}}",
        "Cancel own hold or unpaid booking and release every child slot. Paid bookings cannot be cancelled in MVP.",
        auth=bearer(),
        headers=[auth_header()],
    )
    checkout = req(
        "POST",
        "{{base_url}}/bookings/{{booking_id}}/checkout",
        "Create one Paymob Intention for `total_price_cents` with **one item per slot**. "
        "Returns Unified Checkout URL. Does not mark the booking paid.",
        auth=bearer(),
        body={},
        headers=[auth_header(), json_header()],
    )
    status_poll = req(
        "GET",
        "{{base_url}}/bookings/{{booking_id}}/status",
        "Poll for the pending page. `booking_code` is present only after `confirmed`.",
        auth=bearer(),
        headers=[auth_header()],
    )
    public_pass_req = req(
        "GET",
        "{{base_url}}/passes/{{booking_code}}",
        "Public pass after payment. No phone, no Paymob ids.",
    )
    my_bookings = req(
        "GET",
        "{{base_url}}/bookings",
        "Authenticated customer's upcoming and past bookings.",
        auth=bearer(),
        headers=[auth_header()],
    )
    detail = req(
        "GET",
        "{{base_url}}/bookings/{{booking_id}}",
        "Owner detail. `booking_code` is issued only after confirmed.",
        auth=bearer(),
        headers=[auth_header()],
    )
    staff_list = req(
        "GET",
        "{{base_url}}/staff/bookings?date={{slot_date}}",
        "Paid bookings (`confirmed` / `redeemed`) for a date (default today). Includes every child slot.",
        auth=bearer(),
        headers=[auth_header()],
    )
    staff_lookup = req(
        "GET",
        "{{base_url}}/staff/passes/{{booking_code}}",
        "Staff lookup of a pass. Includes phone, Paymob transaction id, and all child slots.\n\n"
        "`can_redeem` is true only when status is `confirmed`, it is the booking day, and it has not been redeemed.",
        auth=bearer(),
        headers=[auth_header()],
    )
    redeem = req(
        "POST",
        "{{base_url}}/staff/passes/{{booking_code}}/redeem",
        "Atomic one-time redeem: `UPDATE … WHERE booking_code=%s AND status='confirmed'`.\n\n"
        "Concurrent staff taps: only one 200, the other 409 ALREADY_REDEEMED. All slots stay occupied under the same pass.",
        auth=bearer(),
        body={},
        headers=[auth_header(), json_header()],
    )
    webhook = req(
        "POST",
        "{{base_url}}/webhooks/paymob",
        WEBHOOK_DESC,
        body=webhook_body(success=False),
        headers=[json_header()],
    )
    webhook_placeholder = req(
        "POST",
        "{{base_url}}/webhooks/paymob",
        WEBHOOK_DESC,
        body=webhook_body(success=True),
        headers=[json_header()],
    )

    return {
        "info": {
            "_postman_id": COLLECTION_ID,
            "name": "Mahgooz API — MVP v1",
            "description": DESCRIPTION,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {"key": "base_url", "value": "http://localhost:8000/api/v1"},
            {"key": "access_token", "value": ""},
            {"key": "refresh_token", "value": ""},
            {"key": "court_id", "value": COURT_1},
            {"key": "booking_id", "value": ""},
            {"key": "booking_code", "value": BOOKING_CODE},
            {"key": "phone", "value": "01012345678"},
            {"key": "password", "value": "secret12"},
            {"key": "slot_date", "value": SLOT_DATE},
            {"key": "start_time", "value": "18:00"},
            {"key": "staff_phone", "value": "01000000000"},
            {"key": "staff_password", "value": "staffpass"},
        ],
        "auth": bearer(),
        "item": [
            folder(
                "1. Health and courts",
                "No JWT. Smoke the API and load Court 1 into `court_id`.",
                [
                    item(
                        "Health",
                        health,
                        [
                            example("200 OK — healthy", 200, health, {"status": "ok"}),
                            example(
                                "503 Service Unavailable — database down",
                                503,
                                health,
                                error("UNHEALTHY", "Database unavailable"),
                            ),
                        ],
                    ),
                    item(
                        "List courts",
                        courts,
                        [
                            example(
                                "200 OK — two courts",
                                200,
                                courts,
                                [
                                    {"id": COURT_1, "name": "Court 1", "slug": "court-1"},
                                    {"id": COURT_2, "name": "Court 2", "slug": "court-2"},
                                ],
                            ),
                            example(
                                "500 Internal Server Error",
                                500,
                                courts,
                                error("INTERNAL_ERROR", "Unexpected server error"),
                            ),
                        ],
                        events=[
                            test_event(
                                [
                                    "if (pm.response.code === 200) {",
                                    "  const courts = pm.response.json();",
                                    "  if (Array.isArray(courts) && courts.length) {",
                                    "    pm.collectionVariables.set('court_id', courts[0].id);",
                                    "  }",
                                    "}",
                                ]
                            )
                        ],
                    ),
                ],
            ),
            folder(
                "2. Customer register/login",
                "Phone + password JWT. Public register always creates customers.",
                [
                    item(
                        "Register",
                        register,
                        [
                            example("201 Created — account + tokens", 201, register, tokens("customer")),
                            example(
                                "400 Bad Request — invalid phone",
                                400,
                                register,
                                error(
                                    "VALIDATION_ERROR",
                                    "Invalid request body",
                                    {"phone": ["Enter an Egyptian mobile number like 01xxxxxxxxx."]},
                                ),
                            ),
                            example(
                                "400 Bad Request — short password",
                                400,
                                register,
                                error(
                                    "VALIDATION_ERROR",
                                    "Invalid request body",
                                    {"password": ["Ensure this field has at least 6 characters."]},
                                ),
                            ),
                            example(
                                "409 Conflict — phone taken",
                                409,
                                register,
                                error("PHONE_TAKEN", "An account with this phone already exists."),
                            ),
                        ],
                        events=[test_event(SAVE_TOKENS)],
                    ),
                    item(
                        "Login",
                        login,
                        [
                            example("200 OK — tokens", 200, login, tokens("customer")),
                            example(
                                "400 Bad Request — missing fields",
                                400,
                                login,
                                error(
                                    "VALIDATION_ERROR",
                                    "Invalid request body",
                                    {"password": ["This field is required."]},
                                ),
                            ),
                            example(
                                "401 Unauthorized — bad credentials",
                                401,
                                login,
                                error("INVALID_CREDENTIALS", "Phone or password is incorrect."),
                            ),
                        ],
                        events=[test_event(SAVE_TOKENS)],
                    ),
                    item(
                        "Refresh token",
                        refresh,
                        [
                            example(
                                "200 OK — new access token",
                                200,
                                refresh,
                                {
                                    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access",
                                    "token_type": "Bearer",
                                    "expires_in": 3600,
                                },
                            ),
                            example(
                                "401 Unauthorized — invalid refresh",
                                401,
                                refresh,
                                error("UNAUTHENTICATED", "Refresh token is invalid or expired."),
                            ),
                        ],
                        events=[test_event(SAVE_TOKENS)],
                    ),
                    item(
                        "Me",
                        me,
                        [
                            example(
                                "200 OK — profile",
                                200,
                                me,
                                {
                                    "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                                    "name": "Ahmed Hassan",
                                    "phone": "01012345678",
                                    "role": "customer",
                                },
                            ),
                            example(
                                "401 Unauthorized — missing or expired JWT",
                                401,
                                me,
                                error("UNAUTHENTICATED", "Authentication credentials were not provided."),
                            ),
                        ],
                    ),
                ],
            ),
            folder(
                "3. Slots and multi-slot hold",
                "Browse availability, then hold every requested hour in one atomic booking.",
                [
                    item(
                        "List slots",
                        slots,
                        [
                            example(
                                "200 OK — slot grid",
                                200,
                                slots,
                                {
                                    "date": SLOT_DATE,
                                    "court": {"id": COURT_1, "name": "Court 1"},
                                    "operating_hours": {"open": "08:00", "close": "22:00"},
                                    "slot_minutes": 60,
                                    "slots": [
                                        {
                                            "start_time": "08:00",
                                            "end_time": "09:00",
                                            "state": "available",
                                            "period": "morning",
                                            "price_egp": 200,
                                            "price_cents": 20000,
                                            "label": "Morning available",
                                        },
                                        {
                                            "start_time": "18:00",
                                            "end_time": "19:00",
                                            "state": "available",
                                            "period": "evening",
                                            "price_egp": 350,
                                            "price_cents": 35000,
                                            "label": None,
                                        },
                                        {
                                            "start_time": "19:00",
                                            "end_time": "20:00",
                                            "state": "booked",
                                            "period": "evening",
                                            "price_egp": 350,
                                            "price_cents": 35000,
                                            "label": None,
                                        },
                                    ],
                                },
                            ),
                            example(
                                "400 Bad Request — missing date",
                                400,
                                slots,
                                error(
                                    "VALIDATION_ERROR",
                                    "Invalid query parameters",
                                    {"date": ["This field is required."]},
                                ),
                            ),
                            example(
                                "400 Bad Request — date out of range",
                                400,
                                slots,
                                error("DATE_OUT_OF_RANGE", "Date must be today or within the next 14 days."),
                            ),
                            example(
                                "404 Not Found — unknown court",
                                404,
                                slots,
                                error("NOT_FOUND", "Court not found."),
                            ),
                        ],
                    ),
                    item(
                        "Hold slots",
                        hold,
                        [
                            example("201 Created — two slots held", 201, hold, hold_success()),
                            example(
                                "400 Bad Request — mixed court/date",
                                400,
                                mixed,
                                error("MIXED_SLOTS", "All slots in a booking must share the same court and date."),
                            ),
                            example(
                                "400 Bad Request — duplicate start times",
                                400,
                                req(
                                    "POST",
                                    "{{base_url}}/bookings/hold",
                                    HOLD_DESC,
                                    auth=bearer(),
                                    body={
                                        "slots": [
                                            HOLD_SLOTS[0],
                                            HOLD_SLOTS[0],
                                        ],
                                        "attendee_names": HOLD_ATTENDEES,
                                    },
                                    headers=[auth_header(), json_header()],
                                ),
                                error("DUPLICATE_SLOTS", "Duplicate start times are not allowed in one booking."),
                            ),
                            example(
                                "401 Unauthorized",
                                401,
                                hold,
                                error("UNAUTHENTICATED", "Authentication credentials were not provided."),
                            ),
                            example(
                                "409 Conflict — slot taken, no partial hold",
                                409,
                                hold,
                                error(
                                    "SLOT_TAKEN",
                                    "One or more slots were just booked. None of the requested slots were held.",
                                    {
                                        "conflicting_slots": [
                                            {
                                                "court_id": COURT_1,
                                                "date": SLOT_DATE,
                                                "start_time": "19:00",
                                            }
                                        ]
                                    },
                                ),
                            ),
                        ],
                        events=[
                            test_event(
                                [
                                    "if (pm.response.code === 201) {",
                                    "  const json = pm.response.json();",
                                    "  if (json.id) pm.collectionVariables.set('booking_id', json.id);",
                                    "}",
                                ]
                            )
                        ],
                    ),
                    item(
                        "Cancel hold",
                        cancel,
                        [
                            example(
                                "200 OK — cancelled",
                                200,
                                cancel,
                                {"id": BOOKING_ID, "status": "cancelled", "message": "Slot released."},
                            ),
                            example(
                                "401 Unauthorized",
                                401,
                                cancel,
                                error("UNAUTHENTICATED", "Authentication credentials were not provided."),
                            ),
                            example(
                                "403 Forbidden — not owner",
                                403,
                                cancel,
                                error("FORBIDDEN", "You do not own this booking."),
                            ),
                            example("404 Not Found", 404, cancel, error("NOT_FOUND", "Booking not found.")),
                            example(
                                "409 Conflict — already paid",
                                409,
                                cancel,
                                error("CANNOT_CANCEL", "Paid bookings cannot be cancelled in MVP (no refunds)."),
                            ),
                        ],
                    ),
                ],
                auth=bearer(),
            ),
            folder(
                "4. Checkout",
                "One Paymob Intention for the summed price. One item per held slot. Redirect is never treated as paid.",
                [
                    item(
                        "Start checkout",
                        checkout,
                        [
                            example(
                                "200 OK — Paymob checkout URL",
                                200,
                                checkout,
                                {
                                    "booking_id": BOOKING_ID,
                                    "status": "pending_payment",
                                    "amount_egp": 700,
                                    "amount_cents": 70000,
                                    "currency": "EGP",
                                    "checkout_url": "https://eg.checkout.paymob.com/?publicKey=egy_pk_test&clientSecret=egy_csk_test",
                                    "paymob_intention_id": "pi_test_8f3a1c2e",
                                },
                            ),
                            example(
                                "401 Unauthorized",
                                401,
                                checkout,
                                error("UNAUTHENTICATED", "Authentication credentials were not provided."),
                            ),
                            example("404 Not Found", 404, checkout, error("NOT_FOUND", "Booking not found.")),
                            example(
                                "409 Conflict — hold expired",
                                409,
                                checkout,
                                error("HOLD_EXPIRED", "Your hold expired. Please pick the slot again."),
                            ),
                            example(
                                "409 Conflict — already paid",
                                409,
                                checkout,
                                error("ALREADY_PAID", "This booking is already confirmed."),
                            ),
                            example(
                                "502 Bad Gateway — Paymob error",
                                502,
                                checkout,
                                error(
                                    "PAYMOB_ERROR",
                                    "Could not start checkout. Your slot is still held — try again.",
                                ),
                            ),
                        ],
                    ),
                ],
                auth=bearer(),
            ),
            folder(
                "5. Status polling and public pass",
                "Poll until the webhook confirms payment, then open the shareable pass.",
                [
                    item(
                        "Poll payment status",
                        status_poll,
                        [
                            example(
                                "200 OK — still pending",
                                200,
                                status_poll,
                                {
                                    "id": BOOKING_ID,
                                    "status": "pending_payment",
                                    "booking_code": None,
                                    "pass_url": None,
                                    "hold_expires_at": "2026-08-15T16:32:00+03:00",
                                },
                            ),
                            example(
                                "200 OK — confirmed (after webhook)",
                                200,
                                status_poll,
                                {
                                    "id": BOOKING_ID,
                                    "status": "confirmed",
                                    "booking_code": BOOKING_CODE,
                                    "pass_url": f"/pass/{BOOKING_CODE}",
                                    "hold_expires_at": "2026-08-15T16:32:00+03:00",
                                },
                            ),
                            example(
                                "200 OK — payment failed",
                                200,
                                status_poll,
                                {
                                    "id": BOOKING_ID,
                                    "status": "failed",
                                    "booking_code": None,
                                    "pass_url": None,
                                    "hold_expires_at": "2026-08-15T16:32:00+03:00",
                                },
                            ),
                            example(
                                "401 Unauthorized",
                                401,
                                status_poll,
                                error("UNAUTHENTICATED", "Authentication credentials were not provided."),
                            ),
                            example(
                                "403 Forbidden — not owner",
                                403,
                                status_poll,
                                error("FORBIDDEN", "You do not own this booking."),
                            ),
                            example("404 Not Found", 404, status_poll, error("NOT_FOUND", "Booking not found.")),
                        ],
                        events=[
                            test_event(
                                [
                                    "if (pm.response.code === 200) {",
                                    "  const json = pm.response.json();",
                                    "  if (json.booking_code) pm.collectionVariables.set('booking_code', json.booking_code);",
                                    "}",
                                ]
                            )
                        ],
                    ),
                    item(
                        "Get public pass",
                        public_pass_req,
                        [
                            example("200 OK — confirmed pass", 200, public_pass_req, public_pass()),
                            example(
                                "200 OK — already redeemed",
                                200,
                                public_pass_req,
                                public_pass(
                                    status="redeemed",
                                    redeemed_at="2026-08-20T17:58:00+03:00",
                                ),
                            ),
                            example(
                                "404 Not Found — unknown or unpaid code",
                                404,
                                public_pass_req,
                                error("NOT_FOUND", "No paid booking for this code."),
                            ),
                        ],
                    ),
                    item(
                        "My bookings",
                        my_bookings,
                        [
                            example(
                                "200 OK — upcoming and past",
                                200,
                                my_bookings,
                                {
                                    "upcoming": [
                                        {
                                            "id": BOOKING_ID,
                                            "status": "confirmed",
                                            "court_name": "Court 1",
                                            "date": SLOT_DATE,
                                            "start_time": "18:00",
                                            "end_time": "20:00",
                                            "price_egp": 700,
                                            "booking_code": BOOKING_CODE,
                                            "period": "evening",
                                        }
                                    ],
                                    "past": [],
                                },
                            ),
                            example(
                                "401 Unauthorized",
                                401,
                                my_bookings,
                                error("UNAUTHENTICATED", "Authentication credentials were not provided."),
                            ),
                        ],
                    ),
                    item(
                        "Booking detail",
                        detail,
                        [
                            example(
                                "200 OK — owner detail",
                                200,
                                detail,
                                {
                                    "id": BOOKING_ID,
                                    "status": "confirmed",
                                    "court": {"id": COURT_1, "name": "Court 1"},
                                    "date": SLOT_DATE,
                                    "start_times": ["18:00", "19:00"],
                                    "start_time": "18:00",
                                    "end_time": "20:00",
                                    "booker_name": "Ahmed Hassan",
                                    "attendee_names": HOLD_ATTENDEES,
                                    "price_egp": 700,
                                    "price_cents": 70000,
                                    "hold_expires_at": "2026-08-15T16:32:00+03:00",
                                    "booking_code": BOOKING_CODE,
                                    "qr_payload": f"http://localhost:3000/pass/{BOOKING_CODE}",
                                    "redeemed_at": None,
                                    "created_at": "2026-08-15T16:22:00+03:00",
                                },
                            ),
                            example(
                                "403 Forbidden — not owner",
                                403,
                                detail,
                                error("FORBIDDEN", "You do not own this booking."),
                            ),
                            example("404 Not Found", 404, detail, error("NOT_FOUND", "Booking not found.")),
                        ],
                    ),
                ],
            ),
            folder(
                "6. Staff login through /auth/login",
                "No PIN. Seeded staff account uses the same phone + password login.",
                [
                    item(
                        "Staff login",
                        staff_login,
                        [
                            example("200 OK — staff tokens", 200, staff_login, tokens("staff")),
                            example(
                                "401 Unauthorized — bad credentials",
                                401,
                                staff_login,
                                error("INVALID_CREDENTIALS", "Phone or password is incorrect."),
                            ),
                        ],
                        events=[test_event(SAVE_TOKENS)],
                    ),
                ],
            ),
            folder(
                "7. Staff lookup and redemption",
                "Staff JWT required. Customer tokens get 403. Redeem the parent booking once.",
                [
                    item(
                        "Today's bookings",
                        staff_list,
                        [
                            example(
                                "200 OK — paid bookings",
                                200,
                                staff_list,
                                {
                                    "date": SLOT_DATE,
                                    "bookings": [
                                        {
                                            "booking_code": BOOKING_CODE,
                                            "status": "confirmed",
                                            "court_name": "Court 1",
                                            "start_time": "18:00",
                                            "end_time": "20:00",
                                            "booker_name": "Ahmed Hassan",
                                            "redeemed_at": None,
                                            "slots": TWO_SLOTS,
                                        }
                                    ],
                                },
                            ),
                            example(
                                "200 OK — none",
                                200,
                                staff_list,
                                {"date": SLOT_DATE, "bookings": []},
                            ),
                            example(
                                "401 Unauthorized — missing JWT",
                                401,
                                staff_list,
                                error("UNAUTHENTICATED", "Authentication credentials were not provided."),
                            ),
                            example(
                                "403 Forbidden — customer JWT used",
                                403,
                                staff_list,
                                error("FORBIDDEN", "Staff token required."),
                            ),
                        ],
                    ),
                    item(
                        "Lookup pass",
                        staff_lookup,
                        [
                            example("200 OK — valid, not redeemed", 200, staff_lookup, staff_pass()),
                            example(
                                "200 OK — already redeemed",
                                200,
                                staff_lookup,
                                staff_pass(
                                    status="redeemed",
                                    can_redeem=False,
                                    redeemed_at="2026-08-20T17:58:00+03:00",
                                ),
                            ),
                            example(
                                "401 Unauthorized",
                                401,
                                staff_lookup,
                                error("UNAUTHENTICATED", "Authentication credentials were not provided."),
                            ),
                            example(
                                "403 Forbidden — customer JWT used",
                                403,
                                staff_lookup,
                                error("FORBIDDEN", "Staff token required."),
                            ),
                            example(
                                "404 Not Found",
                                404,
                                staff_lookup,
                                error("NOT_FOUND", "No booking for this code."),
                            ),
                            example(
                                "409 Conflict — payment not confirmed",
                                409,
                                staff_lookup,
                                error("PAYMENT_NOT_CONFIRMED", "Payment not confirmed yet."),
                            ),
                        ],
                    ),
                    item(
                        "Redeem pass",
                        redeem,
                        [
                            example(
                                "200 OK — redeemed once",
                                200,
                                redeem,
                                staff_pass(
                                    status="redeemed",
                                    can_redeem=False,
                                    redeemed_at="2026-08-20T17:58:00+03:00",
                                ),
                            ),
                            example(
                                "401 Unauthorized",
                                401,
                                redeem,
                                error("UNAUTHENTICATED", "Authentication credentials were not provided."),
                            ),
                            example(
                                "403 Forbidden — customer JWT used",
                                403,
                                redeem,
                                error("FORBIDDEN", "Staff token required."),
                            ),
                            example(
                                "404 Not Found",
                                404,
                                redeem,
                                error("NOT_FOUND", "No booking for this code."),
                            ),
                            example(
                                "409 Conflict — already redeemed",
                                409,
                                redeem,
                                error("ALREADY_REDEEMED", "This pass was already redeemed at 17:58."),
                            ),
                            example(
                                "409 Conflict — payment not confirmed",
                                409,
                                redeem,
                                error("PAYMENT_NOT_CONFIRMED", "Payment not confirmed yet."),
                            ),
                            example(
                                "409 Conflict — wrong day",
                                409,
                                redeem,
                                error("WRONG_DAY", "This pass is for Thu 20 Aug 2026, not today."),
                            ),
                        ],
                    ),
                ],
                auth=bearer(),
            ),
            folder(
                "8. Invalid webhook example",
                "HMAC-first callback. The runnable example here is an invalid signature (401). A valid success body cannot be static without PAYMOB_HMAC_SECRET.",
                [
                    item(
                        "Reject forged HMAC",
                        webhook,
                        [
                            example(
                                "401 Unauthorized — invalid HMAC",
                                401,
                                webhook,
                                error("INVALID_HMAC", "Callback HMAC verification failed."),
                            ),
                            example(
                                "200 OK — booking confirmed (documented shape only)",
                                200,
                                webhook_placeholder,
                                {
                                    "received": True,
                                    "booking_id": BOOKING_ID,
                                    "status": "confirmed",
                                    "booking_code": BOOKING_CODE,
                                },
                            ),
                            example(
                                "200 OK — duplicate callback (idempotent)",
                                200,
                                webhook_placeholder,
                                {
                                    "received": True,
                                    "booking_id": BOOKING_ID,
                                    "status": "confirmed",
                                    "booking_code": BOOKING_CODE,
                                    "idempotent": True,
                                },
                            ),
                        ],
                    ),
                ],
            ),
        ],
    }


def build_environment():
    def value(key, val, secret=False, enabled=True):
        return {
            "key": key,
            "value": val,
            "type": "secret" if secret else "default",
            "enabled": enabled,
        }

    return {
        "id": ENVIRONMENT_ID,
        "name": "Mahgooz Local",
        "values": [
            value("base_url", "http://localhost:8000/api/v1"),
            value("access_token", "", secret=True),
            value("refresh_token", "", secret=True),
            value("court_id", COURT_1),
            value("booking_id", ""),
            value("booking_code", BOOKING_CODE),
            value("phone", "01012345678"),
            value("password", "secret12", secret=True),
            value("slot_date", SLOT_DATE),
            value("start_time", "18:00"),
            value("staff_phone", "01000000000"),
            value("staff_password", "staffpass", secret=True),
        ],
        "_postman_variable_scope": "environment",
    }


def main():
    COLLECTION_PATH.write_text(
        json.dumps(build_collection(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    ENVIRONMENT_PATH.write_text(
        json.dumps(build_environment(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {COLLECTION_PATH.relative_to(HERE.parent)}")
    print(f"Wrote {ENVIRONMENT_PATH.relative_to(HERE.parent)}")


if __name__ == "__main__":
    main()
