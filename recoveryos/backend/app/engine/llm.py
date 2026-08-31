import os
import json
import boto3
from dotenv import load_dotenv

# Load .env forcefully
load_dotenv(override=True)

def call_bedrock(prompt: str) -> str:
    # We are switching to Amazon's native Nova model to bypass AWS Marketplace limits
    region = os.environ.get("AWS_REGION", "us-east-1")
    
    try:
        bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)
        
        # Amazon Nova Micro is a blazing fast 1st-party model
        model_id = "amazon.nova-micro-v1:0"

        response = bedrock_runtime.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ]
        )
        
        return response["output"]["message"]["content"][0]["text"]
        
    except Exception as e:
        return f"[AWS Bedrock Request Failed] Error: {str(e)}"


def explain_decision(event_data: dict, audit_trail: list) -> str:
    prompt = f"""
    You are an AI Revenue Recovery assistant explaining a decision to a human support agent.
    
    Here is the payment event data:
    {event_data}
    
    Here is the timeline of what the AI engine considered and decided:
    {audit_trail}
    
    Write a short, professional, and clear 3-bullet explanation of WHY this specific action was taken. 
    Point directly to the policy rules, expected recovery value, or customer history.
    CRITICAL RULE: DO NOT use any Markdown formatting (no asterisks, no bolding). Output pure plain text. Use standard dashes (-) for bullets.
    """
    return call_bedrock(prompt)

def draft_communication(event_data: dict, action_taken: str) -> str:
    prompt = f"""
    You are a professional customer support AI for a modern fintech company.
    A payment has failed for a customer, and we decided to take this action: {action_taken}
    
    Customer Data:
    {event_data}
    
    Write a short, polite, and actionable email draft to the customer. 
    If the action was PAYMENT_LINK, ask them to click the link to update their payment.
    If it was RETRY_LATER, just inform them we will try again soon and no action is needed yet.
    Keep it under 3-4 sentences. Include placeholders like [Link] if needed.
    
    CRITICAL RULE: DO NOT include a "Subject:" line (the UI already handles the subject). DO NOT use any Markdown formatting (no asterisks, no bolding). ONLY output the plain text body of the email starting with "Dear Customer,".
    """
    return call_bedrock(prompt)
