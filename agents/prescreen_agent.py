import json
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

AGENT_INSTRUCTION = """You are HireForce PreScreen Agent — an expert technical recruiter AI.

You receive structured candidate data collected from GitHub, LeetCode, and LinkedIn.
Analyze every data point and produce a comprehensive candidate evaluation.

Return your analysis as **valid JSON only** (no markdown fences, no extra text) with this schema:

    {
        "overall_assessment": "2-3 sentence overall assessment",
        "strengths": ["strength 1", "strength 2", ...],
        "areas_to_explore": ["area 1", "area 2", ...],
        "technical_depth": "paragraph assessing technical depth from repos & problem-solving",
        "interview_questions": [
            {"question": "...", "context": "why this question matters given their profile"}
        ],
        "score": {
            "technical_skills": <0-10>,
            "project_quality": <0-10>,
            "problem_solving": <0-10>,
            "overall": <0-10>
        }
    }

Rules:
- Be specific: reference actual repo names, languages, problem counts, etc.
- Generate 5-8 targeted interview questions.
- Return ONLY the JSON object, nothing else."""

agent = Agent(
    name="prescreen_agent",
    model="gemini-2.0-flash",
    description="Candidate prescreening and evaluation agent",
    instruction=AGENT_INSTRUCTION,
)

session_service = InMemorySessionService()
runner = Runner(agent=agent, app_name="hireforce", session_service=session_service)


async def run_prescreen_analysis(
    github_data: dict,
    leetcode_data: dict,
    linkedin_data: dict,
    resume_text: str = "",
) -> dict:
    """Collect all candidate data and ask the agent for a structured evaluation."""

    prompt_parts = ["Analyze the following candidate data and provide your evaluation:\n"]

    if resume_text:
        prompt_parts.append(f"## Resume Text\n{resume_text[:3000]}\n")

    if github_data and not github_data.get("error"):
        prompt_parts.append(
            f"## GitHub Profile\n{json.dumps(github_data, indent=2, default=str)}\n"
        )

    if leetcode_data and not leetcode_data.get("error"):
        prompt_parts.append(
            f"## LeetCode Profile\n{json.dumps(leetcode_data, indent=2, default=str)}\n"
        )

    if linkedin_data and not linkedin_data.get("error"):
        prompt_parts.append(
            f"## LinkedIn Profile\n{json.dumps(linkedin_data, indent=2, default=str)}\n"
        )

    prompt = "\n".join(prompt_parts)

    try:
        session = await session_service.create_session(
            app_name="hireforce", user_id="system"
        )

        content = types.Content(
            role="user", parts=[types.Part(text=prompt)]
        )

        final_response = ""
        async for event in runner.run_async(
            user_id="system", session_id=session.id, new_message=content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_response += part.text

        cleaned = final_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        return json.loads(cleaned)

    except json.JSONDecodeError:
        return _fallback(final_response)
    except Exception as e:
        return _fallback(f"Agent error: {e}")


def _fallback(raw: str) -> dict:
    return {
        "overall_assessment": raw or "Agent analysis unavailable. Check your GOOGLE_API_KEY.",
        "strengths": [],
        "areas_to_explore": [],
        "technical_depth": "",
        "interview_questions": [],
        "score": {
            "technical_skills": 0,
            "project_quality": 0,
            "problem_solving": 0,
            "overall": 0,
        },
        "raw_response": raw,
    }
