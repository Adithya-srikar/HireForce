import json

from .base_runner import run_agent_json

INSTRUCTION = """You are the HireForce Report Generator. Given the summariser's evaluation, produce a final hiring verdict.

Return **valid JSON only** (no markdown, no extra text):

{
    "verdict": "fit" or "unfit",
    "report_text": "2-4 paragraph report for the hiring team: overall impression, key strengths, concerns, recommendation. Professional tone."
}

Rules:
- verdict = "fit" if overall score is >= 6 and no major red flags. "unfit" otherwise.
- report_text should be readable by HR/hiring manager.
- Return ONLY the JSON object."""

agent = {
    "name": "report_generator",
    "model": "gemini-2.0-flash",
    "description": "Produces fit/unfit and report text",
    "instruction": INSTRUCTION,
}


async def generate_report(summary: dict) -> dict:
    """Produce verdict and report_text from summariser output."""
    prompt = f"""## Summariser output
{json.dumps(summary, indent=2)}

Produce the final verdict and report JSON."""
    try:
        return await run_agent_json(agent, prompt)
    except Exception:
        return {
            "verdict": "unfit",
            "report_text": "Report could not be generated automatically.",
        }
