"""
Core data models for RecoveryOS.

These mirror the fields described in the buildathon spec:
 - PaymentEvent: one synthetic transaction / failure event
 - CustomerContext / PaymentContext: inputs to the decision engine
 - ActionType: the allowed action set (allowlist)
 - RecoveryDecision: the engine's chosen action + explanation
 - Policy: merchant-configurable guardrails
 - AuditEvent: one entry in the immutable audit ledger
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FailureReason(str, Enum):
    TEMPORARY_BANK_FAILURE = "temporary_bank_failure"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    CARD_EXPIRED = "card_expired"
    CHECKOUT_ABANDONED = "checkout_abandoned"
    SUBSCRIPTION_PAYMENT_FAILURE = "subscription_payment_failure"
    OVERDUE_PAYMENT = "overdue_payment"
    GENERIC_DECLINE = "generic_decline"


class PaymentMethod(str, Enum):
    CARD = "card"
    UPI = "upi"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    EMANDATE = "emandate"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    NONE = "none"


class ActionType(str, Enum):
    RETRY = "retry"
    RETRY_LATER = "retry_later"
    PAYMENT_LINK = "payment_link"
    NOTIFICATION = "notification"
    ESCALATE = "escalate"
    STOP = "stop"


class AuthorizationBasis(str, Enum):
    EXISTING_MANDATE = "existing_mandate"
    SAVED_CARD_TOKEN = "saved_card_token"
    NONE = "none"


class PaymentEvent(BaseModel):
    """One synthetic payment/subscription/checkout event."""

    transaction_id: str
    customer_id: str
    amount: float
    payment_method: PaymentMethod
    status: str  # e.g. "failed", "success"
    failure_reason: Optional[FailureReason] = None
    timestamp: datetime
    customer_age_days: int
    previous_success_count: int
    previous_failure_count: int
    subscription_status: SubscriptionStatus
    last_activity_days_ago: int
    mandate_available: bool
    retry_count: int = 0


class ExpectedRecovery(BaseModel):
    action: ActionType
    probability: float
    expected_revenue: float
    intervention_cost: float
    expected_net_recovery: float


class RecoveryDecision(BaseModel):
    transaction_id: str
    chosen_action: ActionType
    chosen_expected_net: float
    alternatives: list[ExpectedRecovery]
    authorization_basis: AuthorizationBasis
    reasoning: str
    factors: list[str]
    policy_constraints_applied: list[str] = Field(default_factory=list)


class Policy(BaseModel):
    max_retries: int = 2
    max_recovery_budget: float = 10_000.0
    auto_generate_payment_links: bool = True
    auto_send_notifications: bool = True
    human_approval_above: float = 25_000.0
    max_customer_contact_attempts: int = 2


class ActionCost(BaseModel):
    retry: float = 0.0
    payment_link: float = 1.0
    notification: float = 2.0
    escalation: float = 50.0
    incentive: float = 100.0


class ExecutionResult(BaseModel):
    transaction_id: str
    action: ActionType
    simulated: bool
    success: bool
    amount_recovered: float = 0.0
    razorpay_reference: Optional[str] = None
    detail: str = ""


class AuditEvent(BaseModel):
    transaction_id: str
    timestamp: datetime
    event_type: str
    detail: str
    metadata: dict = Field(default_factory=dict)
