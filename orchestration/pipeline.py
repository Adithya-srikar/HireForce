"""
Agent orchestration pipeline:
  prescreen (saved) -> question generator -> interview (saved)
  -> interviewer (Q&A) + code challenger / code evaluator -> summariser -> report generator -> report (saved)
"""
from agents.question_generator_agent import generate_questions
from agents.code_challenger_agent import generate_coding_question
from agents.code_evaluator_agent import evaluate_code
from agents.interviewer_agent import get_next_agent_message
from agents.summariser_agent import summarise_interview
from agents.report_generator_agent import generate_report
from repositories import (
    get_prescreen,
    create_interview,
    get_interview,
    add_questions_to_interview,
    create_session,
    get_session,
    append_transcript,
    set_code_and_evaluation,
    set_report_id,
    save_report,
)


async def generate_questions_for_interview(
    prescreen_id: str,
    job_description: str,
    interview_date: str,
    interview_time: str,
) -> dict:
    """
    Load prescreen, run question generator, create interview and save questions.
    Returns { "interview_id", "questions", "coding_question" }.
    """
    prescreen = get_prescreen(prescreen_id)
    if not prescreen:
        raise ValueError("Prescreen not found")

    analysis = prescreen.get("analysis") or {}
    platform_data = prescreen.get("platform_data") or {}
    platform_summary = ""
    if platform_data:
        platform_summary = _short_platform_summary(platform_data)

    result = await generate_questions(
        job_description=job_description,
        prescreen_analysis=analysis,
        prescreen_platform_summary=platform_summary,
    )

    questions = result.get("questions") or []
    coding_question = result.get("coding_question") or {}

    # If no coding question from generator, get one from code challenger
    if not coding_question.get("title"):
        coding_question = await generate_coding_question("python")

    interview_id = create_interview(
        prescreen_id=prescreen_id,
        job_description=job_description,
        interview_date=interview_date,
        interview_time=interview_time,
    )
    add_questions_to_interview(interview_id, questions, coding_question)

    return {
        "interview_id": interview_id,
        "questions": questions,
        "coding_question": coding_question,
    }


def _short_platform_summary(platform_data: dict) -> str:
    parts = []
    for key in ("github", "leetcode", "linkedin"):
        data = platform_data.get(key) or {}
        if data.get("error"):
            continue
        if key == "github" and data.get("username"):
            parts.append(f"GitHub: {data.get('username')}, repos: {data.get('public_repos', 0)}")
        if key == "leetcode" and data.get("username"):
            parts.append(f"LeetCode: {data.get('username')}, solved: {data.get('total_solved', 0)}")
        if key == "linkedin" and data.get("name"):
            parts.append(f"LinkedIn: {data.get('name')}, {data.get('headline', '')[:100]}")
    return " | ".join(parts)


async def start_interview(interview_id: str) -> dict:
    """
    Create session, seed transcript with first agent message.
    Returns { "session_id", "agent_message", "questions", "coding_question" }.
    """
    interview = get_interview(interview_id)
    if not interview:
        raise ValueError("Interview not found")

    session_id = create_session(interview_id)
    prescreen = get_prescreen(interview.get("prescreen_id", ""))
    candidate_context = _candidate_context_from_prescreen(prescreen)
    questions = interview.get("questions") or []
    coding_question = interview.get("coding_question") or {}

    # First agent message (greeting + first question)
    first_message = await get_next_agent_message(
        transcript=[],
        questions=questions,
        current_question_index=0,
        candidate_context=candidate_context,
        phase="behavioral",
    )
    append_transcript(session_id, "agent", first_message)

    return {
        "session_id": session_id,
        "agent_message": first_message,
        "questions": questions,
        "coding_question": coding_question,
    }


def _candidate_context_from_prescreen(prescreen: dict | None) -> str:
    if not prescreen:
        return "No prescreen context."
    analysis = prescreen.get("analysis") or {}
    parts = [analysis.get("overall_assessment", "")[:1500]]
    if analysis.get("strengths"):
        parts.append("Strengths: " + ", ".join(analysis["strengths"][:5]))
    if analysis.get("technical_depth"):
        parts.append("Technical: " + analysis["technical_depth"][:800])
    return "\n".join(parts)


async def get_next_turn(session_id: str, candidate_message: str) -> dict:
    """
    Append candidate message to transcript, get next agent message.
    Returns { "agent_message" }.
    """
    session = get_session(session_id)
    if not session:
        raise ValueError("Session not found")

    append_transcript(session_id, "candidate", candidate_message)
    transcript = session.get("transcript", []) + [
        {"role": "candidate", "text": candidate_message},
    ]
    interview = get_interview(session.get("interview_id", ""))
    prescreen = get_prescreen(interview.get("prescreen_id", "")) if interview else None
    candidate_context = _candidate_context_from_prescreen(prescreen)
    questions = (interview or {}).get("questions") or []

    # Next question index = number of agent turns so far (we're about to add one more)
    num_agent_turns = len([t for t in transcript if t.get("role") == "agent"])
    current_index = min(num_agent_turns, len(questions) - 1) if questions else 0
    current_index = max(0, current_index)
    phase = "behavioral" if not session.get("code_evaluation") else "coding_done"

    agent_message = await get_next_agent_message(
        transcript=transcript,
        questions=questions,
        current_question_index=current_index,
        candidate_context=candidate_context,
        phase=phase,
    )
    append_transcript(session_id, "agent", agent_message)

    return {"agent_message": agent_message}


async def submit_code(
    session_id: str,
    code: str,
    language: str,
) -> dict:
    """
    Evaluate code, save to session, return evaluation and a short agent message.
    Returns { "evaluation", "agent_message" }.
    """
    session = get_session(session_id)
    if not session:
        raise ValueError("Session not found")
    interview = get_interview(session.get("interview_id", ""))
    coding = (interview or {}).get("coding_question") or {}
    description = coding.get("description", "Solve the problem.")
    expected = coding.get("expected_behavior", "Correct output.")

    evaluation = await evaluate_code(
        code=code,
        language=language,
        problem_description=description,
        expected_behavior=expected,
    )
    set_code_and_evaluation(session_id, code, language, evaluation)

    passed = evaluation.get("passed", False)
    feedback = evaluation.get("feedback", "")
    agent_message = (
        f"Thanks for submitting. {'The solution looks correct. ' if passed else ''}{feedback}"
    )

    return {"evaluation": evaluation, "agent_message": agent_message}


async def end_interview(session_id: str, recording_ref: str | None = None) -> dict:
    """
    Run summariser -> report generator -> save report -> update session.
    Returns { "report_id", "verdict", "report_text", "summary" }.
    """
    session = get_session(session_id)
    if not session:
        raise ValueError("Session not found")
    interview = get_interview(session.get("interview_id", ""))
    prescreen = get_prescreen(interview.get("prescreen_id", "")) if interview else None
    candidate_context = _candidate_context_from_prescreen(prescreen)
    transcript = session.get("transcript") or []
    code_evaluation = session.get("code_evaluation")

    summary = await summarise_interview(
        transcript=transcript,
        prescreen_summary=candidate_context,
        code_evaluation=code_evaluation,
    )
    report_result = await generate_report(summary)

    verdict = report_result.get("verdict", "unfit")
    report_text = report_result.get("report_text", "")

    report_id = save_report(
        session_id=session_id,
        verdict=verdict,
        summary=summary,
        report_text=report_text,
        recording_ref=recording_ref,
    )
    set_report_id(session_id, report_id)

    return {
        "report_id": report_id,
        "verdict": verdict,
        "report_text": report_text,
        "summary": summary,
    }
