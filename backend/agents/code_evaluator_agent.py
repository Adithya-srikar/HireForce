from .base_runner import run_agent_json

INSTRUCTION = """You are the HireForce Code Evaluator. You evaluate candidate code against a problem description.

You do NOT execute code. You reason about correctness and quality.

Return **valid JSON only** (no markdown, no extra text):

{
    "passed": true or false,
    "feedback": "2-3 sentence feedback",
    "correctness_score": 0-10,
    "reasoning": "brief explanation of why it passes or fails"
}

Rules:
- passed = true only if the code logically solves the problem (correct logic, handles basic cases).
- Consider syntax only for the stated language; assume it runs.
- Be fair: if the solution is correct but verbose, still pass.
- Return ONLY the JSON object."""

agent = {
    "name": "code_evaluator",
    "model": "gemini-2.0-flash",
    "description": "Evaluates candidate code against problem",
    "instruction": INSTRUCTION,
}


async def evaluate_code(
    code: str,
    language: str,
    problem_description: str,
    expected_behavior: str,
) -> dict:
    """Evaluate code. Returns dict with passed, feedback, correctness_score, reasoning."""
    prompt = f"""## Problem
{problem_description}

## Expected behavior
{expected_behavior}

## Language
{language}

## Candidate code
```
{code}
```

Evaluate whether this code solves the problem. Return only the JSON."""
    try:
        return await run_agent_json(agent, prompt)
    except Exception:
        return {
            "passed": False,
            "feedback": "Evaluation could not be completed.",
            "correctness_score": 0,
            "reasoning": "Agent error",
        }
