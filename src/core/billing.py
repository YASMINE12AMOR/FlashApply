from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlencode

import stripe

from src.config.billing import (
    APP_BASE_URL,
    PREMIUM_CURRENCY,
    PREMIUM_PRICE_CENTS,
    PREMIUM_PRODUCT_DESCRIPTION,
    PREMIUM_PRODUCT_NAME,
)


class BillingError(Exception):
    pass


@dataclass
class CheckoutResult:
    checkout_url: str
    session_id: str


def _resolve_stripe_secret_key() -> str:
    key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not key:
        raise BillingError("Missing STRIPE_SECRET_KEY.")
    return key


def _build_return_urls() -> tuple[str, str]:
    success_qs = urlencode({"payment": "success", "session_id": "{CHECKOUT_SESSION_ID}"})
    cancel_qs = urlencode({"payment": "canceled"})
    success_url = f"{APP_BASE_URL}/?{success_qs}"
    cancel_url = f"{APP_BASE_URL}/?{cancel_qs}"
    return success_url, cancel_url


def create_checkout_session(email: str | None = None) -> CheckoutResult:
    stripe.api_key = _resolve_stripe_secret_key()
    success_url, cancel_url = _build_return_urls()

    session = stripe.checkout.Session.create(
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=(email.strip() if email else None),
        allow_promotion_codes=True,
        line_items=[
            {
                "price_data": {
                    "currency": PREMIUM_CURRENCY,
                    "unit_amount": PREMIUM_PRICE_CENTS,
                    "product_data": {
                        "name": PREMIUM_PRODUCT_NAME,
                        "description": PREMIUM_PRODUCT_DESCRIPTION,
                    },
                },
                "quantity": 1,
            }
        ],
    )
    return CheckoutResult(checkout_url=session.url, session_id=session.id)


def is_checkout_session_paid(session_id: str) -> bool:
    stripe.api_key = _resolve_stripe_secret_key()
    session = stripe.checkout.Session.retrieve(session_id)
    return bool(session and session.payment_status == "paid")
