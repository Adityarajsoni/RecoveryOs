"""
Recovery Decision Engine
=========================
Stage 2 of the pipeline. For every at-risk PaymentEvent, evaluates every
candidate action and selects the one with the highest expected net
recovery:

    expected_net_recovery = (probability * amount) - intervention_cost

Probabilities are action-specific: retrying a temporarily-failed payment
recovers differently than sending a payment link or escalating to a
human. This is intentionally simple / explainable for the hackathon —
see risk_predictor.py for where a trained model would plug in.

All financial actions still have to pass through the PolicyEngine and
authorization checks (see policy_engine.py, adapters/) before execution.
Nothing here executes anything.
"""

from __future__ import annotations

from app.engine.risk_predictor import predict_recovery_probability, risk_factors
from app.models import (
    ActionCost,
    ActionType,
    AuthorizationBasis,
    ExpectedRecovery,
    PaymentEvent,
    RecoveryDecision,
)

DEFAULT_COSTS = ActionCost()

# Multiplier applied to the base recovery probability for each action,
# reflecting that not every action is equally effective.
ACTION_EFFECTIVENESS = {
    ActionType.RETRY: 1.00,
    ActionType.RETRY_LATER: 0.85,
    ActionType.PAYMENT_LINK: 0.65,
    ActionType.NOTIFICATION: 0.45,
    ActionType.ESCALATE: 0.55,
}

MIN_VIABLE_NET_RECOVERY = 0.0  # below this, STOP is preferred


def _authorization_basis(event: PaymentEvent) -> AuthorizationBasis:
    if event.mandate_available:
        return AuthorizationBasis.EXISTING_MANDATE
    return AuthorizationBasis.NONE


def _candidate_actions(event: PaymentEvent) -> list[ActionType]:
    """The allowlist of actions available for this transaction.
    RETRY (an automatic debit-style action) is only a candidate when an
    authorization basis exists — this is the safety boundary described
    in the spec: no arbitrary debits.
    """
    actions = [ActionType.PAYMENT_LINK, ActionType.NOTIFICATION, ActionType.ESCALATE]
    if event.mandate_available:
        actions.insert(0, ActionType.RETRY)
        actions.insert(1, ActionType.RETRY_LATER)
    return actions


def evaluate_actions(
    event: PaymentEvent, costs: ActionCost = DEFAULT_COSTS
) -> list[ExpectedRecovery]:
    base_probability = predict_recovery_probability(event)
    cost_map = {
        ActionType.RETRY: costs.retry,
        ActionType.RETRY_LATER: costs.retry,
        ActionType.PAYMENT_LINK: costs.payment_link,
        ActionType.NOTIFICATION: costs.notification,
        ActionType.ESCALATE: costs.escalation,
    }

    results: list[ExpectedRecovery] = []
    for action in _candidate_actions(event):
        probability = min(0.99, base_probability * ACTION_EFFECTIVENESS[action])
        cost = cost_map[action]
        expected_revenue = probability * event.amount
        expected_net = expected_revenue - cost
        results.append(
            ExpectedRecovery(
                action=action,
                probability=round(probability, 4),
                expected_revenue=round(expected_revenue, 2),
                intervention_cost=cost,
                expected_net_recovery=round(expected_net, 2),
            )
        )
    return results


def decide(event: PaymentEvent, costs: ActionCost = DEFAULT_COSTS) -> RecoveryDecision:
    """Pick the action with the highest expected net recovery, or STOP if
    nothing clears the minimum viable threshold."""
    alternatives = evaluate_actions(event, costs)
    best = max(alternatives, key=lambda a: a.expected_net_recovery, default=None)

    if best is None or best.expected_net_recovery <= MIN_VIABLE_NET_RECOVERY:
        reasoning = (
            "Expected recovery is too low to justify another attempt."
            if best is not None
            else "No viable recovery action for this transaction."
        )
        chosen_action = ActionType.STOP
        chosen_net = 0.0
    else:
        chosen_action = best.action
        chosen_net = best.expected_net_recovery
        reasoning = (
            f"{chosen_action.value.replace('_', ' ').title()} selected because it has the "
            f"highest expected net recovery (₹{chosen_net:,.0f}) among available actions, "
            "consistent with this customer's payment history and failure type."
        )

    return RecoveryDecision(
        transaction_id=event.transaction_id,
        chosen_action=chosen_action,
        chosen_expected_net=chosen_net,
        alternatives=alternatives,
        authorization_basis=_authorization_basis(event),
        reasoning=reasoning,
        factors=risk_factors(event),
    )
