"""
Simulation Adapter
===================
Used whenever an action isn't backed by a real Razorpay test-mode call
(or when RAZORPAY_MODE=simulate). Outcomes are drawn from the same
recovery-probability model the Decision Engine used, so the batch-level
metrics stay internally consistent — but every result is clearly labeled
`simulated=True` and must be rendered as such in the UI/audit trail.
"""

from __future__ import annotations

import random

from app.adapters.base import RecoveryActionAdapter
from app.engine.risk_predictor import predict_recovery_probability
from app.models import ActionType, ExecutionResult, PaymentEvent


class SimulationAdapter(RecoveryActionAdapter):
    simulated = True

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def execute(self, event: PaymentEvent, action: ActionType) -> ExecutionResult:
        if action == ActionType.STOP:
            return ExecutionResult(
                transaction_id=event.transaction_id,
                action=action,
                simulated=True,
                success=False,
                amount_recovered=0.0,
                detail="Recovery workflow stopped — no action taken.",
            )

        probability = predict_recovery_probability(event)
        # Action-specific effectiveness mirrors decision_engine.ACTION_EFFECTIVENESS
        # to keep simulated outcomes consistent with what was predicted.
        effectiveness = {
            ActionType.RETRY: 1.00,
            ActionType.RETRY_LATER: 0.85,
            ActionType.PAYMENT_LINK: 0.65,
            ActionType.NOTIFICATION: 0.45,
            ActionType.ESCALATE: 0.55,
        }.get(action, 0.5)

        success = self._rng.random() < probability * effectiveness
        amount_recovered = event.amount if success else 0.0
        detail = (
            f"[SIMULATED] {action.value} executed — "
            + ("payment succeeded." if success else "payment not completed.")
        )

        return ExecutionResult(
            transaction_id=event.transaction_id,
            action=action,
            simulated=True,
            success=success,
            amount_recovered=amount_recovered,
            razorpay_reference=None,
            detail=detail,
        )
