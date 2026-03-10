import json
from google.adk.agents import Agent

from .base_runner import run_agent_json

INSTRUCTION = """You are the HireForce Code Challenger. Generate exactly ONE very easy coding problem for an interview (max 5 minutes).

Return **valid JSON only** (no markdown, no extra text):

{
    "title": "short title",
    "description": "clear problem description for the candidate",
    "expected_behavior": "what the function should do",
    "starter_code_python": "def fn_name(arg1, arg2):\\n    pass",
    "starter_code_javascript": "function fnName(arg1, arg2) { }",
    "starter_code_java": "public int fnName(int a, int b) { return 0; }",
    "starter_code_cpp": "int fnName(int a, int b) { return 0; }",
    "difficulty": "easy",
    "example_input_output": "e.g. (2, 3) -> 5"
}

Rules:
- Problem must be solvable in under 5 minutes (e.g. sum two numbers, reverse string, is even).
- Provide starter_code for python, javascript, java, cpp.
- Return ONLY the JSON object."""

agent = Agent(
    name="code_challenger",
    model="gemini-2.0-flash",
    description="Generates one easy coding question",
    instruction=INSTRUCTION,
)


async def generate_coding_question(language: str = "python") -> dict:
    """Generate one easy coding question. Returns coding_question dict."""
    prompt = f"Generate one very easy coding problem. Prefer a problem that fits {language} naturally. Return only the JSON."
    try:
        return await run_agent_json(agent, prompt)
    except json.JSONDecodeError:
        return {
            "title": "Sum of Two Numbers",
            "description": "Write a function that returns the sum of two numbers.",
            "expected_behavior": "Return a + b.",
            "starter_code_python": "def sum_two(a, b):\n    pass",
            "starter_code_javascript": "function sumTwo(a, b) { }",
            "starter_code_java": "public int sumTwo(int a, int b) { return 0; }",
            "starter_code_cpp": "int sumTwo(int a, int b) { return 0; }",
            "difficulty": "easy",
            "example_input_output": "(2, 3) -> 5",
        }
