import os
import requests

def call_gemini(prompt: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "[Mock AI Reply] Please set GEMINI_API_KEY in the environment to use real AI generation.\n\n" + prompt[:100] + "..."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"[AI Generation Failed] {str(e)}"

def explain_decision(event_data: dict, audit_trail: list) -> str:
    prompt = f"""
    You are an AI Revenue Recovery assistant explaining a decision to a human support agent.
    
    Here is the payment event data:
    {event_data}
    
    Here is the timeline of what the AI engine considered and decided:
    {audit_trail}
    
    Write a short, professional, and clear 3-bullet explanation of WHY this specific action was taken. 
    Do not use generic fluff. Point directly to the policy rules, expected recovery value, or customer history.
    """
    return call_gemini(prompt)

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
    """
    return call_gemini(prompt)

