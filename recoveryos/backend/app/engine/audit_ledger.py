"""
Audit Ledger
============
Append-only in-memory log for the hackathon (swap for a real DB/table
later). Every stage of the pipeline writes an AuditEvent here so the
full timeline in spec section 14 can be reconstructed per transaction.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.models import AuditEvent


class AuditLedger:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def log(self, transaction_id: str, event_type: str, detail: str, **metadata) -> None:
        self._events.append(
            AuditEvent(
                transaction_id=transaction_id,
                timestamp=datetime.now(timezone.utc),
                event_type=event_type,
                detail=detail,
                metadata=metadata,
            )
        )

    def for_transaction(self, transaction_id: str) -> list[AuditEvent]:
        return [e for e in self._events if e.transaction_id == transaction_id]

    def all_events(self) -> list[AuditEvent]:
        return list(self._events)
