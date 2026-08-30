"""
Recovery Playbook
==================
Offline learning/evaluation loop (explicitly labeled as such — see spec
section 12) that mines discovered strategies from a batch of processed
outcomes: for a given segment definition, what recovery rate did the
system actually observe?

This is NOT online learning. It runs after a batch completes and
produces human-readable "DISCOVERED STRATEGY" cards for the dashboard.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from app.models import ActionType, ExecutionResult, PaymentEvent


@dataclass
class Segment:
    label: str
    predicate: str  # human-readable description of the segment rule
    matches: Callable[[PaymentEvent], bool]


@dataclass
class DiscoveredStrategy:
    id: int
    when: str
    recommended_action: str
    observed_recovery_rate: float
    sample_size: int


# Segment definitions mirroring the spec's worked examples. Add more here
# as the dataset grows; each is independently evaluated against outcomes.
SEGMENTS: list[Segment] = [
    Segment(
        label="temp_failure_good_history_low_amount",
        predicate="Temporary payment failure + 5+ previous successes + amount < ₹5,000",
        matches=lambda e: (
            e.failure_reason is not None
            and e.failure_reason.value == "temporary_bank_failure"
            and e.previous_success_count >= 5
            and e.amount < 5000
        ),
    ),
    Segment(
        label="repeat_failures_low_activity",
        predicate="3+ previous failures + low customer activity (30+ days inactive)",
        matches=lambda e: (e.previous_failure_count >= 3 and e.last_activity_days_ago > 30),
    ),
]


def discover_strategies(
    events: list[PaymentEvent], outcomes: dict[str, ExecutionResult]
) -> list[DiscoveredStrategy]:
    strategies: list[DiscoveredStrategy] = []
    for i, segment in enumerate(SEGMENTS, start=1):
        matched = [e for e in events if segment.matches(e)]
        if not matched:
            continue
        recovered = sum(
            1
            for e in matched
            if e.transaction_id in outcomes and outcomes[e.transaction_id].success
        )
        rate = recovered / len(matched)

        # Recommend whichever action was most common among successful
        # outcomes in this segment.
        action_counts: dict[ActionType, int] = defaultdict(int)
        for e in matched:
            result = outcomes.get(e.transaction_id)
            if result and result.success:
                action_counts[result.action] += 1
        recommended = (
            max(action_counts, key=action_counts.get).value.replace("_", " ").title()
            if action_counts
            else "Stop retries / escalate"
        )

        strategies.append(
            DiscoveredStrategy(
                id=i,
                when=segment.predicate,
                recommended_action=recommended,
                observed_recovery_rate=round(rate, 4),
                sample_size=len(matched),
            )
        )
    return strategies
