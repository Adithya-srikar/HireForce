"""
Recruiter API routes.

All routes require a valid recruiter JWT (Authorization: Bearer <token>).
"""
import os

from fastapi import APIRouter, Depends, HTTPException

from models.job import JobCreate, JobUpdate
from repositories.application_repo import (
    get_application,
    get_applications_by_job,
    update_application_status,
)
from repositories.interview_repo import create_interview, get_interview
from repositories.job_repo import (
    create_job,
    delete_job,
    get_job,
    list_jobs_by_recruiter,
    update_job,
)
from repositories.report_repo import get_report
from repositories.user_repo import get_user_by_id
from services.auth_service import require_recruiter
from services.email_service import send_interview_invite

recruiter_router = APIRouter(prefix="/recruiter", tags=["recruiter"])

_APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")


# ── Job management ────────────────────────────────────────────

@recruiter_router.get("/jobs")
async def list_my_jobs(user: dict = Depends(require_recruiter)):
    """List all jobs posted by the authenticated recruiter."""
    return list_jobs_by_recruiter(user["sub"])


@recruiter_router.post("/jobs", status_code=201)
async def post_job(body: JobCreate, user: dict = Depends(require_recruiter)):
    """Create a new job posting."""
    job_id = create_job(recruiter_id=user["sub"], data=body.model_dump())
    return {"message": "Job created", "job_id": job_id}


@recruiter_router.put("/jobs/{job_id}")
async def edit_job(
    job_id: str,
    body: JobUpdate,
    user: dict = Depends(require_recruiter),
):
    """Update an existing job posting."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["recruiter_id"] != user["sub"]:
        raise HTTPException(status_code=403, detail="You can only edit your own jobs")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_job(job_id, updates)
    return {"message": "Job updated"}


@recruiter_router.delete("/jobs/{job_id}")
async def remove_job(
    job_id: str,
    user: dict = Depends(require_recruiter),
):
    """Soft-delete a job posting."""
    deleted = delete_job(job_id, user["sub"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found or access denied")
    return {"message": "Job removed"}


# ── Applicants ────────────────────────────────────────────────

@recruiter_router.get("/jobs/{job_id}/applicants")
async def list_applicants(
    job_id: str,
    user: dict = Depends(require_recruiter),
):
    """
    Get all applicants for a job, sorted by ATS score (highest first).
    Also enriches each entry with the student's basic profile info.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["recruiter_id"] != user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")

    applications = get_applications_by_job(job_id)
    enriched = []
    for app in applications:
        student = get_user_by_id(app["student_id"]) or {}
        student.pop("password_hash", None)
        enriched.append({
            "application_id": app["_id"],
            "status": app["status"],
            "ats_score": app["ats_score"],
            "applied_at": app["created_at"],
            "interview_id": app.get("interview_id"),
            "student": {
                "id": student.get("_id"),
                "name": student.get("name"),
                "email": student.get("email"),
                "phone": student.get("phone"),
                "linkedin": student.get("linkedin"),
                "github": student.get("github"),
                "leetcode": student.get("leetcode"),
            },
        })
    return enriched


# ── Schedule interview ────────────────────────────────────────

@recruiter_router.post("/jobs/{job_id}/applicants/{application_id}/schedule")
async def schedule_interview(
    job_id: str,
    application_id: str,
    interview_date: str,
    interview_time: str,
    user: dict = Depends(require_recruiter),
):
    """
    Schedule an AI interview for a shortlisted candidate.
    Creates an interview record, updates the application status,
    and sends an email invite to the candidate.
    """
    # Validate job ownership
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["recruiter_id"] != user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get application + student
    app = get_application(application_id)
    if not app or app["job_id"] != job_id:
        raise HTTPException(status_code=404, detail="Application not found")

    student = get_user_by_id(app["student_id"])
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Create interview record
    prescreen_id = student.get("prescreen_id") or ""
    interview_id = create_interview(
        prescreen_id=prescreen_id,
        job_description=f"{job.get('title', '')} – {job.get('description', '')}",
        interview_date=interview_date,
        interview_time=interview_time,
    )

    # Update application status
    update_application_status(application_id, "interview_scheduled", interview_id=interview_id)

    # Build interview link and send email
    interview_link = f"{_APP_BASE_URL}/take-interview?interview_id={interview_id}"
    send_interview_invite(
        candidate_name=student.get("name", "Candidate"),
        candidate_email=student["email"],
        job_title=job.get("title", "the role"),
        interview_date=interview_date,
        interview_time=interview_time,
        interview_link=interview_link,
    )

    return {
        "message": "Interview scheduled and invite sent",
        "interview_id": interview_id,
        "interview_link": interview_link,
        "candidate_email": student["email"],
    }


@recruiter_router.get("/applicants/{student_id}/graph")
async def get_applicant_graph(
    student_id: str,
    _user: dict = Depends(require_recruiter),
):
    """
    Return the knowledge graph for a candidate.
    The graph is built from GitHub + LeetCode + LinkedIn data during prescreen.
    """
    student = get_user_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Try prescreen_id on the profile first
    prescreen_id = student.get("prescreen_id")

    # Fall back: graph may be stored directly as platform_data graph
    if not prescreen_id:
        # Build a live graph from whatever platform data the student has stored
        from services.graph_builder import build_knowledge_graph
        platform = student.get("platform_data", {})
        graph = build_knowledge_graph(
            platform.get("github", {}),
            platform.get("leetcode", {}),
            platform.get("linkedin", {}),
            student.get("resume_text", ""),
        )
        return {
            "student_id": student_id,
            "student_name": student.get("name"),
            "source": "live",
            "graph": graph,
        }

    # Use stored prescreen graph
    from repositories.prescreen_repo import get_prescreen
    prescreen = get_prescreen(prescreen_id)
    if not prescreen:
        raise HTTPException(status_code=404, detail="Prescreen data not found")

    graph = prescreen.get("graph")
    if not graph:
        raise HTTPException(status_code=404, detail="No graph yet – student hasn't connected their profiles")

    return {
        "student_id": student_id,
        "student_name": student.get("name"),
        "prescreen_id": prescreen_id,
        "source": "prescreen",
        "graph": graph,
    }


# ── Interview report ──────────────────────────────────────────

@recruiter_router.get("/interviews/{interview_id}/report")
async def get_interview_report(
    interview_id: str,
    user: dict = Depends(require_recruiter),
):
    """Retrieve the AI-generated report for a completed interview."""
    from repositories.session_repo import get_session

    interview = get_interview(interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # Find associated session to locate the report
    from config.db import get_db
    from models import SESSION_COLLECTION

    db = get_db()
    session_doc = db[SESSION_COLLECTION].find_one({"interview_id": interview_id})
    if not session_doc:
        raise HTTPException(status_code=404, detail="No session found for this interview")

    report_id = session_doc.get("report_id")
    if not report_id:
        raise HTTPException(status_code=404, detail="Interview not yet completed or report unavailable")

    report = get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "interview_id": interview_id,
        "report_id": report_id,
        "report": report,
    }
