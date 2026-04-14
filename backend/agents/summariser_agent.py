import json

from .base_runner import run_agent_json

INSTRUCTION = """You are the HireForce Summariser. You evaluate the full interview: transcript, prescreen, and code evaluation.

Return **valid JSON only** (no markdown, no extra text):

{
    "summary": "2-4 sentence overall assessment of the interview",
    "technical_depth": "paragraph on technical depth shown in answers",
    "communication": "paragraph on clarity and communication",
    "scores": {
        "technical": 0-10,
        "communication": 0-10,
        "problem_solving": 0-10,
        "code_quality": 0-10,
        "overall": 0-10
    },
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"]
}

Rules:
- Be specific: reference actual answers or code where relevant.
- code_quality can be from code_evaluation if available.
- overall should reflect fit for a technical role.
- Return ONLY the JSON object."""

agent = {
    "name": "summariser",
    "model": "gemini-2.0-flash",
    "description": "Summarises full interview for report",
    "instruction": INSTRUCTION,
}


async def summarise_interview(
    transcript: list[dict],
    prescreen_summary: str,
    code_evaluation: dict | None,
) -> dict:
    """Produce summary dict for report generator."""
    transcript_str = "\n".join(
        f"{e.get('role', '')}: {e.get('text', '')}" for e in transcript
    )
    code_str = json.dumps(code_evaluation, indent=2) if code_evaluation else "No code submitted."

    prompt = f"""## Prescreen summary
{prescreen_summary[:2500]}

## Interview transcript
{transcript_str[:6000]}

## Code evaluation (if any)
{code_str}

Produce the summary JSON."""

    try:
        return await run_agent_json(agent, prompt)
    except Exception:
        return {
            "summary": "Interview completed.",
            "technical_depth": "",
            "communication": "",
            "scores": {
                "technical": 5,
                "communication": 5,
                "problem_solving": 5,
                "code_quality": 5,
                "overall": 5,
            },
            "strengths": [],
            "weaknesses": [],
        }
