"""
Audit Ledger via Amazon DynamoDB
================================
Append-only log for financial compliance. Every stage of the pipeline writes 
an AuditEvent here so the full timeline can be reconstructed.

If AWS DynamoDB is configured via environment variables, events are 
persisted to AWS. Otherwise, it falls back to in-memory (useful for local testing).
"""

from __future__ import annotations

import os
import boto3
from datetime import datetime, timezone
import uuid

from app.models import AuditEvent

class AuditLedger:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self.table_name = os.environ.get("DYNAMODB_TABLE_NAME")
        
        if self.table_name:
            region = os.environ.get("AWS_REGION", "us-east-1")
            self.dynamodb = boto3.resource("dynamodb", region_name=region)
            self.table = self.dynamodb.Table(self.table_name)
        else:
            self.dynamodb = None
            self.table = None

    def log(self, transaction_id: str, event_type: str, detail: str, **metadata) -> None:
        event = AuditEvent(
            transaction_id=transaction_id,
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            detail=detail,
            metadata=metadata,
        )
        self._events.append(event)
        
        # --- DYNAMODB PERSISTENCE ---
        if self.table:
            try:
                # Single Table Design: PK=TransactionId, SK=Audit#Timestamp#UUID
                item = {
                    "PK": f"TXN#{transaction_id}",
                    "SK": f"AUDIT#{event.timestamp.isoformat()}#{str(uuid.uuid4())[:8]}",
                    "transaction_id": transaction_id,
                    "event_type": event_type,
                    "detail": detail,
                    "timestamp": event.timestamp.isoformat(),
                }
                # Add optional metadata without breaking schema
                for k, v in metadata.items():
                    if v is not None:
                        item[f"meta_{k}"] = str(v)
                        
                self.table.put_item(Item=item)
            except Exception as e:
                print(f"DynamoDB Log Failed: {e}")

    def for_transaction(self, transaction_id: str) -> list[AuditEvent]:
        # If DynamoDB is active, query it. Otherwise use in-memory.
        if self.table:
            try:
                from boto3.dynamodb.conditions import Key
                response = self.table.query(
                    KeyConditionExpression=Key('PK').eq(f"TXN#{transaction_id}") & Key('SK').begins_with("AUDIT#")
                )
                db_events = []
                for item in response.get("Items", []):
                    # We map DDB items back into AuditEvent models
                    db_events.append(
                        AuditEvent(
                            transaction_id=item["transaction_id"],
                            timestamp=datetime.fromisoformat(item["timestamp"]),
                            event_type=item["event_type"],
                            detail=item["detail"],
                            metadata={k.replace("meta_", ""): v for k, v in item.items() if k.startswith("meta_")}
                        )
                    )
                # Sort descending by timestamp
                db_events.sort(key=lambda x: x.timestamp, reverse=True)
                return db_events
            except Exception as e:
                print(f"DynamoDB Query Failed: {e}. Falling back to memory.")
                
        # In-memory fallback
        return [e for e in self._events if e.transaction_id == transaction_id]

    def all_events(self) -> list[AuditEvent]:
        return list(self._events)
