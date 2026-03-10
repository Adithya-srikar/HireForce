import json
from google.adk.agents import Agent

from .base_runner import run_agent_json

INSTRUCTION = """You are the HireForce Question Generator. Given a job description and the candidate's prescreen analysis (from LinkedIn, GitHub, LeetCode, resume), generate a set of interview questions.

Return **valid JSON only** (no markdown fences, no extra text) with this schema:

{
    "questions": [
        {
            "question": "exact question text to ask",
            "context": "why this question given the candidate profile",
            "order": 1
        }
    ],
    "coding_question": {
        "title": "short title e.g. Sum of Two Numbers",
        "description": "problem description for the candidate",
        "expected_behavior": "what the code should do",
        "starter_code_python": "def sum_two(a, b):\\n    pass",
        "starter_code_javascript": "function sumTwo(a, b) { }",
        "difficulty": "easy"
    }
}

Rules:
- Generate 5–7 behavioral/technical questions tailored to the job and candidate profile.
- Reference their repos, experience, or LeetCode where relevant in "context".
- Coding question must be very easy (e.g. sum two numbers, reverse string), one function.
- order should be 1, 2, 3, ...
- Return ONLY the JSON object."""

agent = Agent(
    name="question_generator",
    model="gemini-2.0-flash",
    description="Generates interview questions from job + prescreen",
    instruction=INSTRUCTION,
)


async def generate_questions(
    job_description: str,
    prescreen_analysis: dict,
    prescreen_platform_summary: str = "",
) -> dict:
    """Generate questions and coding question. Returns dict with questions and coding_question."""
    prompt_parts = [
        "## Job Description\n",
        job_description[:6000],
        "\n\n## Candidate Prescreen Analysis (JSON)\n",
        json.dumps(prescreen_analysis, indent=2, default=str)[:8000],
    ]
    if prescreen_platform_summary:
        prompt_parts.append("\n\n## Platform data summary (optional)\n")
        prompt_parts.append(prescreen_platform_summary[:2000])
    prompt_parts.append("\n\nGenerate the interview questions and the one easy coding question as JSON.")
    prompt = "".join(prompt_parts)

    try:
        return await run_agent_json(agent, prompt)
    except json.JSONDecodeError:
        return _fallback()


def _fallback() -> dict:
    return {
        "questions": [
            {"question": "Tell me about a recent technical project.", "context": "General.", "order": 1},
            {"question": "How do you approach debugging?", "context": "Problem-solving.", "order": 2},
            {"question": "Describe working with a team on a tight deadline.", "context": "Collaboration.", "order": 3},
        ],
        "coding_question": {
            "title": "Sum of Two Numbers",
            "description": "Write a function that returns the sum of two numbers.",
            "expected_behavior": "Return a + b.",
            "starter_code_python": "def sum_two(a, b):\n    pass",
            "starter_code_javascript": "function sumTwo(a, b) { }",
            "difficulty": "easy",
        },
    }
