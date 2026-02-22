import os

import stripe


def _get_secret_key() -> str:
    key = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_RESTRICTED_KEY")
    if not key:
        raise RuntimeError("Missing STRIPE_SECRET_KEY or STRIPE_RESTRICTED_KEY in environment.")
    return key


def create_payment_link(
    amount_cents: int,
    currency: str = "usd",
    product_name: str = "FlashApply Premium",
    success_url: str | None = None,
) -> str:
    stripe.api_key = _get_secret_key()
    redirect_url = success_url or os.getenv("FLASHAPPLY_SUCCESS_URL", "http://localhost:8501/?payment=success")

    product = stripe.Product.create(name=product_name)
    price = stripe.Price.create(
        unit_amount=amount_cents,
        currency=currency,
        product=product.id,
    )
    link = stripe.PaymentLink.create(
        line_items=[{"price": price.id, "quantity": 1}],
        after_completion={"type": "redirect", "redirect": {"url": redirect_url}},
        metadata={"source": "flashapply_streamlit"},
    )
    return link.url
