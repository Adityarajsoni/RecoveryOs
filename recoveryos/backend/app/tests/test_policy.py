import pytest
from app.models import ActionType, ExpectedRecovery, RecoveryDecision, Policy, AuthorizationBasis

from app.engine.policy_engine import check

def test_policy_budget_enforcement():
    decision = RecoveryDecision(
        transaction_id="txn_123",
        chosen_action=ActionType.NOTIFICATION,
        chosen_expected_net=50.0,
        alternatives=[],
        authorization_basis=AuthorizationBasis.NONE,
        reasoning="Test",
        factors=[]
    )
    
    # Policy says max budget is 100, we spent 90 so far, action costs 20 -> should reject
    policy = Policy(max_recovery_budget=100.0)
    
    result = check(
        decision, 
        policy=policy, 
        retry_count_so_far=0, 
        budget_spent_so_far=90.0, 
        contact_attempts_so_far=0, 
        action_cost=20.0, 
        transaction_amount=100.0
    )
    
    assert result.final_action == ActionType.STOP
    assert any("budget" in c.lower() for c in result.constraints_applied)

def test_policy_human_approval_limit():
    decision = RecoveryDecision(
        transaction_id="txn_123",
        chosen_action=ActionType.RETRY,
        chosen_expected_net=50.0,
        alternatives=[],
        authorization_basis=AuthorizationBasis.EXISTING_MANDATE,
        reasoning="Test",
        factors=[]
    )
    
    # Transaction amount is 30,000. Approval limit is 25,000.
    policy = Policy(human_approval_above=25000.0)
    
    result = check(
        decision, 
        policy=policy, 
        retry_count_so_far=0, 
        budget_spent_so_far=0.0, 
        contact_attempts_so_far=0, 
        action_cost=0.0, 
        transaction_amount=30000.0
    )
    
    # It should escalate instead of retry
    assert result.final_action == ActionType.ESCALATE
    assert any("human-approval" in c.lower() for c in result.constraints_applied)

def test_policy_max_retries():
    decision = RecoveryDecision(
        transaction_id="txn_123",
        chosen_action=ActionType.RETRY,
        chosen_expected_net=50.0,
        alternatives=[],
        authorization_basis=AuthorizationBasis.EXISTING_MANDATE,
        reasoning="Test",
        factors=[]
    )
    
    policy = Policy(max_retries=2)
    
    # Already retried 2 times
    result = check(
        decision, 
        policy=policy, 
        retry_count_so_far=2, 
        budget_spent_so_far=0.0, 
        contact_attempts_so_far=0, 
        action_cost=0.0, 
        transaction_amount=100.0
    )
    
    assert result.final_action == ActionType.STOP
    assert any("retries" in c.lower() for c in result.constraints_applied)

def test_policy_no_arbitrary_debit():
    decision = RecoveryDecision(
        transaction_id="txn_123",
        chosen_action=ActionType.RETRY,
        chosen_expected_net=50.0,
        alternatives=[],
        authorization_basis=AuthorizationBasis.NONE, # NO MANDATE!
        reasoning="Test",
        factors=[]
    )
    
    policy = Policy()
    
    result = check(
        decision, 
        policy=policy, 
        retry_count_so_far=0, 
        budget_spent_so_far=0.0, 
        contact_attempts_so_far=0, 
        action_cost=0.0, 
        transaction_amount=100.0
    )
    
    assert result.final_action == ActionType.PAYMENT_LINK
    assert any("authorization" in c.lower() for c in result.constraints_applied)

