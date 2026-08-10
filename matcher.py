import re
from typing import Dict, Any, List

class ResumeMatcher:
    """
    Evaluates resume fit against job listings, calculates match score %,
    identifies matched & missing skills, and auto-generates custom application answers & cover letters.
    """

    def match_resume_to_job(self, resume_data: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
        candidate_skills = set([s.lower() for s in resume_data.get("skills", [])])
        job_description = (job.get("description", "") + " " + job.get("title", "")).lower()
        job_tags = set([t.lower() for t in job.get("tags", [])])

        # Extract skills present in job
        job_keywords = set()
        for skill in ResumeParser.COMMON_SKILLS if 'ResumeParser' in globals() else candidate_skills:
            if re.search(r'\b' + re.escape(skill.lower()) + r'\b', job_description):
                job_keywords.add(skill.lower())
        job_keywords.update(job_tags)

        if not job_keywords:
            job_keywords = candidate_skills.copy() or {"python", "javascript", "react", "sql"}

        # Calculate matching skills
        matching = candidate_skills.intersection(job_keywords)
        missing = job_keywords.difference(candidate_skills)

        # Base score calculation
        if job_keywords:
            match_percentage = int((len(matching) / len(job_keywords)) * 100)
        else:
            match_percentage = 75

        # Boost score if title matches experience or role keywords
        title_words = set(job.get("title", "").lower().split())
        resume_text_lower = resume_data.get("raw_text", "").lower()
        for word in title_words:
            if len(word) > 3 and word in resume_text_lower:
                match_percentage += 5

        match_percentage = min(98, max(50, match_percentage))

        # Generate cover letter & preset answers
        cover_letter = self.generate_cover_letter(resume_data, job, list(matching))
        answers = self.generate_application_answers(resume_data, job)

        return {
            "job_id": job.get("id"),
            "job_title": job.get("title"),
            "company": job.get("company"),
            "match_score": match_percentage,
            "matching_skills": sorted([s.title() for s in matching]),
            "missing_skills": sorted([s.title() for s in missing]),
            "cover_letter": cover_letter,
            "application_answers": answers
        }

    def generate_cover_letter(self, resume_data: Dict[str, Any], job: Dict[str, Any], matched_skills: List[str]) -> str:
        name = resume_data.get("name", "Applicant")
        email = resume_data.get("email", "")
        phone = resume_data.get("phone", "")
        skills_str = ", ".join([s.title() for s in matched_skills[:5]]) or "software engineering and modern tech stacks"
        exp_level = resume_data.get("experience_level", "experienced")

        return f"""Dear Hiring Manager at {job.get('company', 'the team')},

I am writing to express my strong interest in the {job.get('title', 'Role')} position ({job.get('remote_type', 'Remote')}). With my background as a {exp_level} professional and expertise in {skills_str}, I am confident in my ability to make an immediate positive impact.

In my recent projects, I have focused on building robust, performant systems and delivering high-quality solutions. The opportunity at {job.get('company')} aligns perfectly with my skills and career goals, particularly regarding {job.get('category', 'technology')} and modern software workflows.

Key Highlights of My Qualifications:
- Proven experience with {skills_str}.
- Strong problem-solving abilities and a track record of driving impactful results.
- Self-driven remote collaboration and proactive communication skills.

I look forward to discussing how my experience and passion for technical excellence align with the needs of your team at {job.get('company')}.

Sincerely,
{name}
Email: {email}
Phone: {phone}
"""

    def generate_application_answers(self, resume_data: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, str]:
        name = resume_data.get("name", "Applicant")
        skills = ", ".join(resume_data.get("skills", ["software development"])[:4])

        return {
            "first_name": name.split()[0] if " " in name else name,
            "last_name": name.split()[-1] if " " in name and len(name.split()) > 1 else "Candidate",
            "email": resume_data.get("email", "candidate@example.com"),
            "phone": resume_data.get("phone", "+91 9876543210"),
            "linkedin": resume_data.get("linkedin", "https://linkedin.com/in/candidate"),
            "github": resume_data.get("github", "https://github.com/candidate"),
            "website": resume_data.get("github", "https://github.com/candidate"),
            "work_authorization": "Yes, I am authorized to work remotely.",
            "notice_period": "Immediate / 15-30 Days",
            "salary_expectation": "Negotiable / Market Competitive",
            "why_hire_me": f"I bring proven expertise in {skills}, combined with strong remote work discipline and alignment with {job.get('company', 'your company')}'s mission.",
            "years_of_experience": "4-6 Years"
        }
