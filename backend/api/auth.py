"""Auth routes: register (student/recruiter) and login."""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from models.user import LoginRequest, RecruiterRegister, StudentRegister, TokenResponse
from repositories.user_repo import create_user, get_user_by_email
from services.auth_service import create_jwt, hash_password, verify_password

auth_router = APIRouter(prefix="/auth", tags=["auth"])


# ── Register ──────────────────────────────────────────────────

@auth_router.post("/register/student", response_model=TokenResponse, status_code=201)
async def register_student(body: StudentRegister):
    """Register a new student account."""
    if get_user_by_email(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = create_user({
        "name": body.name,
        "email": body.email,
        "password_hash": hash_password(body.password),
        "phone": body.phone,
        "role": "student",
        # Profile data filled in later
        "linkedin": "",
        "github": "",
        "leetcode": "",
        "resume_text": "",
        "resume_filename": "",
        "platform_data": {},
        "graph": {},
        "prescreen_id": None,
    })

    token = create_jwt(user_id, "student")
    return TokenResponse(access_token=token, user_id=user_id, role="student")


@auth_router.post("/register/recruiter", response_model=TokenResponse, status_code=201)
async def register_recruiter(body: RecruiterRegister):
    """Register a new recruiter account."""
    if get_user_by_email(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = create_user({
        "name": body.name,
        "email": body.email,
        "password_hash": hash_password(body.password),
        "phone": body.phone,
        "role": "recruiter",
        "company": body.company,
        "designation": body.designation,
        "company_url": body.company_url,
    })

    token = create_jwt(user_id, "recruiter")
    return TokenResponse(access_token=token, user_id=user_id, role="recruiter")


# ── Login ─────────────────────────────────────────────────────

@auth_router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    """Login with email + password. Returns JWT."""
    user = get_user_by_email(body.email)
    if not user or not verify_password(body.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_jwt(user["_id"], user["role"])
    return TokenResponse(
        access_token=token,
        user_id=user["_id"],
        role=user["role"],
    )
