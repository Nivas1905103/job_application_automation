import os
import json
import smtplib
import time
import asyncio
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from parser import ResumeParser
from job_fetcher import JobFetcher
from matcher import ResumeMatcher
from auto_applier import AutoApplier

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
LOGS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(LOGS_DIR, exist_ok=True)

# Email configuration (Can be configured via ENV variables or default log service)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "nivasanmugam@gmail.com")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")

async def run_daily_automation():
    """
    Executes daily midnight automation (12:00 AM - 12:30 AM):
    1. Scans uploaded resume.
    2. Searches for live matching Cloud Support & Admin jobs in India & Worldwide.
    3. Auto-applies to all matched jobs.
    4. Sends summary email report to candidate.
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Daily Midnight Job Application Run...")

    # Find uploaded resume file in uploads directory or fall back to default profile
    uploaded_files = [os.path.join(UPLOADS_DIR, f) for f in os.listdir(UPLOADS_DIR) if f.endswith(('.pdf', '.docx', '.txt'))] if os.path.exists(UPLOADS_DIR) else []

    if uploaded_files:
        latest_resume = max(uploaded_files, key=os.path.getmtime)
        parser = ResumeParser(file_path=latest_resume)
        resume_data = parser.parse()
        resume_path = latest_resume
    else:
        # Default profile if resume not uploaded yet
        resume_path = None
        resume_data = {
            "name": "Cloud Operations Specialist",
            "email": "cloud.support.india@example.com",
            "phone": "+91 9876543210",
            "skills": ["AWS", "Azure", "Cloud Support", "Linux", "Systems Administration", "Docker", "Kubernetes", "Troubleshooting", "Networking", "IAM", "ITIL"],
            "experience_level": "Senior Cloud Support Engineer"
        }

    recipient_email = os.environ.get("CANDIDATE_EMAIL", resume_data.get("email") or "nivasanmugam@gmail.com")
    candidate_name = resume_data.get("name", "Nivas")

    # Fetch matching jobs in India & Global
    fetcher = JobFetcher()
    matcher = ResumeMatcher()
    applier = AutoApplier(resume_file_path=resume_path)

    keywords = resume_data.get("skills", []) + [
        "Azure Support Engineer", "Azure Administrator", "Azure Cloud Engineer",
        "Azure DevOps Support", "Azure Systems Admin", "Cloud Support Engineer",
        "Systems Administrator", "IT Infrastructure Admin"
    ]
    jobs = fetcher.search_jobs(keywords=keywords, location_filter="india", limit=50)

    applied_jobs = []
    for job in jobs:
        match_info = matcher.match_resume_to_job(resume_data, job)
        if match_info.get("match_score", 0) >= 50:
            result = await applier.apply_to_job(
                job=job,
                candidate_info=match_info.get("application_answers", {}),
                cover_letter=match_info.get("cover_letter", ""),
                headless=True
            )
            applied_jobs.append({
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "match_score": match_info.get("match_score"),
                "status": result.get("status")
            })

    # Prepare Email Summary Digest
    report_content = generate_email_report(candidate_name, recipient_email, applied_jobs)

    # Save JSON report log
    report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(os.path.join(LOGS_DIR, report_filename), "w", encoding="utf-8") as f:
        json.dump({
            "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "candidate_name": candidate_name,
            "recipient_email": recipient_email,
            "total_applied": len(applied_jobs),
            "jobs": applied_jobs
        }, f, indent=2)

    # Save HTML report file
    html_filename = f"daily_report_{datetime.now().strftime('%Y%m%d')}.html"
    with open(os.path.join(LOGS_DIR, html_filename), "w", encoding="utf-8") as f:
        f.write(report_content)

    # Save latest HTML report file
    with open(os.path.join(LOGS_DIR, "latest_daily_report.html"), "w", encoding="utf-8") as f:
        f.write(report_content)

    # Send Email Report
    send_email_notification(recipient_email, candidate_name, len(applied_jobs), report_content)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Midnight Automation Finished! Total applied: {len(applied_jobs)}")

def generate_email_report(name: str, email: str, applied_jobs: list) -> str:
    date_str = datetime.now().strftime("%B %d, %Y")

    jobs_html = ""
    for idx, j in enumerate(applied_jobs, 1):
        jobs_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{idx}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;"><b>{j['title']}</b><br><small style="color: #666;">{j['company']}</small></td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{j['location']}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;"><span style="background: #e0e7ff; color: #4338ca; padding: 3px 8px; border-radius: 12px; font-weight: bold;">{j['match_score']}% Match</span></td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; color: #059669; font-weight: bold;">{j['status']}</td>
        </tr>
        """

    if not applied_jobs:
        jobs_html = "<tr><td colspan='5' style='padding: 15px; text-align: center; color: #666;'>No new matching jobs found today.</td></tr>"

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 20px; text-align: center; border-radius: 10px 10px 0 0; color: white;">
            <h2 style="margin: 0;">AutoApply AI Daily Job Report</h2>
            <p style="margin: 5px 0 0; font-size: 0.9em;">Midnight Run Summary - {date_str}</p>
        </div>
        <div style="background: #ffffff; padding: 20px; border: 1px solid #e5e7eb; border-radius: 0 0 10px 10px;">
            <p>Hi <b>{name}</b>,</p>
            <p>Your daily midnight job application task ran successfully between 12:00 AM and 12:30 AM.</p>

            <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
                <span style="font-size: 2em; font-weight: bold; color: #4f46e5;">{len(applied_jobs)}</span><br>
                <span style="color: #6b7280; font-size: 0.9em;">Total India Cloud Jobs Applied Today</span>
            </div>

            <h3>Applied Job Applications Summary:</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.85em;">
                <thead>
                    <tr style="background: #f9fafb; text-align: left;">
                        <th style="padding: 8px;">#</th>
                        <th style="padding: 8px;">Job Title & Company</th>
                        <th style="padding: 8px;">Location</th>
                        <th style="padding: 8px;">Match</th>
                        <th style="padding: 8px;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {jobs_html}
                </tbody>
            </table>

            <p style="margin-top: 25px; font-size: 0.85em; color: #6b7280; text-align: center;">
                This process will automatically run every day at 12:00 AM until stopped.<br>
                AutoApply AI Engine • India Cloud Support & Admin Automation
            </p>
        </div>
    </body>
    </html>
    """

def send_email_notification(to_email: str, name: str, job_count: int, html_body: str):
    """
    Sends email via SMTP or logs output if SMTP credentials not configured.
    """
    if SENDER_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚀 Daily Job Application Report: {job_count} Jobs Applied ({datetime.now().strftime('%b %d')})"
            msg["From"] = SENDER_EMAIL
            msg["To"] = to_email
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
            print(f"Email sent successfully to {to_email}")
        except Exception as e:
            print(f"SMTP send error (logged to file): {e}")
    else:
        print(f"[Email Notification Logged] Sent report for {job_count} jobs to {to_email}")

if __name__ == "__main__":
    asyncio.run(run_daily_automation())
