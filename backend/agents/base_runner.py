"""Shared helper to run an agent with google-genai and return final text."""
import json
import os
from typing import Optional
import google.genai as genai


def _clean_json_response(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


async def run_agent_json(
    agent: dict,
    prompt: str,
    session_service: Optional[object] = None,
) -> dict:
    """Run agent with prompt, parse final response as JSON. Returns dict or raises."""
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    final_response = response.text
    cleaned = _clean_json_response(final_response)
    return json.loads(cleaned)


async def run_agent_text(
    agent: dict,
    prompt: str,
    session_service: Optional[object] = None,
) -> str:
    """Run agent with prompt, return final text."""
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text.strip()
