from __future__ import annotations
import os

from app.models import FailureReason, PaymentEvent


def is_at_risk(event: PaymentEvent) -> bool:
    """A transaction is "at risk" if it failed and hasn't already
    exhausted recovery attempts."""
    return event.status == "failed"



_MODEL = None
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "risk_model.pkl")
try:
    import joblib
    if os.path.exists(_MODEL_PATH):
        _MODEL = joblib.load(_MODEL_PATH)
except ImportError:
    pass

def predict_recovery_probability(event: PaymentEvent) -> float:
    """Return a probability in [0, 1] that this payment can be recovered."""
    if _MODEL is not None:
        history = event.previous_success_count + event.previous_failure_count
        success_rate = event.previous_success_count / history if history > 0 else 0.5
        reason_map = {
            "temporary_bank_failure": 1,
            "insufficient_funds": 2,
            "card_expired": 3,
            "checkout_abandoned": 4,
            "subscription_payment_failure": 5,
            "overdue_payment": 6,
            "generic_decline": 7
        }
        reason_val = reason_map.get(event.failure_reason.value if event.failure_reason else "", 0)
        
        features = [[
            success_rate,
            history,
            event.last_activity_days_ago,
            event.retry_count,
            event.customer_age_days,
            reason_val,
            1 if event.mandate_available else 0
        ]]
        pred = _MODEL.predict(features)[0]
        return float(max(0.01, min(0.99, round(pred, 4))))

    # Fallback to hand-tuned logic if model not trained
    score = 0.5


    # Payment history is the strongest signal.
    total_history = event.previous_success_count + event.previous_failure_count
    if total_history > 0:
        success_rate = event.previous_success_count / total_history
        score += (success_rate - 0.5) * 0.6

    # Failure reason matters a lot: temporary issues recover well.
    reason_adjustment = {
        FailureReason.TEMPORARY_BANK_FAILURE: 0.20,
        FailureReason.INSUFFICIENT_FUNDS: -0.05,
        FailureReason.CARD_EXPIRED: -0.15,
        FailureReason.CHECKOUT_ABANDONED: -0.10,
        FailureReason.SUBSCRIPTION_PAYMENT_FAILURE: 0.05,
        FailureReason.OVERDUE_PAYMENT: -0.10,
        FailureReason.GENERIC_DECLINE: -0.05,
    }
    if event.failure_reason is not None:
        score += reason_adjustment.get(event.failure_reason, 0.0)

    # Recent activity correlates with willingness/ability to pay.
    if event.last_activity_days_ago <= 3:
        score += 0.10
    elif event.last_activity_days_ago > 30:
        score -= 0.15

    # Repeated retries on the same transaction erode probability.
    score -= 0.12 * event.retry_count

    # Very new customers are noisier / riskier.
    if event.customer_age_days < 7:
        score -= 0.05

    return max(0.01, min(0.99, round(score, 4)))


def risk_factors(event: PaymentEvent) -> list[str]:
    """Human-readable factors backing the probability estimate, used by
    the "Why this action?" panel."""
    factors: list[str] = []
    total_history = event.previous_success_count + event.previous_failure_count
    if event.previous_success_count >= 5:
        factors.append(f"✓ {event.previous_success_count} previous successful payments")
    if event.previous_failure_count >= 2:
        factors.append(f"✗ {event.previous_failure_count} previous failures")
    if event.failure_reason == FailureReason.TEMPORARY_BANK_FAILURE:
        factors.append("✓ Temporary failure")
    if event.last_activity_days_ago <= 3:
        factors.append("✓ Customer active recently")
    elif event.last_activity_days_ago > 30:
        factors.append("✗ Customer inactive for 30+ days")
    if event.mandate_available:
        factors.append("✓ Existing authorization available")
    else:
        factors.append("✗ No reusable authorization")
    if total_history == 0:
        factors.append("• No payment history yet")
    return factors
