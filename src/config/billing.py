from __future__ import annotations

import os

FREE_ANALYSIS_LIMIT = int(os.getenv("FREE_ANALYSIS_LIMIT", "3"))
PREMIUM_PRICE_CENTS = int(os.getenv("STRIPE_PREMIUM_PRICE_CENTS", "900"))
PREMIUM_CURRENCY = os.getenv("STRIPE_CURRENCY", "usd").lower()
PREMIUM_PRODUCT_NAME = os.getenv("STRIPE_PREMIUM_PRODUCT_NAME", "ApplyFlash Premium")
PREMIUM_PRODUCT_DESCRIPTION = os.getenv(
    "STRIPE_PREMIUM_PRODUCT_DESCRIPTION",
    "Unlock premium PDF export, unlimited analyses, and advanced country templates.",
)
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8501").rstrip("/")

# Free tier has a smaller country set; premium unlocks all.
FREE_COUNTRIES = {"USA", "UK", "Canada"}
