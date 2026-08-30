"""
Policy Engine
=============
Deterministic gate that sits between the Decision Engine's recommendation
and the Action Executor. The LLM/decision engine can *recommend*, but only
this module (plus the authorization check) can permit an action to run.
This is the "AI must never exceed these policies" boundary from the spec.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models import ActionType, AuthorizationBasis, Policy, RecoveryDecision


@dataclass
class PolicyCheckResult:
    allowed: bool
    final_action: ActionType
    requires_human_approval: bool
    constraints_applied: list[str]


def check(
    decision: RecoveryDecision,
    *,
    policy: Policy,
    retry_count_so_far: int,
    budget_spent_so_far: float,
    contact_attempts_so_far: int,
    action_cost: float,
    transaction_amount: float,
) -> PolicyCheckResult:
    constraints: list[str] = []
    action = decision.chosen_action

    # 1. Authorization: RETRY-style actions require an existing mandate.
    if action in (ActionType.RETRY, ActionType.RETRY_LATER) and (
        decision.authorization_basis == AuthorizationBasis.NONE
    ):
        constraints.append("No reusable authorization — direct debit blocked")
        action = ActionType.PAYMENT_LINK

    # 2. Retry limit.
    if action in (ActionType.RETRY, ActionType.RETRY_LATER) and (
        retry_count_so_far >= policy.max_retries
    ):
        constraints.append(f"Retry limit reached (max_retries={policy.max_retries})")
        action = ActionType.STOP

    # 3. Recovery budget.
    if budget_spent_so_far + action_cost > policy.max_recovery_budget:
        constraints.append(
            f"Recovery budget exhausted (₹{budget_spent_so_far:,.0f} of "
            f"₹{policy.max_recovery_budget:,.0f} already spent)"
        )
        action = ActionType.STOP

    # 4. Feature toggles.
    if action == ActionType.PAYMENT_LINK and not policy.auto_generate_payment_links:
        constraints.append("Auto payment-link generation disabled by merchant policy")
        action = ActionType.ESCALATE
    if action == ActionType.NOTIFICATION and not policy.auto_send_notifications:
        constraints.append("Auto customer notifications disabled by merchant policy")
        action = ActionType.ESCALATE

    # 5. Contact attempt cap.
    if action == ActionType.NOTIFICATION and (
        contact_attempts_so_far >= policy.max_customer_contact_attempts
    ):
        constraints.append(
            f"Customer contact attempt limit reached (max={policy.max_customer_contact_attempts})"
        )
        action = ActionType.STOP

    # 6. Human-approval threshold for large amounts.
    requires_human_approval = transaction_amount > policy.human_approval_above
    if requires_human_approval and action != ActionType.STOP:
        constraints.append(
            f"Amount exceeds human-approval threshold (₹{policy.human_approval_above:,.0f})"
        )
        action = ActionType.ESCALATE

    return PolicyCheckResult(
        allowed=action != ActionType.STOP,
        final_action=action,
        requires_human_approval=requires_human_approval,
        constraints_applied=constraints,
    )
