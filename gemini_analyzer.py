import os
import json
from google import genai
from google.genai import types
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
IMPORTANCE_PROMPT = os.getenv("IMPORTANCE_PROMPT", "Categorize email into High, Mid, Low, or Spam. Extract deadline and summary. Return JSON with keys: priority, deadline, summary.")

client = genai.Client(api_key=api_key) if api_key else None

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "priority": {"type": "string", "enum": ["High", "Mid", "Low", "Spam"]},
        "deadline": {"type": "string"},
        "summary": {"type": "string"}
    },
    "required": ["priority", "deadline", "summary"]
}

@retry(
    wait=wait_exponential(multiplier=5, min=5, max=60),
    stop=stop_after_attempt(5),
    reraise=True
)
def analyze_email(subject: str, sender: str, date: str, body: str) -> dict:
    """
    Analyzes an email using Gemini 1.5 Flash.
    Returns a dictionary with 'priority', 'deadline', and 'summary'.
    """
    if not client:
        print("WARNING: GEMINI_API_KEY not set.")
        return {"priority": "Low", "deadline": "", "summary": "No API key configured."}

    content = f"Sender: {sender}\nDate: {date}\nSubject: {subject}\n\nBody:\n{body[:15000]}"

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=content,
        config=types.GenerateContentConfig(
            system_instruction=IMPORTANCE_PROMPT,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
        )
    )

    try:
        return json.loads(response.text)
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error parsing Gemini response: {e} — raw: {response.text}")
        return {"priority": "Spam", "deadline": "", "summary": "Failed to parse AI response."}
