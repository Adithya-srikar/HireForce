"""Shared helper to run an ADK agent with a single prompt and return final text."""
import json
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


def _clean_json_response(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


async def run_agent_json(
    agent: Agent,
    prompt: str,
    session_service: InMemorySessionService | None = None,
) -> dict:
    """Run agent with prompt, parse final response as JSON. Returns dict or raises."""
    if session_service is None:
        session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="hireforce", session_service=session_service)
    session = await session_service.create_session(app_name="hireforce", user_id="system")
    content = types.Content(role="user", parts=[types.Part(text=prompt)])
    final_response = ""
    async for event in runner.run_async(
        user_id="system", session_id=session.id, new_message=content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_response += part.text
    cleaned = _clean_json_response(final_response)
    return json.loads(cleaned)


async def run_agent_text(
    agent: Agent,
    prompt: str,
    session_service: InMemorySessionService | None = None,
) -> str:
    """Run agent with prompt, return final text."""
    if session_service is None:
        session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="hireforce", session_service=session_service)
    session = await session_service.create_session(app_name="hireforce", user_id="system")
    content = types.Content(role="user", parts=[types.Part(text=prompt)])
    final_response = ""
    async for event in runner.run_async(
        user_id="system", session_id=session.id, new_message=content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_response += part.text
    return final_response.strip()
