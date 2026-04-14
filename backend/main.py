import asyncio
from contextlib import asynccontextmanager
from config.db import get_db
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

from services.resume_parser import (
    extract_text_from_pdf,
    extract_urls,
    extract_username_from_url,
)
from api.auth import auth_router
from api.student import student_router
from api.recruiter import recruiter_router
from services.github_service import fetch_github_profile
from services.leetcode_service import fetch_leetcode_profile
from services.linkedin_service import fetch_linkedin_profile
from services.graph_builder import build_knowledge_graph
from agents.prescreen_agent import run_prescreen_analysis
from repositories.prescreen_repo import save_prescreen, get_prescreen
from orchestration import (
    generate_questions_for_interview,
    start_interview,
    get_next_turn,
    submit_code,
    end_interview,
)
from repositories.report_repo import get_report

@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_db()  # verify connection on startup
    yield

app = FastAPI(title="HireForce PreScreen", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

app.include_router(auth_router)
app.include_router(student_router)
app.include_router(recruiter_router)
@app.get("/paste-job-interview", response_class=HTMLResponse)
async def paste_job_interview(request: Request):
    return templates.TemplateResponse("paste_job_interview.html", {"request": request})


@app.get("/questions-preview", response_class=HTMLResponse)
async def questions_preview(request: Request):
    return templates.TemplateResponse("questions_preview.html", {"request": request})


@app.get("/take-interview", response_class=HTMLResponse)
async def take_interview(request: Request):
    return templates.TemplateResponse("take_interview.html", {"request": request})


@app.get("/interview-report", response_class=HTMLResponse)
async def interview_report(request: Request, report_id: str | None = None):
    return templates.TemplateResponse(
        "interview_report.html",
        {"request": request, "report_id": report_id},
    )


@app.get("/knowledge-graph", response_class=HTMLResponse)
async def knowledge_graph_page(request: Request):
    return templates.TemplateResponse("knowledge_graph.html", {"request": request})


# ---------- Orchestration API ----------


@app.post("/api/interviews/generate-questions")
async def api_generate_questions(
    prescreen_id: str = Form(...),
    job_description: str = Form(...),
    interview_date: str = Form(...),
    interview_time: str = Form(...),
):
    try:
        result = await generate_questions_for_interview(
            prescreen_id=prescreen_id,
            job_description=job_description,
            interview_date=interview_date,
            interview_time=interview_time,
        )
        return result
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/interviews/start")
async def api_start_interview(interview_id: str = Form(...)):
    try:
        return await start_interview(interview_id=interview_id)
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/sessions/{session_id}/turn")
async def api_turn(session_id: str, candidate_message: str = Form(...)):
    try:
        return await get_next_turn(session_id=session_id, candidate_message=candidate_message)
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/sessions/{session_id}/code")
async def api_submit_code(
    session_id: str,
    code: str = Form(...),
    language: str = Form("python"),
):
    try:
        return await submit_code(session_id=session_id, code=code, language=language)
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/sessions/{session_id}/end")
async def api_end_interview(
    session_id: str,
    recording_ref: str | None = Form(None),
):
    try:
        return await end_interview(session_id=session_id, recording_ref=recording_ref)
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/interviews/{interview_id}")
async def api_get_interview(interview_id: str):
    from repositories.interview_repo import get_interview as repo_get
    interview = repo_get(interview_id)
    if not interview:
        return JSONResponse(status_code=404, content={"error": "Interview not found"})
    return interview


@app.get("/api/reports/{report_id}")
async def api_get_report(report_id: str):
    report = get_report(report_id)
    if not report:
        return JSONResponse(status_code=404, content={"error": "Report not found"})
    return report


@app.get("/api/reports/{report_id}/prescreen")
async def api_get_report_prescreen(report_id: str):
    """
    Resolve report -> session -> interview -> prescreen and return the prescreen doc.
    Useful for the report screen to show prescreen context.
    """
    report = get_report(report_id)
    if not report:
        return JSONResponse(status_code=404, content={"error": "Report not found"})

    from repositories.session_repo import get_session as repo_get_session
    from repositories.interview_repo import get_interview as repo_get_interview

    session_id = report.get("session_id") or ""
    session = repo_get_session(session_id) if session_id else None
    if not session:
        return JSONResponse(status_code=404, content={"error": "Session not found for report"})

    interview_id = session.get("interview_id") or ""
    interview = repo_get_interview(interview_id) if interview_id else None
    if not interview:
        return JSONResponse(status_code=404, content={"error": "Interview not found for report"})

    prescreen_id = interview.get("prescreen_id") or ""
    prescreen = get_prescreen(prescreen_id) if prescreen_id else None
    if not prescreen:
        return JSONResponse(status_code=404, content={"error": "Prescreen not found for report"})

    return {"prescreen_id": prescreen_id, "prescreen": prescreen}


@app.get("/api/knowledge-graph/{prescreen_id}")
async def api_get_knowledge_graph(prescreen_id: str):
    """Fetch the knowledge graph for a prescreen result by prescreen_id."""
    prescreen = get_prescreen(prescreen_id)
    if not prescreen:
        return JSONResponse(
            status_code=404,
            content={"error": "Prescreen not found"},
        )
    graph = prescreen.get("graph")
    if graph is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Knowledge graph not found for this prescreen"},
        )
    return {"prescreen_id": prescreen_id, "graph": graph}


@app.post("/api/analyze")
async def analyze_candidate(
    resume: UploadFile | None = File(None),
    linkedin_url: str = Form(""),
    github_url: str = Form(""),
    leetcode_url: str = Form(""),
):
    try:
        return await _analyze_candidate(resume, linkedin_url, github_url, leetcode_url)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


async def _analyze_candidate(resume, linkedin_url, github_url, leetcode_url):
    resume_text = ""

    if resume and resume.filename:
        file_bytes = await resume.read()
        if resume.filename.lower().endswith(".pdf"):
            resume_text = extract_text_from_pdf(file_bytes)
            extracted = extract_urls(resume_text)
            if not linkedin_url and extracted["linkedin"]:
                linkedin_url = extracted["linkedin"]
            if not github_url and extracted["github"]:
                github_url = extracted["github"]
            if not leetcode_url and extracted["leetcode"]:
                leetcode_url = extracted["leetcode"]

    if not any([linkedin_url, github_url, leetcode_url]):
        return JSONResponse(
            status_code=400,
            content={
                "error": "Provide at least one profile URL or upload a resume containing profile links."
            },
        )

    github_username = extract_username_from_url(github_url, "github")
    leetcode_username = extract_username_from_url(leetcode_url, "leetcode")

    coros = {}
    if github_username:
        coros["github"] = fetch_github_profile(github_username)
    if leetcode_username:
        coros["leetcode"] = fetch_leetcode_profile(leetcode_username)
    if linkedin_url:
        coros["linkedin"] = fetch_linkedin_profile(linkedin_url)

    keys = list(coros.keys())
    results = await asyncio.gather(*coros.values(), return_exceptions=True)

    platform_data = {"github": {}, "leetcode": {}, "linkedin": {}}
    for key, result in zip(keys, results):
        platform_data[key] = {"error": str(result)} if isinstance(result, Exception) else result

    graph = build_knowledge_graph(
        platform_data["github"],
        platform_data["leetcode"],
        platform_data["linkedin"],
        resume_text,
    )

    analysis = await run_prescreen_analysis(
        platform_data["github"],
        platform_data["leetcode"],
        platform_data["linkedin"],
        resume_text,
    )

    urls = {
        "linkedin": linkedin_url,
        "github": github_url,
        "leetcode": leetcode_url,
    }
    prescreen_id = save_prescreen(
        urls=urls,
        platform_data=platform_data,
        graph=graph,
        analysis=analysis,
    )

    return {
        "prescreen_id": prescreen_id,
        "github": platform_data["github"],
        "leetcode": platform_data["leetcode"],
        "linkedin": platform_data["linkedin"],
        "graph": graph,
        "analysis": analysis,
        "urls": urls,
    }



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
