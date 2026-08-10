import os
import shutil
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from parser import ResumeParser
from job_fetcher import JobFetcher
from matcher import ResumeMatcher
from auto_applier import AutoApplier

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI(
    title="Automated Job Application Suite",
    description="Resume Parser, AI Job Matcher, and Automated Application Engine for India & Worldwide Remote Jobs."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Global state in memory for active user session
CURRENT_RESUME = {
    "file_path": None,
    "parsed_data": {
        "name": "Cloud Operations Specialist",
        "email": "cloud.support.india@example.com",
        "phone": "+91 9876543210",
        "linkedin": "https://linkedin.com/in/cloud-support-engineer-india",
        "github": "https://github.com/cloud-admin-india",
        "skills": ["AWS", "Azure", "Cloud Support", "Linux", "Systems Administration", "Docker", "Kubernetes", "Troubleshooting", "Networking", "IAM", "Terraform", "Python", "ITIL", "Incident Management"],
        "experience_level": "Senior Cloud Support Engineer",
        "raw_text": "Senior Cloud Support Engineer & Systems Administrator in India with 5+ years experience in AWS, Azure, Linux troubleshooting, networking, Docker, Kubernetes, ITIL incident management, and automated cloud infrastructure."
    }
}

fetcher = JobFetcher()
matcher = ResumeMatcher()

@app.get("/", response_class=HTMLResponse)
def index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Automated Job Application Suite Server</h1>"

@app.get("/api/profile")
def get_profile():
    return JSONResponse({
        "status": "success",
        "has_resume": CURRENT_RESUME["file_path"] is not None,
        "file_name": os.path.basename(CURRENT_RESUME["file_path"]) if CURRENT_RESUME["file_path"] else "Default Demo Profile",
        "profile": CURRENT_RESUME["parsed_data"]
    })

@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    filename = file.filename
    file_path = os.path.join(UPLOADS_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Parse resume
    parser = ResumeParser(file_path=file_path)
    parsed_info = parser.parse()

    CURRENT_RESUME["file_path"] = file_path
    CURRENT_RESUME["parsed_data"] = parsed_info

    return JSONResponse({
        "status": "success",
        "message": "Resume uploaded & parsed successfully",
        "file_name": filename,
        "profile": parsed_info
    })

@app.get("/api/search-jobs")
def search_jobs(location: str = "india", query: str = "", limit: int = 25):
    keywords = [k.strip() for k in query.split(",") if k.strip()] if query else None

    # If no specific query is provided, use parsed resume skills + Cloud Support & Admin role keywords
    if not keywords and CURRENT_RESUME["parsed_data"].get("skills"):
        resume_skills = CURRENT_RESUME["parsed_data"].get("skills", [])
        keywords = resume_skills + ["Cloud Support Engineer", "Cloud Admin", "Systems Administrator"]

    jobs = fetcher.search_jobs(keywords=keywords, location_filter=location, limit=limit)

    # Match each job with current resume
    matched_results = []
    for job in jobs:
        match_info = matcher.match_resume_to_job(CURRENT_RESUME["parsed_data"], job)
        combined = {**job, **match_info}
        matched_results.append(combined)

    # Sort jobs by highest match score first
    matched_results.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    return JSONResponse({
        "status": "success",
        "total_jobs": len(matched_results),
        "location_filter": location,
        "active_keywords": keywords[:10] if keywords else ["Cloud Support", "Cloud Admin"],
        "jobs": matched_results
    })

@app.post("/api/apply-job")
async def apply_job(job_id: str = Form(...), job_data_json: str = Form(...)):
    try:
        job = json.loads(job_data_json)
        applier = AutoApplier(resume_file_path=CURRENT_RESUME["file_path"])
        match_info = matcher.match_resume_to_job(CURRENT_RESUME["parsed_data"], job)
        cover_letter = match_info.get("cover_letter", "")
        answers = match_info.get("application_answers", {})

        result = await applier.apply_to_job(
            job=job,
            candidate_info=answers,
            cover_letter=cover_letter,
            headless=True
        )

        return JSONResponse({
            "status": "success",
            "result": result
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/batch-apply")
async def batch_apply(location: str = Form("all"), min_score: int = Form(70), query: str = Form("")):
    keywords = [k.strip() for k in query.split(",") if k.strip()] if query else None
    jobs = fetcher.search_jobs(keywords=keywords, location_filter=location, limit=30)
    applier = AutoApplier(resume_file_path=CURRENT_RESUME["file_path"])

    applied_list = []
    for job in jobs:
        match_info = matcher.match_resume_to_job(CURRENT_RESUME["parsed_data"], job)
        score = match_info.get("match_score", 0)

        if score >= min_score:
            res = await applier.apply_to_job(
                job=job,
                candidate_info=match_info.get("application_answers", {}),
                cover_letter=match_info.get("cover_letter", ""),
                headless=True
            )
            applied_list.append(res)

    return JSONResponse({
        "status": "success",
        "total_applied": len(applied_list),
        "applications": applied_list
    })

@app.get("/api/history")
def get_application_history():
    applier = AutoApplier()
    history = applier.get_history()
    return JSONResponse({
        "status": "success",
        "total": len(history),
        "history": history
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
