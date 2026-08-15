"""One-off generator for the Mahgooz Postman collection. Run from backend/postman."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

OUT = Path(__file__).resolve().parent

COURT_1 = "11111111-1111-4111-8111-111111111111"
COURT_2 = "22222222-2222-4222-8222-222222222222"
BOOKING_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
USER_ID = "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
TXN_ID = 289187034
INTENTION_ID = "pi_test_8f3a1c2e"

BASE = "{{base_url}}"


def header_json():
    return [{"key": "Content-Type", "value": "application/json"}]


def header_auth(token_var="{{access_token}}"):
    return [
        {"key": "Authorization", "value": f"Bearer {token_var}"},
        {"key": "Content-Type", "value": "application/json"},
    ]


def header_auth_only(token_var="{{access_token}}"):
    return [{"key": "Authorization", "value": f"Bearer {token_var}"}]


def url(path: str, query: list[tuple[str, str]] | None = None):
    # String URL so {{base_url}} can include scheme + /api/v1 prefix.
    raw = f"{BASE}{path}"
    if query:
        raw += "?" + "&".join(f"{k}={v}" for k, v in query)
    return raw


def req(
    method: str,
    path: str,
    *,
    description: str,
    headers=None,
    body=None,
    query: list[tuple[str, str]] | None = None,
    auth=None,
):
    r = {
        "method": method,
        "header": headers or [],
        "url": url(path, query),
        "description": description,
    }
    if body is not None:
        r["body"] = {
            "mode": "raw",
            "raw": json.dumps(body, indent=2),
            "options": {"raw": {"language": "json"}},
        }
    if auth is not None:
        r["auth"] = auth
    return r


def example(name: str, original, status: str, code: int, body, headers=None):
    return {
        "name": name,
        "originalRequest": original,
        "status": status,
        "code": code,
        "_postman_previewlanguage": "json",
        "header": headers
        or [{"key": "Content-Type", "value": "application/json; charset=utf-8"}],
        "cookie": [],
        "body": json.dumps(body, indent=2) if not isinstance(body, str) else body,
    }


def err(code: str, message: str, details=None):
    payload = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return payload


def item(name, request, responses, events=None):
    obj = {"name": name, "request": request, "response": responses}
    if events:
        obj["event"] = events
    return obj


def test_script(lines: list[str]):
    return [
        {
            "listen": "test",
            "script": {"type": "text/javascript", "exec": lines},
        }
    ]


NO_AUTH = {"type": "noauth"}
BEARER_CUSTOMER = {
    "type": "bearer",
    "bearer": [{"key": "token", "value": "{{access_token}}", "type": "string"}],
}
BEARER_STAFF = {
    "type": "bearer",
    "bearer": [{"key": "token", "value": "{{staff_token}}", "type": "string"}],
}


# ---------------------------------------------------------------------------
# Shared example payloads
# ---------------------------------------------------------------------------

courts_ok = [
    {"id": COURT_1, "name": "Court 1", "slug": "court-1"},
    {"id": COURT_2, "name": "Court 2", "slug": "court-2"},
]

slots_ok = {
    "date": "2026-08-20",
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
            "start_time": "09:00",
            "end_time": "10:00",
            "state": "held",
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
        {
            "start_time": "20:00",
            "end_time": "21:00",
            "state": "available",
            "period": "evening",
            "price_egp": 350,
            "price_cents": 35000,
            "label": None,
        },
        {
            "start_time": "21:00",
            "end_time": "22:00",
            "state": "available",
            "period": "evening",
            "price_egp": 350,
            "price_cents": 35000,
            "label": None,
        },
    ],
}

hold_ok = {
    "id": BOOKING_ID,
    "status": "held",
    "court": {"id": COURT_1, "name": "Court 1"},
    "date": "2026-08-20",
    "start_time": "18:00",
    "end_time": "19:00",
    "booker_name": "Ahmed Hassan",
    "attendee_names": ["Ahmed Hassan", "Omar Ali", "Youssef Nabil", "Karim Fathy"],
    "price_egp": 350,
    "price_cents": 35000,
    "hold_expires_at": "2026-08-15T16:32:00+03:00",
    "booking_code": None,
    "created_at": "2026-08-15T16:22:00+03:00",
}

checkout_ok = {
    "booking_id": BOOKING_ID,
    "status": "pending_payment",
    "amount_egp": 350,
    "amount_cents": 35000,
    "currency": "EGP",
    "checkout_url": (
        "https://accept.paymob.com/unifiedcheckout/"
        "?publicKey=egy_pk_test_xxxxxxxx&clientSecret=egy_csk_test_xxxxxxxx"
    ),
    "paymob_intention_id": INTENTION_ID,
}

status_pending = {
    "id": BOOKING_ID,
    "status": "pending_payment",
    "booking_code": None,
    "hold_expires_at": "2026-08-15T16:32:00+03:00",
}

status_confirmed = {
    "id": BOOKING_ID,
    "status": "confirmed",
    "booking_code": "MGZ-7F42K",
    "pass_url": "/pass/MGZ-7F42K",
    "hold_expires_at": None,
}

status_failed = {
    "id": BOOKING_ID,
    "status": "failed",
    "booking_code": None,
    "hold_expires_at": None,
}

booking_confirmed = {
    "id": BOOKING_ID,
    "status": "confirmed",
    "court": {"id": COURT_1, "name": "Court 1"},
    "date": "2026-08-20",
    "start_time": "18:00",
    "end_time": "19:00",
    "booker_name": "Ahmed Hassan",
    "attendee_names": ["Ahmed Hassan", "Omar Ali", "Youssef Nabil", "Karim Fathy"],
    "price_egp": 350,
    "price_cents": 35000,
    "booking_code": "MGZ-7F42K",
    "qr_payload": "https://mahgooz.app/pass/MGZ-7F42K",
    "redeemed_at": None,
    "created_at": "2026-08-15T16:22:00+03:00",
    "paid_at": "2026-08-15T16:24:11+03:00",
}

my_bookings_ok = {
    "upcoming": [
        {
            "id": BOOKING_ID,
            "status": "confirmed",
            "court_name": "Court 1",
            "date": "2026-08-20",
            "start_time": "18:00",
            "end_time": "19:00",
            "price_egp": 350,
            "booking_code": "MGZ-7F42K",
            "period": "evening",
        }
    ],
    "past": [
        {
            "id": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
            "status": "redeemed",
            "court_name": "Court 2",
            "date": "2026-08-11",
            "start_time": "19:00",
            "end_time": "20:00",
            "price_egp": 350,
            "booking_code": "MGZ-2K91P",
            "period": "evening",
        }
    ],
}

public_pass_ok = {
    "booking_code": "MGZ-7F42K",
    "status": "confirmed",
    "court": {"id": COURT_1, "name": "Court 1"},
    "date": "2026-08-20",
    "start_time": "18:00",
    "end_time": "19:00",
    "booker_name": "Ahmed Hassan",
    "attendee_names": ["Ahmed Hassan", "Omar Ali", "Youssef Nabil", "Karim Fathy"],
    "price_egp": 350,
    "qr_payload": "https://mahgooz.app/pass/MGZ-7F42K",
    "redeemed_at": None,
}

staff_pass_ok = {
    "booking_code": "MGZ-7F42K",
    "status": "confirmed",
    "can_redeem": True,
    "court": {"id": COURT_1, "name": "Court 1"},
    "date": "2026-08-20",
    "start_time": "18:00",
    "end_time": "19:00",
    "booker_name": "Ahmed Hassan",
    "booker_phone": "01012345678",
    "attendee_names": ["Ahmed Hassan", "Omar Ali", "Youssef Nabil", "Karim Fathy"],
    "price_egp": 350,
    "paymob_transaction_id": TXN_ID,
    "redeemed_at": None,
}

staff_today_ok = {
    "date": "2026-08-20",
    "bookings": [
        {
            "booking_code": "MGZ-7F42K",
            "status": "confirmed",
            "court_name": "Court 1",
            "start_time": "18:00",
            "end_time": "19:00",
            "booker_name": "Ahmed Hassan",
            "redeemed_at": None,
        }
    ],
}

redeemed_ok = {
    "booking_code": "MGZ-7F42K",
    "status": "redeemed",
    "redeemed_at": "2026-08-20T17:58:00+03:00",
    "court": {"id": COURT_1, "name": "Court 1"},
    "date": "2026-08-20",
    "start_time": "18:00",
    "end_time": "19:00",
    "booker_name": "Ahmed Hassan",
    "attendee_names": ["Ahmed Hassan", "Omar Ali", "Youssef Nabil", "Karim Fathy"],
}

me_ok = {
    "id": USER_ID,
    "name": "Ahmed Hassan",
    "phone": "01012345678",
}

tokens_ok = {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh",
    "token_type": "Bearer",
    "expires_in": 3600,
}

staff_tokens_ok = {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.staff",
    "token_type": "Bearer",
    "role": "staff",
    "expires_in": 43200,
}

webhook_success_body = {
    "type": "TRANSACTION",
    "obj": {
        "id": TXN_ID,
        "pending": False,
        "amount_cents": 35000,
        "success": True,
        "is_auth": False,
        "is_capture": False,
        "is_standalone_payment": True,
        "is_voided": False,
        "is_refunded": False,
        "is_3d_secure": True,
        "integration_id": 123456,
        "profile_id": 98765,
        "has_parent_transaction": False,
        "order": {
            "id": 998877,
            "merchant_order_id": BOOKING_ID,
        },
        "created_at": "2026-08-15T13:24:11.123456",
        "currency": "EGP",
        "error_occured": False,
        "owner": 111222,
        "source_data": {
            "pan": "2346",
            "type": "card",
            "sub_type": "MasterCard",
        },
    },
    "hmac": "REPLACE_WITH_COMPUTED_HMAC_SHA512",
}

webhook_failed_body = {
    "type": "TRANSACTION",
    "obj": {
        **webhook_success_body["obj"],
        "success": False,
        "error_occured": True,
        "data": {"message": "Insufficient funds"},
    },
    "hmac": "REPLACE_WITH_COMPUTED_HMAC_SHA512",
}


# ---------------------------------------------------------------------------
# Folders
# ---------------------------------------------------------------------------


def folder_public():
    health_req = req(
        "GET",
        "/health",
        description=(
            "Liveness check for deploy/tunnel. No auth.\n\n"
            "Use this URL in ngrok health checks and as a smoke test after boot."
        ),
        headers=[],
        auth=NO_AUTH,
    )
    courts_req = req(
        "GET",
        "/courts",
        description="List the two seeded padel courts. No auth. Save `court_id` from the first item.",
        headers=[],
        auth=NO_AUTH,
    )
    slots_req = req(
        "GET",
        "/slots",
        description=(
            "Generated 08:00–21:00 grid for one court and date.\n\n"
            "**States:** `available` | `held` | `booked`. Held slots of other customers "
            "are never selectable.\n\n"
            "Morning slots include `label: \"Morning available\"` and a lower `price_egp`.\n\n"
            "Book-ahead window: today through 14 days. Slot duration: 60 minutes."
        ),
        headers=[],
        query=[("date", "{{slot_date}}"), ("court_id", "{{court_id}}")],
        auth=NO_AUTH,
    )
    pass_req = req(
        "GET",
        "/passes/{{booking_code}}",
        description=(
            "Public booking pass. Unlisted — you need the code. "
            "Omits phone and Paymob ids. Frontend renders QR from `qr_payload`.\n\n"
            "Codes are issued **only after** a verified Paymob webhook, so unpaid holds "
            "cannot be looked up here."
        ),
        headers=[],
        auth=NO_AUTH,
    )

    return {
        "name": "1. Public",
        "description": "No JWT. Health, courts, availability, and the shareable pass.",
        "item": [
            item(
                "Health",
                health_req,
                [
                    example("200 OK — healthy", health_req, "OK", 200, {"status": "ok"}),
                    example(
                        "503 Service Unavailable — database down",
                        health_req,
                        "Service Unavailable",
                        503,
                        err("UNHEALTHY", "Database unavailable"),
                    ),
                ],
            ),
            item(
                "List courts",
                courts_req,
                [
                    example("200 OK — two courts", courts_req, "OK", 200, courts_ok),
                    example(
                        "500 Internal Server Error",
                        courts_req,
                        "Internal Server Error",
                        500,
                        err("INTERNAL_ERROR", "Unexpected server error"),
                    ),
                ],
                test_script(
                    [
                        "if (pm.response.code === 200) {",
                        "  const courts = pm.response.json();",
                        "  if (Array.isArray(courts) && courts.length) {",
                        "    pm.collectionVariables.set('court_id', courts[0].id);",
                        "  }",
                        "}",
                    ]
                ),
            ),
            item(
                "List slots",
                slots_req,
                [
                    example("200 OK — slot grid", slots_req, "OK", 200, slots_ok),
                    example(
                        "400 Bad Request — missing date",
                        slots_req,
                        "Bad Request",
                        400,
                        err(
                            "VALIDATION_ERROR",
                            "Invalid query parameters",
                            {"date": ["This field is required."]},
                        ),
                    ),
                    example(
                        "400 Bad Request — date out of range",
                        slots_req,
                        "Bad Request",
                        400,
                        err(
                            "DATE_OUT_OF_RANGE",
                            "Date must be today or within the next 14 days.",
                        ),
                    ),
                    example(
                        "404 Not Found — unknown court",
                        slots_req,
                        "Not Found",
                        404,
                        err("NOT_FOUND", "Court not found."),
                    ),
                ],
            ),
            item(
                "Get public pass",
                pass_req,
                [
                    example("200 OK — confirmed pass", pass_req, "OK", 200, public_pass_ok),
                    example(
                        "200 OK — already redeemed",
                        pass_req,
                        "OK",
                        200,
                        {**public_pass_ok, "status": "redeemed", "redeemed_at": "2026-08-20T17:58:00+03:00"},
                    ),
                    example(
                        "404 Not Found — unknown or unpaid code",
                        pass_req,
                        "Not Found",
                        404,
                        err("NOT_FOUND", "No paid booking for this code."),
                    ),
                ],
            ),
        ],
    }


def folder_auth():
    register_body = {
        "name": "Ahmed Hassan",
        "phone": "{{phone}}",
        "password": "{{password}}",
    }
    register_req = req(
        "POST",
        "/auth/register",
        description=(
            "Create a customer account. Phone is the unique identifier "
            "(`01xxxxxxxxx`, 11 digits). Password min 6 characters.\n\n"
            "On success, tokens are returned so the client can book immediately."
        ),
        headers=header_json(),
        body=register_body,
        auth=NO_AUTH,
    )
    login_req = req(
        "POST",
        "/auth/login",
        description="Phone + password → JWT access and refresh. Saves tokens into collection variables.",
        headers=header_json(),
        body={"phone": "{{phone}}", "password": "{{password}}"},
        auth=NO_AUTH,
    )
    refresh_req = req(
        "POST",
        "/auth/refresh",
        description="Exchange a valid refresh token for a new access token.",
        headers=header_json(),
        body={"refresh": "{{refresh_token}}"},
        auth=NO_AUTH,
    )
    me_req = req(
        "GET",
        "/auth/me",
        description="Current customer profile. Requires customer JWT.",
        headers=header_auth_only(),
        auth=BEARER_CUSTOMER,
    )

    save_tokens = test_script(
        [
            "if (pm.response.code === 200 || pm.response.code === 201) {",
            "  const json = pm.response.json();",
            "  if (json.access) pm.collectionVariables.set('access_token', json.access);",
            "  if (json.refresh) pm.collectionVariables.set('refresh_token', json.refresh);",
            "}",
        ]
    )

    return {
        "name": "2. Customer auth",
        "description": "Phone + password JWT. No SMS OTP in MVP.",
        "item": [
            item(
                "Register",
                register_req,
                [
                    example("201 Created — account + tokens", register_req, "Created", 201, {
                        **tokens_ok,
                        "user": me_ok,
                    }),
                    example(
                        "400 Bad Request — invalid phone",
                        register_req,
                        "Bad Request",
                        400,
                        err(
                            "VALIDATION_ERROR",
                            "Invalid request body",
                            {"phone": ["Enter an Egyptian mobile number like 01xxxxxxxxx."]},
                        ),
                    ),
                    example(
                        "400 Bad Request — short password",
                        register_req,
                        "Bad Request",
                        400,
                        err(
                            "VALIDATION_ERROR",
                            "Invalid request body",
                            {"password": ["Ensure this field has at least 6 characters."]},
                        ),
                    ),
                    example(
                        "409 Conflict — phone taken",
                        register_req,
                        "Conflict",
                        409,
                        err("PHONE_TAKEN", "An account with this phone already exists."),
                    ),
                ],
                save_tokens,
            ),
            item(
                "Login",
                login_req,
                [
                    example("200 OK — tokens", login_req, "OK", 200, {**tokens_ok, "user": me_ok}),
                    example(
                        "400 Bad Request — missing fields",
                        login_req,
                        "Bad Request",
                        400,
                        err(
                            "VALIDATION_ERROR",
                            "Invalid request body",
                            {"password": ["This field is required."]},
                        ),
                    ),
                    example(
                        "401 Unauthorized — bad credentials",
                        login_req,
                        "Unauthorized",
                        401,
                        err("INVALID_CREDENTIALS", "Phone or password is incorrect."),
                    ),
                ],
                save_tokens,
            ),
            item(
                "Refresh token",
                refresh_req,
                [
                    example(
                        "200 OK — new access token",
                        refresh_req,
                        "OK",
                        200,
                        {"access": tokens_ok["access"], "token_type": "Bearer", "expires_in": 3600},
                    ),
                    example(
                        "401 Unauthorized — invalid refresh",
                        refresh_req,
                        "Unauthorized",
                        401,
                        err("UNAUTHENTICATED", "Refresh token is invalid or expired."),
                    ),
                ],
                test_script(
                    [
                        "if (pm.response.code === 200) {",
                        "  const json = pm.response.json();",
                        "  if (json.access) pm.collectionVariables.set('access_token', json.access);",
                        "}",
                    ]
                ),
            ),
            item(
                "Me",
                me_req,
                [
                    example("200 OK — profile", me_req, "OK", 200, me_ok),
                    example(
                        "401 Unauthorized — missing or expired JWT",
                        me_req,
                        "Unauthorized",
                        401,
                        err("UNAUTHENTICATED", "Authentication credentials were not provided."),
                    ),
                ],
            ),
        ],
    }


def folder_bookings():
    hold_body = {
        "court_id": "{{court_id}}",
        "date": "{{slot_date}}",
        "start_time": "{{start_time}}",
        "attendee_names": [
            "Ahmed Hassan",
            "Omar Ali",
            "Youssef Nabil",
            "Karim Fathy",
        ],
    }
    hold_req = req(
        "POST",
        "/bookings/hold",
        description=(
            "Atomically hold a slot for 10 minutes.\n\n"
            "Creates a `held` booking row. Postgres partial unique index on "
            "`court + date + start_time` (active statuses only) prevents double booking.\n\n"
            "**Attendee names** are required (1–4). Booker name is copied from the JWT user.\n\n"
            "On unique-constraint race: **409 SLOT_TAKEN**."
        ),
        headers=header_auth(),
        body=hold_body,
        auth=BEARER_CUSTOMER,
    )
    cancel_req = req(
        "DELETE",
        "/bookings/{{booking_id}}",
        description=(
            "Cancel own hold or unpaid booking and release the slot "
            "(`cancelled`). Confirmed/redeemed bookings cannot be cancelled in MVP (no refunds)."
        ),
        headers=header_auth_only(),
        auth=BEARER_CUSTOMER,
    )
    checkout_req = req(
        "POST",
        "/bookings/{{booking_id}}/checkout",
        description=(
            "Create a Paymob Intention for this hold and return Unified Checkout URL.\n\n"
            "Does **not** mark the booking paid. Status becomes `pending_payment`.\n\n"
            "`special_reference` sent to Paymob = booking UUID.\n\n"
            "If Paymob fails, status stays `held` so the customer can retry until TTL."
        ),
        headers=header_auth(),
        body={},
        auth=BEARER_CUSTOMER,
    )
    status_req = req(
        "GET",
        "/bookings/{{booking_id}}/status",
        description=(
            "Lightweight poll for `/book/pending`. Call every 2s for up to 60s.\n\n"
            "`confirmed` only after HMAC-verified webhook — never because the browser "
            "landed on Paymob's success redirect."
        ),
        headers=header_auth_only(),
        auth=BEARER_CUSTOMER,
    )
    list_req = req(
        "GET",
        "/bookings",
        description="Authenticated customer's upcoming and past bookings.",
        headers=header_auth_only(),
        auth=BEARER_CUSTOMER,
    )
    detail_req = req(
        "GET",
        "/bookings/{{booking_id}}",
        description="Owner-only booking detail. Includes `booking_code` after payment is confirmed.",
        headers=header_auth_only(),
        auth=BEARER_CUSTOMER,
    )

    return {
        "name": "3. Bookings (customer JWT)",
        "description": "Hold → checkout → poll status → my bookings. Pay → Reserve.",
        "auth": BEARER_CUSTOMER,
        "item": [
            item(
                "Hold a slot",
                hold_req,
                [
                    example("201 Created — slot held", hold_req, "Created", 201, hold_ok),
                    example(
                        "400 Bad Request — attendees",
                        hold_req,
                        "Bad Request",
                        400,
                        err(
                            "VALIDATION_ERROR",
                            "Invalid request body",
                            {
                                "attendee_names": [
                                    "Provide between 1 and 4 attendee names."
                                ]
                            },
                        ),
                    ),
                    example(
                        "400 Bad Request — past slot",
                        hold_req,
                        "Bad Request",
                        400,
                        err("PAST_SLOT", "Cannot book a slot that has already started."),
                    ),
                    example(
                        "401 Unauthorized",
                        hold_req,
                        "Unauthorized",
                        401,
                        err("UNAUTHENTICATED", "Authentication credentials were not provided."),
                    ),
                    example(
                        "409 Conflict — slot taken",
                        hold_req,
                        "Conflict",
                        409,
                        err(
                            "SLOT_TAKEN",
                            "This slot was just booked. Please choose another available slot.",
                        ),
                    ),
                ],
                test_script(
                    [
                        "if (pm.response.code === 201) {",
                        "  const json = pm.response.json();",
                        "  if (json.id) pm.collectionVariables.set('booking_id', json.id);",
                        "}",
                    ]
                ),
            ),
            item(
                "Cancel hold",
                cancel_req,
                [
                    example(
                        "200 OK — cancelled",
                        cancel_req,
                        "OK",
                        200,
                        {
                            "id": BOOKING_ID,
                            "status": "cancelled",
                            "message": "Slot released.",
                        },
                    ),
                    example(
                        "401 Unauthorized",
                        cancel_req,
                        "Unauthorized",
                        401,
                        err("UNAUTHENTICATED", "Authentication credentials were not provided."),
                    ),
                    example(
                        "403 Forbidden — not owner",
                        cancel_req,
                        "Forbidden",
                        403,
                        err("FORBIDDEN", "You do not own this booking."),
                    ),
                    example(
                        "404 Not Found",
                        cancel_req,
                        "Not Found",
                        404,
                        err("NOT_FOUND", "Booking not found."),
                    ),
                    example(
                        "409 Conflict — already paid",
                        cancel_req,
                        "Conflict",
                        409,
                        err(
                            "CANNOT_CANCEL",
                            "Paid bookings cannot be cancelled in MVP (no refunds).",
                        ),
                    ),
                ],
            ),
            item(
                "Start checkout",
                checkout_req,
                [
                    example("200 OK — Paymob checkout URL", checkout_req, "OK", 200, checkout_ok),
                    example(
                        "401 Unauthorized",
                        checkout_req,
                        "Unauthorized",
                        401,
                        err("UNAUTHENTICATED", "Authentication credentials were not provided."),
                    ),
                    example(
                        "404 Not Found",
                        checkout_req,
                        "Not Found",
                        404,
                        err("NOT_FOUND", "Booking not found."),
                    ),
                    example(
                        "409 Conflict — hold expired",
                        checkout_req,
                        "Conflict",
                        409,
                        err("HOLD_EXPIRED", "Your hold expired. Please pick the slot again."),
                    ),
                    example(
                        "409 Conflict — already paid",
                        checkout_req,
                        "Conflict",
                        409,
                        err("ALREADY_PAID", "This booking is already confirmed."),
                    ),
                    example(
                        "502 Bad Gateway — Paymob error",
                        checkout_req,
                        "Bad Gateway",
                        502,
                        err(
                            "PAYMOB_ERROR",
                            "Could not start checkout. Your slot is still held — try again.",
                        ),
                    ),
                ],
            ),
            item(
                "Poll payment status",
                status_req,
                [
                    example(
                        "200 OK — still pending",
                        status_req,
                        "OK",
                        200,
                        status_pending,
                    ),
                    example(
                        "200 OK — confirmed (after webhook)",
                        status_req,
                        "OK",
                        200,
                        status_confirmed,
                    ),
                    example(
                        "200 OK — payment failed",
                        status_req,
                        "OK",
                        200,
                        status_failed,
                    ),
                    example(
                        "200 OK — hold expired",
                        status_req,
                        "OK",
                        200,
                        {
                            "id": BOOKING_ID,
                            "status": "expired",
                            "booking_code": None,
                            "hold_expires_at": "2026-08-15T16:32:00+03:00",
                        },
                    ),
                    example(
                        "401 Unauthorized",
                        status_req,
                        "Unauthorized",
                        401,
                        err("UNAUTHENTICATED", "Authentication credentials were not provided."),
                    ),
                    example(
                        "403 Forbidden — not owner",
                        status_req,
                        "Forbidden",
                        403,
                        err("FORBIDDEN", "You do not own this booking."),
                    ),
                    example(
                        "404 Not Found",
                        status_req,
                        "Not Found",
                        404,
                        err("NOT_FOUND", "Booking not found."),
                    ),
                ],
                test_script(
                    [
                        "if (pm.response.code === 200) {",
                        "  const json = pm.response.json();",
                        "  if (json.booking_code) pm.collectionVariables.set('booking_code', json.booking_code);",
                        "}",
                    ]
                ),
            ),
            item(
                "My bookings",
                list_req,
                [
                    example("200 OK — upcoming and past", list_req, "OK", 200, my_bookings_ok),
                    example(
                        "200 OK — empty",
                        list_req,
                        "OK",
                        200,
                        {"upcoming": [], "past": []},
                    ),
                    example(
                        "401 Unauthorized",
                        list_req,
                        "Unauthorized",
                        401,
                        err("UNAUTHENTICATED", "Authentication credentials were not provided."),
                    ),
                ],
            ),
            item(
                "Booking detail",
                detail_req,
                [
                    example("200 OK — owner detail", detail_req, "OK", 200, booking_confirmed),
                    example(
                        "200 OK — still held (no code yet)",
                        detail_req,
                        "OK",
                        200,
                        {**hold_ok, "qr_payload": None, "redeemed_at": None, "paid_at": None},
                    ),
                    example(
                        "401 Unauthorized",
                        detail_req,
                        "Unauthorized",
                        401,
                        err("UNAUTHENTICATED", "Authentication credentials were not provided."),
                    ),
                    example(
                        "403 Forbidden — not owner",
                        detail_req,
                        "Forbidden",
                        403,
                        err("FORBIDDEN", "You do not own this booking."),
                    ),
                    example(
                        "404 Not Found",
                        detail_req,
                        "Not Found",
                        404,
                        err("NOT_FOUND", "Booking not found."),
                    ),
                ],
            ),
        ],
    }


def folder_staff():
    login_req = req(
        "POST",
        "/staff/login",
        description=(
            "Staff gate: 4-digit PIN from `STAFF_PIN` env. Returns a staff JWT "
            "(not a customer token). No staff user table in MVP."
        ),
        headers=header_json(),
        body={"pin": "{{staff_pin}}"},
        auth=NO_AUTH,
    )
    today_req = req(
        "GET",
        "/staff/bookings",
        description="Paid bookings for a date (default today), focused on the next ~12 hours.",
        headers=header_auth_only("{{staff_token}}"),
        query=[("date", "{{slot_date}}")],
        auth=BEARER_STAFF,
    )
    lookup_req = req(
        "GET",
        "/staff/passes/{{booking_code}}",
        description=(
            "Staff lookup of a pass. Includes phone and Paymob transaction id.\n\n"
            "`can_redeem` is true only when status is `confirmed`, it is the booking day, "
            "and it has not been redeemed."
        ),
        headers=header_auth_only("{{staff_token}}"),
        auth=BEARER_STAFF,
    )
    redeem_req = req(
        "POST",
        "/staff/passes/{{booking_code}}/redeem",
        description=(
            "Atomic one-time redeem: `UPDATE … WHERE booking_code=%s AND status='confirmed'`.\n\n"
            "Concurrent staff taps: only one 200, the other 409 ALREADY_REDEEMED."
        ),
        headers=header_auth("{{staff_token}}"),
        body={},
        auth=BEARER_STAFF,
    )

    return {
        "name": "4. Staff (staff JWT)",
        "description": "PIN login, today's list, lookup, redeem once.",
        "auth": BEARER_STAFF,
        "item": [
            item(
                "Staff login",
                login_req,
                [
                    example("200 OK — staff token", login_req, "OK", 200, staff_tokens_ok),
                    example(
                        "400 Bad Request — missing pin",
                        login_req,
                        "Bad Request",
                        400,
                        err(
                            "VALIDATION_ERROR",
                            "Invalid request body",
                            {"pin": ["This field is required."]},
                        ),
                    ),
                    example(
                        "401 Unauthorized — wrong pin",
                        login_req,
                        "Unauthorized",
                        401,
                        err("INVALID_PIN", "Staff PIN is incorrect."),
                    ),
                ],
                test_script(
                    [
                        "if (pm.response.code === 200) {",
                        "  const json = pm.response.json();",
                        "  if (json.access) pm.collectionVariables.set('staff_token', json.access);",
                        "}",
                    ]
                ),
            ),
            item(
                "Today's bookings",
                today_req,
                [
                    example("200 OK — paid bookings", today_req, "OK", 200, staff_today_ok),
                    example("200 OK — none", today_req, "OK", 200, {"date": "2026-08-20", "bookings": []}),
                    example(
                        "401 Unauthorized — missing staff JWT",
                        today_req,
                        "Unauthorized",
                        401,
                        err("UNAUTHENTICATED", "Authentication credentials were not provided."),
                    ),
                    example(
                        "403 Forbidden — customer JWT used",
                        today_req,
                        "Forbidden",
                        403,
                        err("FORBIDDEN", "Staff token required."),
                    ),
                ],
            ),
            item(
                "Lookup pass",
                lookup_req,
                [
                    example("200 OK — valid, not redeemed", lookup_req, "OK", 200, staff_pass_ok),
                    example(
                        "200 OK — already redeemed",
                        lookup_req,
                        "OK",
                        200,
                        {
                            **staff_pass_ok,
                            "status": "redeemed",
                            "can_redeem": False,
                            "redeemed_at": "2026-08-20T17:58:00+03:00",
                        },
                    ),
                    example(
                        "401 Unauthorized",
                        lookup_req,
                        "Unauthorized",
                        401,
                        err("UNAUTHENTICATED", "Authentication credentials were not provided."),
                    ),
                    example(
                        "404 Not Found",
                        lookup_req,
                        "Not Found",
                        404,
                        err("NOT_FOUND", "No booking for this code."),
                    ),
                    example(
                        "409 Conflict — payment not confirmed",
                        lookup_req,
                        "Conflict",
                        409,
                        err("PAYMENT_NOT_CONFIRMED", "Payment not confirmed yet."),
                    ),
                ],
            ),
            item(
                "Redeem pass",
                redeem_req,
                [
                    example("200 OK — redeemed once", redeem_req, "OK", 200, redeemed_ok),
                    example(
                        "401 Unauthorized",
                        redeem_req,
                        "Unauthorized",
                        401,
                        err("UNAUTHENTICATED", "Authentication credentials were not provided."),
                    ),
                    example(
                        "403 Forbidden — customer JWT used",
                        redeem_req,
                        "Forbidden",
                        403,
                        err("FORBIDDEN", "Staff token required."),
                    ),
                    example(
                        "404 Not Found",
                        redeem_req,
                        "Not Found",
                        404,
                        err("NOT_FOUND", "No booking for this code."),
                    ),
                    example(
                        "409 Conflict — already redeemed",
                        redeem_req,
                        "Conflict",
                        409,
                        err(
                            "ALREADY_REDEEMED",
                            "This pass was already redeemed at 17:58.",
                        ),
                    ),
                    example(
                        "409 Conflict — payment not confirmed",
                        redeem_req,
                        "Conflict",
                        409,
                        err("PAYMENT_NOT_CONFIRMED", "Payment not confirmed yet."),
                    ),
                    example(
                        "409 Conflict — wrong day",
                        redeem_req,
                        "Conflict",
                        409,
                        err(
                            "WRONG_DAY",
                            "This pass is for Wed 20 Aug 2026, not today.",
                        ),
                    ),
                ],
            ),
        ],
    }


def folder_webhooks():
    success_req = req(
        "POST",
        "/webhooks/paymob",
        description=(
            "**Source of truth for payment.** Paymob POSTs here; the browser redirect is ignored.\n\n"
            "1. Verify HMAC-SHA512 with `PAYMOB_HMAC_SECRET` using Paymob's documented field order.\n"
            "2. Reject mismatch with **401 INVALID_HMAC** — do not update the booking.\n"
            "3. On `obj.success === true`: set status `confirmed`, issue `booking_code`, "
            "store unique `paymob_transaction_id` (idempotent on retries).\n"
            "4. On failure: set status `failed` and release the slot.\n\n"
            "`obj.order.merchant_order_id` / `special_reference` = booking UUID.\n\n"
            "**This saved success body uses a placeholder hmac.** A live 200 requires a "
            "signature computed against your `PAYMOB_HMAC_SECRET`. The invalid-hmac example "
            "is what you can send as-is to test rejection."
        ),
        headers=header_json(),
        body=webhook_success_body,
        auth=NO_AUTH,
    )
    failed_req = req(
        "POST",
        "/webhooks/paymob",
        description=(
            "Same endpoint, payment-failed payload. After HMAC verify, booking becomes "
            "`failed` and the court+slot is bookable again."
        ),
        headers=header_json(),
        body=webhook_failed_body,
        auth=NO_AUTH,
    )
    forged = {**webhook_success_body, "hmac": "deadbeef" * 16}
    forged_req = req(
        "POST",
        "/webhooks/paymob",
        description="Forged callback: hmac does not match. Booking must stay unpaid.",
        headers=header_json(),
        body=forged,
        auth=NO_AUTH,
    )

    return {
        "name": "5. Paymob webhook (HMAC, no JWT)",
        "description": (
            "Public URL that Paymob calls. Must be reachable from the internet "
            "(ngrok / Cloudflare Tunnel). Never treat the frontend redirect as paid."
        ),
        "item": [
            item(
                "Payment success (placeholder HMAC)",
                success_req,
                [
                    example(
                        "200 OK — booking confirmed",
                        success_req,
                        "OK",
                        200,
                        {
                            "received": True,
                            "booking_id": BOOKING_ID,
                            "status": "confirmed",
                            "booking_code": "MGZ-7F42K",
                        },
                    ),
                    example(
                        "200 OK — duplicate callback (idempotent)",
                        success_req,
                        "OK",
                        200,
                        {
                            "received": True,
                            "booking_id": BOOKING_ID,
                            "status": "confirmed",
                            "booking_code": "MGZ-7F42K",
                            "idempotent": True,
                        },
                    ),
                    example(
                        "400 Bad Request — malformed payload",
                        success_req,
                        "Bad Request",
                        400,
                        err("VALIDATION_ERROR", "Unrecognized Paymob callback payload."),
                    ),
                    example(
                        "401 Unauthorized — invalid HMAC",
                        success_req,
                        "Unauthorized",
                        401,
                        err("INVALID_HMAC", "Callback HMAC verification failed."),
                    ),
                    example(
                        "404 Not Found — unknown booking reference",
                        success_req,
                        "Not Found",
                        404,
                        err("NOT_FOUND", "No booking matches this payment reference."),
                    ),
                ],
            ),
            item(
                "Payment failed (placeholder HMAC)",
                failed_req,
                [
                    example(
                        "200 OK — slot released",
                        failed_req,
                        "OK",
                        200,
                        {
                            "received": True,
                            "booking_id": BOOKING_ID,
                            "status": "failed",
                        },
                    ),
                    example(
                        "401 Unauthorized — invalid HMAC",
                        failed_req,
                        "Unauthorized",
                        401,
                        err("INVALID_HMAC", "Callback HMAC verification failed."),
                    ),
                ],
            ),
            item(
                "Forged callback (invalid HMAC)",
                forged_req,
                [
                    example(
                        "401 Unauthorized — rejected, booking unchanged",
                        forged_req,
                        "Unauthorized",
                        401,
                        err("INVALID_HMAC", "Callback HMAC verification failed."),
                    ),
                ],
            ),
        ],
    }


def build_collection():
    return {
        "info": {
            "_postman_id": str(uuid4()),
            "name": "Mahgooz API — MVP v1",
            "description": (
                "# Mahgooz padel booking — MVP v1\n\n"
                "Django REST API for **Pay → Reserve → Redeem**.\n\n"
                "## Base URL\n"
                "`{{base_url}}` defaults to `http://localhost:8000/api/v1`.\n\n"
                "## Auth\n"
                "- **Customer JWT** (`Authorization: Bearer {{access_token}}`) on booking routes.\n"
                "- **Staff JWT** (`{{staff_token}}`) from PIN login — not interchangeable with customer tokens.\n"
                "- **Webhook** has no JWT; authenticity is HMAC-SHA512.\n"
                "- Public pass, courts, slots, and health need no auth.\n\n"
                "## Suggested run order\n"
                "1. Health → List courts (saves `court_id`)\n"
                "2. Register or Login (saves `access_token`)\n"
                "3. List slots → Hold a slot (saves `booking_id`)\n"
                "4. Start checkout → open `checkout_url` in a browser with a Paymob test card\n"
                "5. Poll payment status until `confirmed` (saves `booking_code`)\n"
                "6. Get public pass\n"
                "7. Staff login (saves `staff_token`) → Lookup → Redeem\n\n"
                "## Error shape\n"
                "```json\n"
                '{ \"error\": { \"code\": \"SLOT_TAKEN\", \"message\": \"...\" } }\n'
                "```\n\n"
                "Every request has saved **success and failure examples** in the Examples dropdown.\n\n"
                "## Slot rules\n"
                "- Two courts, 60-minute slots, 08:00–22:00, book 14 days ahead.\n"
                "- Hold TTL **10 minutes**. Abandoned / failed / expired holds free the slot.\n"
                "- Unique active row: `court + date + start_time`.\n"
                "- Pricing: morning EGP 200 (08–12), afternoon 280 (12–17), evening 350 (17–22).\n"
                "- A booking is **paid only** after a verified Paymob webhook, never after the redirect page.\n"
            ),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {"key": "base_url", "value": "http://localhost:8000/api/v1"},
            {"key": "access_token", "value": ""},
            {"key": "refresh_token", "value": ""},
            {"key": "staff_token", "value": ""},
            {"key": "court_id", "value": COURT_1},
            {"key": "booking_id", "value": ""},
            {"key": "booking_code", "value": "MGZ-7F42K"},
            {"key": "staff_pin", "value": "1234"},
            {"key": "phone", "value": "01012345678"},
            {"key": "password", "value": "secret12"},
            {"key": "slot_date", "value": "2026-08-20"},
            {"key": "start_time", "value": "18:00"},
        ],
        "auth": BEARER_CUSTOMER,
        "item": [
            folder_public(),
            folder_auth(),
            folder_bookings(),
            folder_staff(),
            folder_webhooks(),
        ],
    }


def build_environment():
    return {
        "id": str(uuid4()),
        "name": "Mahgooz Local",
        "values": [
            {
                "key": "base_url",
                "value": "http://localhost:8000/api/v1",
                "type": "default",
                "enabled": True,
            },
            {"key": "access_token", "value": "", "type": "secret", "enabled": True},
            {"key": "refresh_token", "value": "", "type": "secret", "enabled": True},
            {"key": "staff_token", "value": "", "type": "secret", "enabled": True},
            {"key": "court_id", "value": COURT_1, "type": "default", "enabled": True},
            {"key": "booking_id", "value": "", "type": "default", "enabled": True},
            {
                "key": "booking_code",
                "value": "MGZ-7F42K",
                "type": "default",
                "enabled": True,
            },
            {"key": "staff_pin", "value": "1234", "type": "secret", "enabled": True},
            {
                "key": "phone",
                "value": "01012345678",
                "type": "default",
                "enabled": True,
            },
            {"key": "password", "value": "secret12", "type": "secret", "enabled": True},
            {
                "key": "slot_date",
                "value": "2026-08-20",
                "type": "default",
                "enabled": True,
            },
            {
                "key": "start_time",
                "value": "18:00",
                "type": "default",
                "enabled": True,
            },
        ],
        "_postman_variable_scope": "environment",
    }


def main():
    collection = build_collection()
    environment = build_environment()
    (OUT / "Mahgooz_API.postman_collection.json").write_text(
        json.dumps(collection, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "Mahgooz_Local.postman_environment.json").write_text(
        json.dumps(environment, indent=2) + "\n", encoding="utf-8"
    )
    n_req = 0
    n_ex = 0

    def walk(items):
        nonlocal n_req, n_ex
        for it in items:
            if "item" in it:
                walk(it["item"])
            else:
                n_req += 1
                n_ex += len(it.get("response") or [])

    walk(collection["item"])
    print(f"Wrote collection with {n_req} requests and {n_ex} examples")


if __name__ == "__main__":
    main()
