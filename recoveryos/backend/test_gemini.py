import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load from .env
load_dotenv()

key = os.environ.get("GEMINI_API_KEY")
print(f"API Key loaded from .env: {key}")

if not key:
    print("ERROR: GEMINI_API_KEY is completely empty in .env!")
    exit(1)

print("Attempting to contact Gemini API...")
try:
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-3.6-flash')
    response = model.generate_content("Hello! Say 'Gemini is working!'")
    print("\n--- RESPONSE FROM GEMINI ---")
    print(response.text)
    print("----------------------------\n")
    print("SUCCESS!")
except Exception as e:
    print(f"\n[FAILED] {str(e)}")
