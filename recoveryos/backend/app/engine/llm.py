import os
import json
import boto3
from dotenv import load_dotenv

# Load .env forcefully
load_dotenv(override=True)

def call_bedrock(prompt: str) -> str:
    # We will use Claude 3 Haiku for blazing fast responses
    # Make sure your AWS credentials are set in your environment
    region = os.environ.get("AWS_REGION", "us-east-1")
    
    try:
        # We wrap in try/except so the app doesn't crash if AWS credentials aren't set yet
        bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })

        model_id = "anthropic.claude-3-haiku-20240307-v1:0"

        response = bedrock_runtime.invoke_model(
            body=body,
            modelId=model_id,
            accept="application/json",
            contentType="application/json"
        )
        
        response_body = json.loads(response.get("body").read())
        return response_body["content"][0]["text"]
        
    except Exception as e:
        return f"[AWS Bedrock Request Failed] Error: {str(e)}\n\nMake sure your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set, and Claude 3 Haiku model access is requested in Amazon Bedrock console."


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
