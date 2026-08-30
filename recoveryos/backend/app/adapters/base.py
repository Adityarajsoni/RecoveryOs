"""
Common interface both the real Razorpay adapter and the simulation
adapter implement, so the Action Executor never has to know which one
it's talking to.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import ActionType, ExecutionResult, PaymentEvent


class RecoveryActionAdapter(ABC):
    simulated: bool = True

    @abstractmethod
    def execute(self, event: PaymentEvent, action: ActionType) -> ExecutionResult:
        """Perform (or simulate) the given action for this transaction and
        return the outcome. Must never raise for expected business
        failures (e.g. retry declined) — encode that in ExecutionResult.
        """
        raise NotImplementedError
