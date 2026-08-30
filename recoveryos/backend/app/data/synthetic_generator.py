"""
Synthetic Dataset Generator
============================
Produces a reproducible batch of synthetic payment events (spec section
10) with realistic-ish distributions: most events succeed, a minority
fail for varied reasons, and failed events have varied customer/payment
context so the decision engine has something interesting to reason
about. Seeded for a reproducible demo (spec section 24).
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

from app.models import (
    FailureReason,
    PaymentEvent,
    PaymentMethod,
    SubscriptionStatus,
)

FAILURE_REASONS = list(FailureReason)
PAYMENT_METHODS = list(PaymentMethod)
SUBSCRIPTION_STATUSES = list(SubscriptionStatus)

# Roughly mirrors the spec's headline numbers: ~10,000 events,
# ~18% at-risk (failed).
FAILURE_RATE = 0.185


def generate_batch(n: int = 10_000, seed: int = 42) -> list[PaymentEvent]:
    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    events: list[PaymentEvent] = []

    for i in range(n):
        customer_id = f"cust_{rng.randint(1, max(1, n // 4)):06d}"
        is_failed = rng.random() < FAILURE_RATE

        prev_success = max(0, int(rng.gauss(6, 5)))
        prev_failure = max(0, int(rng.gauss(1, 1.5)))
        customer_age_days = max(1, int(rng.gauss(240, 200)))
        last_activity = max(0, int(rng.expovariate(1 / 10)))
        if rng.random() > 0.05:
            amount = round(rng.uniform(100.0, 5000.0), 2)
        else:
            amount = round(rng.uniform(5000.0, 50000.0), 2)
        mandate_available = rng.random() < 0.55

        event = PaymentEvent(
            transaction_id=f"txn_{uuid.uuid4().hex[:10]}",
            customer_id=customer_id,
            amount=amount,
            payment_method=rng.choice(PAYMENT_METHODS),
            status="failed" if is_failed else "success",
            failure_reason=rng.choice(FAILURE_REASONS) if is_failed else None,
            timestamp=now - timedelta(minutes=rng.randint(0, 60 * 24 * 7)),
            customer_age_days=customer_age_days,
            previous_success_count=prev_success,
            previous_failure_count=prev_failure,
            subscription_status=rng.choice(SUBSCRIPTION_STATUSES),
            last_activity_days_ago=last_activity,
            mandate_available=mandate_available,
            retry_count=rng.randint(0, 2) if is_failed else 0,
        )
        events.append(event)

    return events
