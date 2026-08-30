"""
Agent Orchestrator
==================
Runs the full pipeline for a batch of PaymentEvents:

    Risk/Recovery Predictor -> Decision Engine -> Policy Engine
        -> Action Executor (Razorpay | Simulation) -> Outcome Verifier
        -> Audit Ledger -> Metrics

This is the P0 backbone described in spec sections 20-22. The LLM (if
used at all) only narrates/explains decisions already made here — it
never bypasses the policy/authorization checks below.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.adapters.base import RecoveryActionAdapter
from app.engine.audit_ledger import AuditLedger
from app.engine.decision_engine import decide
from app.engine.policy_engine import check as policy_check
from app.engine.risk_predictor import is_at_risk
from app.models import ActionCost, ActionType, ExecutionResult, PaymentEvent, Policy


@dataclass
class BatchState:
    """Tracks running totals needed by the policy engine across a batch
    (per-customer retry counts, spend against the shared recovery
    budget, contact attempts)."""

    retry_counts: dict[str, int] = field(default_factory=dict)
    contact_counts: dict[str, int] = field(default_factory=dict)
    budget_spent: float = 0.0


@dataclass
class BatchResult:
    events_processed: int = 0
    at_risk_count: int = 0
    eligible_count: int = 0
    intervention_count: int = 0
    recovered_count: int = 0
    revenue_at_risk: float = 0.0
    revenue_recovered: float = 0.0
    outcomes: dict[str, ExecutionResult] = field(default_factory=dict)


class Orchestrator:
    def __init__(
        self,
        adapter: RecoveryActionAdapter,
        *,
        policy: Policy = Policy(),
        costs: ActionCost = ActionCost(),
        ledger: AuditLedger | None = None,
    ):
        self.adapter = adapter
        self.policy = policy
        self.costs = costs
        self.ledger = ledger or AuditLedger()
        self.state = BatchState()

    def run_batch(self, events: list[PaymentEvent]) -> BatchResult:
        result = BatchResult()

        for event in events:
            result.events_processed += 1

            if not is_at_risk(event):
                continue
            result.at_risk_count += 1
            result.revenue_at_risk += event.amount
            self.ledger.log(event.transaction_id, "payment_failed", "Payment failed")
            if event.failure_reason:
                self.ledger.log(
                    event.transaction_id,
                    "failure_classified",
                    f"Failure classified: {event.failure_reason.value}",
                )

            decision = decide(event, self.costs)
            self.ledger.log(
                event.transaction_id,
                "recovery_probability",
                f"Recovery probability estimated",
                chosen_action=decision.chosen_action.value,
            )

            cost_for_action = next(
                (a.intervention_cost for a in decision.alternatives if a.action == decision.chosen_action),
                0.0,
            )

            pcheck = policy_check(
                decision,
                policy=self.policy,
                retry_count_so_far=self.state.retry_counts.get(event.customer_id, 0),
                budget_spent_so_far=self.state.budget_spent,
                contact_attempts_so_far=self.state.contact_counts.get(event.customer_id, 0),
                action_cost=cost_for_action,
                transaction_amount=event.amount,
            )
            for constraint in pcheck.constraints_applied:
                self.ledger.log(event.transaction_id, "policy_constraint", constraint)

            final_action = pcheck.final_action
            self.ledger.log(
                event.transaction_id,
                "action_selected",
                f"AI selected: {final_action.value}",
            )

            if final_action == ActionType.STOP:
                self.ledger.log(
                    event.transaction_id,
                    "recovery_stopped",
                    "Recovery workflow stopped — expected recovery too low or policy limit reached.",
                )
                continue

            result.eligible_count += 1
            if final_action in (ActionType.RETRY, ActionType.RETRY_LATER):
                self.state.retry_counts[event.customer_id] = (
                    self.state.retry_counts.get(event.customer_id, 0) + 1
                )
            if final_action == ActionType.NOTIFICATION:
                self.state.contact_counts[event.customer_id] = (
                    self.state.contact_counts.get(event.customer_id, 0) + 1
                )
            self.state.budget_spent += cost_for_action

            result.intervention_count += 1
            execution = self.adapter.execute(event, final_action)
            result.outcomes[event.transaction_id] = execution

            label = "[SIMULATED] " if execution.simulated else ""
            self.ledger.log(
                event.transaction_id,
                "action_executed",
                f"{label}{final_action.value} executed",
            )
            if execution.success:
                result.recovered_count += 1
                result.revenue_recovered += execution.amount_recovered
                self.ledger.log(
                    event.transaction_id,
                    "payment_recovered",
                    f"₹{execution.amount_recovered:,.2f} recovered",
                )
            else:
                self.ledger.log(event.transaction_id, "action_failed", execution.detail)

        return result
