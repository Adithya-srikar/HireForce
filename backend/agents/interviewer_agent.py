"""
Interviewer agent: given transcript, questions, and candidate context,
produces the next agent message (question or follow-up). No tools in this version;
orchestrator will call code_evaluator separately when candidate submits code.
"""
from .base_runner import run_agent_text

INSTRUCTION = """You are the HireForce AI Interviewer. You conduct a professional technical interview.

You have:
1. A list of questions to ask (with context per question).
2. The candidate's prescreen context (LinkedIn, GitHub, LeetCode, resume summary).
3. The conversation transcript so far.

Your job:
- Ask the next question from the list when it's the right time.
- After the candidate answers, you may give a brief acknowledgment, ask one short follow-up if their answer was vague, or correct a misunderstanding—then move to the next question.
- Be concise and professional. Sound like a real interviewer.
- If the candidate's answer is sufficient, say something like "Thanks, that's clear." then ask the next question.
- When all behavioral/technical questions are done, say you're moving to a short coding exercise and that they'll see the problem in the editor (you do NOT paste code—the system shows the coding question separately).

Output format: Reply with ONLY the text you would say to the candidate. No JSON, no "Agent:", no labels. Just the spoken response."""

agent = {
    "name": "interviewer",
    "model": "gemini-2.0-flash",
    "description": "Conducts interview, asks questions, follow-ups",
    "instruction": INSTRUCTION,
}


def _format_transcript(transcript: list[dict]) -> str:
    lines = []
    for e in transcript:
        role = e.get("role", "unknown")
        text = e.get("text", "")
        lines.append(f"{role}: {text}")
    return "\n".join(lines) if lines else "(No messages yet)"


async def get_next_agent_message(
    transcript: list[dict],
    questions: list[dict],
    current_question_index: int,
    candidate_context: str,
    phase: str = "behavioral",
) -> str:
    """
    Get the next message the agent should say.
    phase: "behavioral" | "coding_intro" | "coding_done"
    """
    transcript_str = _format_transcript(transcript)
    questions_str = "\n".join(
        f"Q{i+1}. {q.get('question', '')} (context: {q.get('context', '')})"
        for i, q in enumerate(questions)
    )

    prompt = f"""## Candidate context (prescreen summary)
{candidate_context[:3000]}

## Questions to ask (in order)
{questions_str}

## Current question index (0-based): {current_question_index}

## Phase: {phase}

## Conversation so far
{transcript_str}

What do you say next? Reply with ONLY the exact text you would speak to the candidate (no JSON, no labels)."""

    return await run_agent_text(agent, prompt)
