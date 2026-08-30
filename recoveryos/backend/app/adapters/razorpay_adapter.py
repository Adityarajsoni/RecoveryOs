from __future__ import annotations

import os

from app.adapters.base import RecoveryActionAdapter
from app.models import ActionType, AuthorizationBasis, ExecutionResult, PaymentEvent

class RazorpayAdapter(RecoveryActionAdapter):
    simulated = False

    def __init__(self, key_id: str | None = None, key_secret: str | None = None):
        self.key_id = key_id or os.environ.get("RAZORPAY_KEY_ID")
        self.key_secret = key_secret or os.environ.get("RAZORPAY_KEY_SECRET")
        self._client = None
        if self.key_id and self.key_secret:
            try:
                import razorpay  # type: ignore

                self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
            except ImportError:
                self._client = None  # razorpay SDK not installed yet

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def execute(self, event: PaymentEvent, action: ActionType) -> ExecutionResult:
        if not self.is_configured:
            raise RuntimeError(
                "RazorpayAdapter is not configured (missing keys or SDK). "
                "Use SimulationAdapter instead."
            )

        if action == ActionType.PAYMENT_LINK:
            return self._create_payment_link(event)

        if action in (ActionType.RETRY, ActionType.RETRY_LATER):
            if event.mandate_available is False:
                raise ValueError(
                    "RETRY requested without an authorization basis — this must never "
                    "reach the adapter. Check policy_engine/decision_engine wiring."
                )
            return self._retry_payment(event)

        raise ValueError(f"RazorpayAdapter does not support action: {action}")

    # -- individual action implementations -------------------------------

    def _create_payment_link(self, event: PaymentEvent) -> ExecutionResult:
        payload = {
            "amount": int(event.amount * 100),  # paise
            "currency": "INR",
            "accept_partial": False,
            "description": f"Payment recovery for transaction {event.transaction_id}",
            "reference_id": event.transaction_id,
            "customer": {
                "name": f"Customer {event.customer_id}",
                "email": f"customer_{event.customer_id}@example.com",
                "contact": "+919999999999"
            },
            "notify": {"sms": True, "email": True},
            "reminder_enable": True
        }
        
        try:
            link = self._client.payment_link.create(payload)  # type: ignore[union-attr]
            return ExecutionResult(
                transaction_id=event.transaction_id,
                action=ActionType.PAYMENT_LINK,
                simulated=False,
                success=True,
                amount_recovered=0.0,
                razorpay_reference=link.get("id"),
                detail=f"Payment link created: {link.get('short_url', '')}",
            )
        except Exception as e:
            return ExecutionResult(
                transaction_id=event.transaction_id,
                action=ActionType.PAYMENT_LINK,
                simulated=False,
                success=False,
                amount_recovered=0.0,
                detail=f"Razorpay API Error: {str(e)}",
            )

    def _retry_payment(self, event: PaymentEvent) -> ExecutionResult:
        # Implementing the recurring payment flow assuming a saved token or mandate.
        # This assumes we have a stored 'token_id' (stubbed here as event.customer_id).
        # In a real app, you fetch the token_id from your DB.
        payload = {
            "amount": int(event.amount * 100),
            "currency": "INR",
            "customer_id": f"cust_{event.customer_id}",
            "token": "token_stub_12345", # Stubbed
            "receipt": event.transaction_id,
            "recurring": "1",
            "description": f"Auto-retry for failed payment {event.transaction_id}"
        }
        
        try:
            # We create a payment. This requires the customer and token to be valid in Razorpay.
            # (If it fails in test mode without valid token, we catch the exception).
            payment = self._client.payment.create(payload) # type: ignore[union-attr]
            
            # Auto-capture the payment since we are doing a direct charge
            payment_id = payment.get("id")
            if payment_id:
                self._client.payment.capture(payment_id, payload["amount"])
            
            return ExecutionResult(
                transaction_id=event.transaction_id,
                action=ActionType.RETRY,
                simulated=False,
                success=True,
                amount_recovered=event.amount,
                razorpay_reference=payment_id,
                detail="Payment retry succeeded via recurring token."
            )
        except Exception as e:
            return ExecutionResult(
                transaction_id=event.transaction_id,
                action=ActionType.RETRY,
                simulated=False,
                success=False,
                amount_recovered=0.0,
                detail=f"Razorpay Retry Error: {str(e)}"
            )

