"""
Policy Engine via Amazon Verified Permissions (Cedar)
===================================================
Replaces the old Python deterministic rules with an AWS-native 
Cedar policy evaluation. 

The AI proposes an action. AVP checks if the "AutonomousAgent" 
is permitted to take that action on the "PaymentEvent" given the context.
"""

from __future__ import annotations

import os
import boto3
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
    
    proposed_action = decision.chosen_action
    constraints: list[str] = []
    
    # Check if we should route to AWS Verified Permissions (Cedar)
    policy_store_id = os.environ.get("AVP_POLICY_STORE_ID")
    
    if policy_store_id:
        # --- AWS VERIFIED PERMISSIONS (CEDAR) FLOW ---
        region = os.environ.get("AWS_REGION", "us-east-1")
        avp_client = boto3.client("verifiedpermissions", region_name=region)
        
        # Build Cedar Context
        context_map = {
            "transaction_amount": {"long": int(transaction_amount)},
            "retry_count": {"long": retry_count_so_far},
            "contact_attempts": {"long": contact_attempts_so_far},
            "budget_spent": {"long": int(budget_spent_so_far)},
            "has_mandate": {"boolean": decision.authorization_basis != AuthorizationBasis.NONE},
            "max_retries": {"long": policy.max_retries},
            "max_contacts": {"long": policy.max_customer_contact_attempts},
            "human_approval_threshold": {"long": int(policy.human_approval_above)},
        }
        
        try:
            # Cedar Action string (e.g. Action::"RETRY")
            cedar_action = f'Action::"{proposed_action.value}"'
            
            response = avp_client.is_authorized(
                policyStoreId=policy_store_id,
                principal={"entityType": "Role", "entityId": "AutonomousAgent"},
                action={"actionType": "Action", "actionId": proposed_action.value},
                resource={"entityType": "Payment", "entityId": decision.transaction_id},
                context={"contextMap": context_map}
            )
            
            decision_result = response.get("decision") # 'ALLOW' or 'DENY'
            
            if decision_result == "ALLOW":
                return PolicyCheckResult(
                    allowed=True,
                    final_action=proposed_action,
                    requires_human_approval=False,
                    constraints_applied=["Amazon Verified Permissions: ALLOW"]
                )
            else:
                # If Cedar DENIES the action, we escalate to human review
                return PolicyCheckResult(
                    allowed=True, # We allow the escalation
                    final_action=ActionType.ESCALATE,
                    requires_human_approval=True,
                    constraints_applied=[f"Amazon Verified Permissions: DENY (Fell back to ESCALATE)"]
                )
                
        except Exception as e:
            constraints.append(f"AVP Request Failed: {str(e)}")
            # Fall through to local logic below if AWS fails
            print(f"AVP Error: {e}. Falling back to local logic.")
            
    # --- FALLBACK / LOCAL MOCK FLOW ---
    # This keeps your app working even before you setup AVP in AWS Console
    action = proposed_action

    if action in (ActionType.RETRY, ActionType.RETRY_LATER) and (decision.authorization_basis == AuthorizationBasis.NONE):
        constraints.append("No reusable authorization — direct debit blocked")
        action = ActionType.PAYMENT_LINK

    if action in (ActionType.RETRY, ActionType.RETRY_LATER) and (retry_count_so_far >= policy.max_retries):
        constraints.append(f"Retry limit reached (max_retries={policy.max_retries})")
        action = ActionType.STOP

    if budget_spent_so_far + action_cost > policy.max_recovery_budget:
        constraints.append(f"Recovery budget exhausted")
        action = ActionType.STOP

    if action == ActionType.PAYMENT_LINK and not policy.auto_generate_payment_links:
        constraints.append("Auto payment-link generation disabled")
        action = ActionType.ESCALATE
        
    if action == ActionType.NOTIFICATION and not policy.auto_send_notifications:
        constraints.append("Auto customer notifications disabled")
        action = ActionType.ESCALATE

    if action == ActionType.NOTIFICATION and (contact_attempts_so_far >= policy.max_customer_contact_attempts):
        constraints.append(f"Customer contact limit reached")
        action = ActionType.STOP

    requires_human_approval = transaction_amount > policy.human_approval_above
    if requires_human_approval and action != ActionType.STOP:
        constraints.append(f"Amount exceeds human-approval threshold")
        action = ActionType.ESCALATE

    return PolicyCheckResult(
        allowed=action != ActionType.STOP,
        final_action=action,
        requires_human_approval=requires_human_approval,
        constraints_applied=constraints,
    )
