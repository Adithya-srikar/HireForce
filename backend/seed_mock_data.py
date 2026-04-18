"""
Seed script – inserts mock recruiter, students, jobs, and applications.
Run from the backend/ directory:  python seed_mock_data.py
Safe to run multiple times; skips entities that already exist (by email / job title + recruiter).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from passlib.context import CryptContext

from config.db import get_db
from models import USERS_COLLECTION, JOBS_COLLECTION, APPLICATIONS_COLLECTION

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = get_db()

# ── helpers ──────────────────────────────────────────────────────────────

def upsert_user(data: dict) -> str:
    existing = db[USERS_COLLECTION].find_one({"email": data["email"]})
    if existing:
        return str(existing["_id"])
    now = datetime.utcnow()
    data.update({"created_at": now, "updated_at": now})
    return str(db[USERS_COLLECTION].insert_one(data).inserted_id)


def upsert_job(recruiter_id: str, title: str, data: dict) -> str:
    existing = db[JOBS_COLLECTION].find_one({"recruiter_id": recruiter_id, "title": title})
    if existing:
        return str(existing["_id"])
    now = datetime.utcnow()
    data.update({
        "recruiter_id": recruiter_id,
        "title": title,
        "is_open": True,
        "created_at": now,
        "updated_at": now,
    })
    return str(db[JOBS_COLLECTION].insert_one(data).inserted_id)


def upsert_application(student_id: str, job_id: str, data: dict) -> str:
    existing = db[APPLICATIONS_COLLECTION].find_one({"student_id": student_id, "job_id": job_id})
    if existing:
        return str(existing["_id"])
    now = datetime.utcnow()
    data.update({
        "student_id": student_id,
        "job_id": job_id,
        "interview_id": None,
        "created_at": now,
        "updated_at": now,
    })
    return str(db[APPLICATIONS_COLLECTION].insert_one(data).inserted_id)


# ── recruiter ────────────────────────────────────────────────────────────
# Use the existing srikar@plexis.in recruiter account.

RECRUITER_EMAIL = "srikar@plexis.in"

existing_recruiter = db[USERS_COLLECTION].find_one({"email": RECRUITER_EMAIL})
if not existing_recruiter:
    raise RuntimeError(f"Recruiter {RECRUITER_EMAIL} not found in DB – register first.")
recruiter_id = str(existing_recruiter["_id"])
print(f"Recruiter: {recruiter_id} ({existing_recruiter['name']})")

# ── jobs ─────────────────────────────────────────────────────────────────

job_ids = {}

job_ids["swe"] = upsert_job(recruiter_id, "Software Engineer – Backend", {
    "description": (
        "Join our backend team to design and scale distributed services. "
        "You will work on high-throughput APIs, data pipelines, and cloud infrastructure."
    ),
    "requirements": (
        "2+ years of backend experience. Strong knowledge of Python or Go. "
        "Familiarity with PostgreSQL, Redis, and REST API design."
    ),
    "location": "Bangalore, India (Hybrid)",
    "employment_type": "full-time",
    "salary_range": "12–18 LPA",
    "skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
    "coding_round": True,
})

job_ids["ml"] = upsert_job(recruiter_id, "Machine Learning Engineer", {
    "description": (
        "Build and productionise ML models that power our recommendation and search systems. "
        "Work closely with data scientists and platform engineers."
    ),
    "requirements": (
        "3+ years in ML engineering. Proficient in PyTorch or TensorFlow. "
        "Experience with MLOps tooling (MLflow, Kubeflow, or similar)."
    ),
    "location": "Remote (India)",
    "employment_type": "full-time",
    "salary_range": "18–28 LPA",
    "skills": ["Python", "PyTorch", "MLflow", "Kubernetes", "SQL"],
    "coding_round": True,
})

job_ids["fe"] = upsert_job(recruiter_id, "Frontend Developer – React", {
    "description": (
        "Craft responsive, accessible UIs for our SaaS platform used by 50k+ recruiters worldwide. "
        "Collaborate with designers and product managers to ship delightful features."
    ),
    "requirements": (
        "2+ years with React. Strong CSS and TypeScript skills. "
        "Experience with state management (Redux, Zustand, or similar)."
    ),
    "location": "Hyderabad, India (On-site)",
    "employment_type": "full-time",
    "salary_range": "10–16 LPA",
    "skills": ["React", "TypeScript", "Tailwind CSS", "Redux", "Vite"],
    "coding_round": False,
})

job_ids["devops"] = upsert_job(recruiter_id, "DevOps / Platform Engineer", {
    "description": (
        "Own CI/CD pipelines, cloud infrastructure, and observability for our production systems. "
        "Drive automation across deployment, monitoring, and cost optimisation."
    ),
    "requirements": (
        "3+ years in DevOps or SRE roles. Hands-on with AWS or GCP. "
        "Strong scripting skills (Bash/Python). IaC experience with Terraform."
    ),
    "location": "Pune, India (Hybrid)",
    "employment_type": "full-time",
    "salary_range": "14–22 LPA",
    "skills": ["AWS", "Terraform", "Kubernetes", "GitHub Actions", "Prometheus"],
    "coding_round": False,
})

job_ids["intern"] = upsert_job(recruiter_id, "Software Engineering Intern", {
    "description": (
        "Six-month internship working on real product features alongside senior engineers. "
        "Great opportunity to learn full-stack development in a fast-paced startup environment."
    ),
    "requirements": (
        "Currently pursuing B.Tech/B.E. in CS or related field. "
        "Comfortable with any one programming language. Eagerness to learn."
    ),
    "location": "Bangalore, India (On-site)",
    "employment_type": "internship",
    "salary_range": "25,000–40,000 /month",
    "skills": ["Python", "JavaScript", "Git", "REST APIs"],
    "coding_round": True,
})

print("Jobs:", job_ids)

# ── students ─────────────────────────────────────────────────────────────

students = [
    {
        "name": "Arjun Mehta",
        "email": "arjun.mehta@example.com",
        "phone": "9000000001",
        "linkedin": "https://linkedin.com/in/arjunmehta",
        "github": "arjunmehta",
        "leetcode": "arjun_codes",
    },
    {
        "name": "Sneha Reddy",
        "email": "sneha.reddy@example.com",
        "phone": "9000000002",
        "linkedin": "https://linkedin.com/in/snehareddy",
        "github": "snehareddy",
        "leetcode": "sneha_r",
    },
    {
        "name": "Karan Patel",
        "email": "karan.patel@example.com",
        "phone": "9000000003",
        "linkedin": "https://linkedin.com/in/karanpatel",
        "github": "karanpatel",
        "leetcode": "karan_p",
    },
    {
        "name": "Divya Nair",
        "email": "divya.nair@example.com",
        "phone": "9000000004",
        "linkedin": "https://linkedin.com/in/divyanair",
        "github": "divyanair",
        "leetcode": "divya_n",
    },
    {
        "name": "Rahul Gupta",
        "email": "rahul.gupta@example.com",
        "phone": "9000000005",
        "linkedin": "https://linkedin.com/in/rahulgupta",
        "github": "rahulgupta",
        "leetcode": "rahul_g",
    },
    {
        "name": "Ananya Singh",
        "email": "ananya.singh@example.com",
        "phone": "9000000006",
        "linkedin": "https://linkedin.com/in/ananyasingh",
        "github": "ananyasingh",
        "leetcode": "ananya_s",
    },
    {
        "name": "Vikram Joshi",
        "email": "vikram.joshi@example.com",
        "phone": "9000000007",
        "linkedin": "https://linkedin.com/in/vikramjoshi",
        "github": "vikramjoshi",
        "leetcode": "vikram_j",
    },
    {
        "name": "Pooja Iyer",
        "email": "pooja.iyer@example.com",
        "phone": "9000000008",
        "linkedin": "https://linkedin.com/in/poojaiyer",
        "github": "poojaiyer",
        "leetcode": "pooja_i",
    },
]

student_ids = []
for s in students:
    sid = upsert_user({
        **s,
        "password_hash": pwd_ctx.hash("password123"),
        "role": "student",
    })
    student_ids.append(sid)
    print(f"  Student {s['name']}: {sid}")

# ── applications ─────────────────────────────────────────────────────────
# Each student gets realistic applications with varied ATS scores and statuses.

applications = [
    # SWE Backend
    (student_ids[0], job_ids["swe"], {"ats_score": 0.885, "status": "shortlisted",
        "resume_filename": "arjun_resume.pdf",
        "resume_text": "3 years Python, FastAPI, PostgreSQL. Built microservices at Infosys."}),
    (student_ids[1], job_ids["swe"], {"ats_score": 0.74, "status": "applied",
        "resume_filename": "sneha_resume.pdf",
        "resume_text": "Backend intern, Django REST, MySQL. Final year student."}),
    (student_ids[4], job_ids["swe"], {"ats_score": 0.912, "status": "interview_scheduled",
        "resume_filename": "rahul_resume.pdf",
        "resume_text": "5 years Python/Go, Redis, Kafka. Lead engineer at startup."}),
    (student_ids[6], job_ids["swe"], {"ats_score": 0.62, "status": "rejected",
        "resume_filename": "vikram_resume.pdf",
        "resume_text": "PHP developer, 1 year exp. Familiar with basic REST APIs."}),

    # ML Engineer
    (student_ids[1], job_ids["ml"], {"ats_score": 0.85, "status": "shortlisted",
        "resume_filename": "sneha_ml_resume.pdf",
        "resume_text": "MS Data Science, PyTorch, scikit-learn. Published NLP paper."}),
    (student_ids[3], job_ids["ml"], {"ats_score": 0.795, "status": "applied",
        "resume_filename": "divya_resume.pdf",
        "resume_text": "ML intern at Google. TensorFlow, Keras, MLflow experience."}),
    (student_ids[5], job_ids["ml"], {"ats_score": 0.93, "status": "interview_scheduled",
        "resume_filename": "ananya_resume.pdf",
        "resume_text": "4 years ML engineering. Kubeflow, PyTorch, production model serving."}),

    # Frontend
    (student_ids[2], job_ids["fe"], {"ats_score": 0.82, "status": "shortlisted",
        "resume_filename": "karan_resume.pdf",
        "resume_text": "React, TypeScript, Redux Toolkit. 2.5 years frontend dev."}),
    (student_ids[7], job_ids["fe"], {"ats_score": 0.70, "status": "applied",
        "resume_filename": "pooja_resume.pdf",
        "resume_text": "Vue.js, some React experience, CSS animations expert."}),
    (student_ids[0], job_ids["fe"], {"ats_score": 0.55, "status": "rejected",
        "resume_filename": "arjun_fe_resume.pdf",
        "resume_text": "Primarily backend dev, basic React knowledge."}),

    # DevOps
    (student_ids[4], job_ids["devops"], {"ats_score": 0.89, "status": "shortlisted",
        "resume_filename": "rahul_devops_resume.pdf",
        "resume_text": "AWS certified, Terraform, Kubernetes, GitHub Actions pipelines."}),
    (student_ids[6], job_ids["devops"], {"ats_score": 0.765, "status": "applied",
        "resume_filename": "vikram_devops_resume.pdf",
        "resume_text": "2 years SRE, GCP, basic Terraform, on-call experience."}),

    # Intern
    (student_ids[1], job_ids["intern"], {"ats_score": 0.78, "status": "shortlisted",
        "resume_filename": "sneha_intern_resume.pdf",
        "resume_text": "3rd year CS student, Python, JavaScript, 1 internship."}),
    (student_ids[2], job_ids["intern"], {"ats_score": 0.65, "status": "applied",
        "resume_filename": "karan_intern_resume.pdf",
        "resume_text": "2nd year student, strong DSA, hackathon winner."}),
    (student_ids[3], job_ids["intern"], {"ats_score": 0.81, "status": "interview_scheduled",
        "resume_filename": "divya_intern_resume.pdf",
        "resume_text": "Final year, ML coursework, Python, Git, REST API projects."}),
    (student_ids[7], job_ids["intern"], {"ats_score": 0.60, "status": "applied",
        "resume_filename": "pooja_intern_resume.pdf",
        "resume_text": "2nd year, web development basics, React tutorial projects."}),
]

for student_id, job_id, app_data in applications:
    app_id = upsert_application(student_id, job_id, app_data)
    print(f"  Application {student_id[:8]}->{job_id[:8]}: {app_id[:8]} [{app_data['status']}]")

print("\nDone – mock data seeded successfully.")
