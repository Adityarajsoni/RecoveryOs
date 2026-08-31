"""
API routes.

Endpoints (see frontend/src/api for the matching client calls):

  GET  /api/dataset/summary        -> headline counts before running
  POST /api/recovery/run           -> RUN RECOVERY AUTOPILOT (spec #3)
  GET  /api/recovery/transaction/{id} -> transaction detail page (#17)
  GET  /api/recovery/audit/{id}    -> full audit timeline for a txn
  GET  /api/recovery/playbook      -> discovered strategies (#12)
  POST /api/recovery/whatif        -> policy what-if simulator (#18)
  GET  /api/policy                 -> current merchant policy
  PUT  /api/policy                 -> update merchant policy
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
import os

from app.adapters.simulation_adapter import SimulationAdapter
from app.data.synthetic_generator import generate_batch
from app.engine.orchestrator import Orchestrator
from app.engine.playbook import discover_strategies
from app.models import ActionCost, Policy
from app.engine.llm import explain_decision, draft_communication, call_bedrock


router = APIRouter(prefix="/api")

@router.get("/test_bedrock")
def test_bedrock():
    return {"response": call_bedrock("Hello, are you working?")}

# --- in-memory demo state (swap for a DB in a real deployment) ----------
_DATASET = generate_batch(n=10_000, seed=42)
_POLICY = Policy()
_COSTS = ActionCost()
_LAST_ORCHESTRATOR: Orchestrator | None = None
_LAST_RESULT = None


@router.get("/dataset/summary")
def dataset_summary():
    at_risk = [e for e in _DATASET if e.status == "failed"]
    return {
        "total_events": len(_DATASET),
        "at_risk_events": len(at_risk),
        "revenue_at_risk": round(sum(e.amount for e in at_risk), 2),
    }


@router.post("/recovery/run")
def run_recovery_autopilot():
    global _LAST_ORCHESTRATOR, _LAST_RESULT
    adapter = SimulationAdapter(seed=7)
    orchestrator = Orchestrator(adapter, policy=_POLICY, costs=_COSTS)
    result = orchestrator.run_batch(_DATASET)
    _LAST_ORCHESTRATOR = orchestrator
    _LAST_RESULT = result

    recovery_rate = (
        result.recovered_count / result.intervention_count
        if result.intervention_count
        else 0.0
    )
    return {
        "events_processed": result.events_processed,
        "at_risk_count": result.at_risk_count,
        "eligible_count": result.eligible_count,
        "intervention_count": result.intervention_count,
        "recovered_count": result.recovered_count,
        "revenue_at_risk": round(result.revenue_at_risk, 2),
        "revenue_recovered": round(result.revenue_recovered, 2),
        "recovery_rate": round(recovery_rate, 4),
    }

@router.get("/recovery/last_result")
def get_last_result():
    if not _LAST_RESULT:
        return None
    recovery_rate = (
        _LAST_RESULT.recovered_count / _LAST_RESULT.intervention_count
        if _LAST_RESULT.intervention_count
        else 0.0
    )
    return {
        "events_processed": _LAST_RESULT.events_processed,
        "at_risk_count": _LAST_RESULT.at_risk_count,
        "eligible_count": _LAST_RESULT.eligible_count,
        "intervention_count": _LAST_RESULT.intervention_count,
        "recovered_count": _LAST_RESULT.recovered_count,
        "revenue_at_risk": round(_LAST_RESULT.revenue_at_risk, 2),
        "revenue_recovered": round(_LAST_RESULT.revenue_recovered, 2),
        "recovery_rate": round(recovery_rate, 4),
    }


@router.get("/recovery/transactions")
def get_transactions():
    if _LAST_RESULT is None:
        return []
    
    # We want to return a summary of intervened transactions
    # that includes the original event data + execution result
    results = []
    for tx_id, execution in _LAST_RESULT.outcomes.items():
        # Find the original event
        event = next((e for e in _DATASET if e.transaction_id == tx_id), None)
        if event:
            results.append({
                "transaction_id": tx_id,
                "customer_id": event.customer_id,
                "amount": event.amount,
                "status": "recovered" if execution.success else "failed",
                "action_taken": execution.action.value,
                "simulated": execution.simulated,
                "timestamp": event.timestamp.isoformat()
            })
    # sort by timestamp descending
    results.sort(key=lambda x: x["timestamp"], reverse=True)
    return results


@router.get("/recovery/transaction/{transaction_id}")
def get_transaction_detail(transaction_id: str):
    event = next((e for e in _DATASET if e.transaction_id == transaction_id), None)
    if not event:
        raise HTTPException(404, "Transaction not found.")
    
    execution = None
    if _LAST_RESULT and transaction_id in _LAST_RESULT.outcomes:
        execution = _LAST_RESULT.outcomes[transaction_id]
        
    return {
        "event": event.model_dump(),
        "execution": execution.model_dump() if execution else None
    }


@router.get("/recovery/audit/{transaction_id}")
def get_audit_trail(transaction_id: str):
    if _LAST_ORCHESTRATOR is None:
        raise HTTPException(400, "Run the recovery autopilot first.")
    events = _LAST_ORCHESTRATOR.ledger.for_transaction(transaction_id)
    if not events:
        raise HTTPException(404, "No audit events for this transaction.")
    return [e.model_dump() for e in events]


@router.get("/recovery/playbook")
def get_playbook():
    if _LAST_ORCHESTRATOR is None or _LAST_RESULT is None:
        raise HTTPException(400, "Run the recovery autopilot first.")
    at_risk_events = [e for e in _DATASET if e.status == "failed"]
    strategies = discover_strategies(at_risk_events, _LAST_RESULT.outcomes)
    return [s.__dict__ for s in strategies]


@router.get("/policy")
def get_policy():
    return _POLICY.model_dump()


@router.put("/policy")
def update_policy(policy: Policy):
    global _POLICY
    _POLICY = policy
    return _POLICY.model_dump()


@router.post("/recovery/whatif")
def whatif(policy: Policy):
    """Re-run the batch under a hypothetical policy without mutating the
    live policy, and report the delta (spec #18)."""
    adapter = SimulationAdapter(seed=7)
    orchestrator = Orchestrator(adapter, policy=policy, costs=_COSTS)
    result = orchestrator.run_batch(_DATASET)

    baseline_recovered = _LAST_RESULT.revenue_recovered if _LAST_RESULT else 0.0
    return {
        "hypothetical_revenue_recovered": round(result.revenue_recovered, 2),
        "baseline_revenue_recovered": round(baseline_recovered, 2),
        "delta": round(result.revenue_recovered - baseline_recovered, 2),
        "intervention_count": result.intervention_count,
    }


@router.post("/recovery/transaction/{transaction_id}/explain")
def explain_transaction(transaction_id: str):
    if _LAST_ORCHESTRATOR is None:
        raise HTTPException(400, "Run the recovery autopilot first.")
    
    event = next((e for e in _DATASET if e.transaction_id == transaction_id), None)
    if not event:
        raise HTTPException(404, "Transaction not found.")
        
    audit = _LAST_ORCHESTRATOR.ledger.for_transaction(transaction_id)
    explanation = explain_decision(event.model_dump(), [a.model_dump() for a in audit])
    return {"explanation": explanation}

@router.post("/recovery/transaction/{transaction_id}/draft_email")
def draft_email_route(transaction_id: str):
    if _LAST_ORCHESTRATOR is None:
        raise HTTPException(400, "Run the recovery autopilot first.")
        
    event = next((e for e in _DATASET if e.transaction_id == transaction_id), None)
    if not event:
        raise HTTPException(404, "Transaction not found.")
        
    execution = _LAST_RESULT.outcomes.get(transaction_id) if _LAST_RESULT else None
    action = execution.action.value if execution else "Unknown"
    
    draft = draft_communication(event.model_dump(), action)
    return {"draft": draft}
