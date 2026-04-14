"""
Student API routes.

All routes require a valid student JWT (Authorization: Bearer <token>).
"""
import asyncio
import os
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse

from models.user import StudentProfileUpdate
from repositories.application_repo import (
    create_application,
    get_application,
    get_applications_by_student,
    update_application_status,
)
from repositories.interview_repo import get_interview
from repositories.job_repo import get_job, list_open_jobs
from repositories.user_repo import get_user_by_id, update_user
from services.ats_service import score_resume
from services.auth_service import require_student
from services.github_service import fetch_github_profile
from services.leetcode_service import fetch_leetcode_profile
from services.linkedin_service import fetch_linkedin_profile
from services.resume_parser import extract_text_from_pdf, extract_urls, extract_username_from_url

student_router = APIRouter(prefix="/student", tags=["student"])

_GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
_GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
_GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/student/github/callback")
_APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")


# ── Profile ───────────────────────────────────────────────────

@student_router.get("/profile")
async def get_profile(user: dict = Depends(require_student)):
    """Return the authenticated student's profile."""
    doc = get_user_by_id(user["sub"])
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    doc.pop("password_hash", None)
    return doc


@student_router.put("/profile")
async def update_profile(
    body: StudentProfileUpdate,
    user: dict = Depends(require_student),
):
    """Update basic profile fields."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_user(user["sub"], updates)
    return {"message": "Profile updated"}


# ── Resume upload ─────────────────────────────────────────────

@student_router.post("/resume/upload")
async def upload_resume(
    resume: UploadFile = File(...),
    user: dict = Depends(require_student),
):
    """
    Upload a PDF resume. Extracts text, auto-detects social profile URLs,
    and saves them to the student's profile. Returns extracted data.
    """
    if not resume.filename or not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")

    file_bytes = await resume.read()
    resume_text = extract_text_from_pdf(file_bytes)
    extracted = extract_urls(resume_text)

    profile_updates: dict = {
        "resume_text": resume_text,
        "resume_filename": resume.filename,
    }
    if extracted.get("linkedin"):
        profile_updates["linkedin"] = extracted["linkedin"]
    if extracted.get("github"):
        profile_updates["github"] = extracted["github"]
    if extracted.get("leetcode"):
        profile_updates["leetcode"] = extracted["leetcode"]

    update_user(user["sub"], profile_updates)

    return {
        "message": "Resume uploaded successfully",
        "filename": resume.filename,
        "extracted_urls": extracted,
        "resume_preview": resume_text[:500] + "..." if len(resume_text) > 500 else resume_text,
    }


# ── GitHub OAuth ──────────────────────────────────────────────

@student_router.get("/github/connect-url")
async def github_connect_url(user: dict = Depends(require_student)):
    """
    Returns the GitHub OAuth URL as JSON so the frontend can redirect to it.
    (Browser link navigation can't send Bearer headers, so we use fetch + JS redirect.)
    """
    if not _GITHUB_CLIENT_ID:
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured (GITHUB_CLIENT_ID missing)")

    state = user["sub"]   # user_id as state for CSRF protection
    url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={_GITHUB_CLIENT_ID}"
        f"&redirect_uri={_GITHUB_REDIRECT_URI}"
        f"&scope=read:user,repo"
        f"&state={state}"
    )
    return {"url": url}


@student_router.get("/github/callback")
async def github_callback(code: str, state: str):
    """
    GitHub OAuth callback. Exchanges the code for an access token,
    fetches the GitHub profile, stores it, and redirects to the dashboard.
    """
    if not _GITHUB_CLIENT_ID or not _GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured")

    # Exchange code → access token
    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": _GITHUB_CLIENT_ID,
                "client_secret": _GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": _GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to obtain GitHub access token")

    # Get GitHub username
    async with httpx.AsyncClient(timeout=15.0) as client:
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github.v3+json"},
        )
    gh_user = user_resp.json()
    username = gh_user.get("login")
    if not username:
        raise HTTPException(status_code=400, detail="Could not determine GitHub username")

    # Fetch full profile using existing service (uses GITHUB_TOKEN env var)
    profile_data = await fetch_github_profile(username)

    # Persist to student profile
    update_user(state, {
        "github": f"https://github.com/{username}",
        "platform_data.github": profile_data,
    })

    # Redirect back to frontend profile page with success flag
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(url=f"{frontend_url}/student/profile?github_connected=1")


# ── LeetCode connect (username-based, no OAuth) ───────────────

@student_router.post("/leetcode/connect")
async def leetcode_connect(
    leetcode_username: str = Form(...),
    user: dict = Depends(require_student),
):
    """
    Fetch and store LeetCode profile data using the student's username.
    LeetCode doesn't have OAuth, so we accept the username directly.
    """
    profile_data = await fetch_leetcode_profile(leetcode_username)
    if "error" in profile_data:
        raise HTTPException(status_code=400, detail=profile_data["error"])

    update_user(user["sub"], {
        "leetcode": f"https://leetcode.com/{leetcode_username}",
        "platform_data.leetcode": profile_data,
    })
    return {"message": f"LeetCode @{leetcode_username} connected", "profile": profile_data}


# ── Jobs ──────────────────────────────────────────────────────

@student_router.get("/jobs")
async def browse_jobs(_user: dict = Depends(require_student)):
    """List all open job postings."""
    return list_open_jobs()


@student_router.post("/jobs/{job_id}/apply")
async def apply_for_job(
    job_id: str,
    resume: UploadFile = File(...),
    user: dict = Depends(require_student),
):
    """
    Apply to a job with a per-application resume upload.
    The resume is scored against the job description (ATS) and stored.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.get("is_open"):
        raise HTTPException(status_code=400, detail="This job is no longer open")

    # Check for duplicate application
    existing = get_applications_by_student(user["sub"])
    if any(a["job_id"] == job_id for a in existing):
        raise HTTPException(status_code=400, detail="You have already applied to this job")

    # Parse resume
    if not resume.filename or not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")
    file_bytes = await resume.read()
    resume_text = extract_text_from_pdf(file_bytes)

    # ATS scoring
    job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('requirements', '')}"
    ats_score = score_resume(resume_text, job_text)

    application_id = create_application(
        student_id=user["sub"],
        job_id=job_id,
        resume_text=resume_text,
        ats_score=ats_score,
        resume_filename=resume.filename,
    )

    return {
        "message": "Application submitted successfully",
        "application_id": application_id,
        "ats_score": ats_score,
    }


@student_router.get("/jobs/{job_id}/status")
async def job_application_status(
    job_id: str,
    user: dict = Depends(require_student),
):
    """Check the status of the student's application for a specific job."""
    applications = get_applications_by_student(user["sub"])
    app = next((a for a in applications if a["job_id"] == job_id), None)
    if not app:
        raise HTTPException(status_code=404, detail="No application found for this job")
    return {
        "application_id": app["_id"],
        "status": app["status"],
        "ats_score": app["ats_score"],
        "applied_at": app["created_at"],
        "interview_id": app.get("interview_id"),
    }


# ── Interviews ────────────────────────────────────────────────

@student_router.get("/interviews")
async def list_interviews(user: dict = Depends(require_student)):
    """List all interviews scheduled for this student."""
    applications = get_applications_by_student(user["sub"])
    scheduled = [a for a in applications if a.get("interview_id")]

    interviews = []
    for app in scheduled:
        interview = get_interview(app["interview_id"])
        if interview:
            interviews.append({
                "application_id": app["_id"],
                "job_id": app["job_id"],
                "interview": interview,
            })
    return interviews


@student_router.get("/interviews/{interview_id}")
async def get_interview_detail(
    interview_id: str,
    user: dict = Depends(require_student),
):
    """Get full details for a specific interview."""
    # Ensure this interview belongs to the student
    applications = get_applications_by_student(user["sub"])
    owns = any(a.get("interview_id") == interview_id for a in applications)
    if not owns:
        raise HTTPException(status_code=403, detail="Access denied")

    interview = get_interview(interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview
