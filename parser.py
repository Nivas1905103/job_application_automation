import re
import os
from typing import Dict, Any, List
from pypdf import PdfReader
import docx

class ResumeParser:
    """
    Parses resume files (.pdf, .docx, .txt, .md) and extracts key candidate profile metrics.
    """

    COMMON_SKILLS = [
        # Cloud & Systems Administration
        "Cloud Support", "Systems Administration", "AWS", "Azure", "GCP", "Linux", "Windows Server",
        "DevOps", "Docker", "Kubernetes", "Terraform", "Ansible", "Shell Scripting", "Bash", "Powershell",
        "Networking", "DNS", "VPN", "TCP/IP", "Firewall", "IAM", "CloudWatch", "Datadog", "Nagios",
        "ITIL", "ServiceDesk", "Jira", "Incident Management", "SLA Management", "Troubleshooting",
        "Customer Support", "Technical Support", "Active Directory", "VMware", "CI/CD",
        # Software & Data
        "Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI", "Express", "SQL", "PostgreSQL", "MongoDB",
        "REST API", "Git", "Agile", "Scrum", "Communication"
    ]

    def __init__(self, file_path: str = None, text_content: str = None):
        self.file_path = file_path
        self.raw_text = text_content or ""
        if file_path and os.path.exists(file_path):
            self.raw_text = self._extract_text_from_file(file_path)

    def _extract_text_from_file(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        text = ""

        try:
            if ext == ".pdf":
                reader = PdfReader(file_path)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            elif ext == ".docx":
                doc = docx.Document(file_path)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            else:
                # Text or Markdown file
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
        except Exception as e:
            text = f"Error reading file: {str(e)}"

        return text

    def parse(self) -> Dict[str, Any]:
        """
        Parses raw text and returns structured dictionary of resume info.
        """
        email = self._extract_email()
        phone = self._extract_phone()
        linkedin = self._extract_linkedin()
        github = self._extract_github()
        skills = self._extract_skills()
        exp_level = self._determine_experience_level()

        # Clean name from first line or email handle
        lines = [line.strip() for line in self.raw_text.splitlines() if line.strip()]
        name = lines[0] if lines else "Candidate"
        if len(name) > 40 or "@" in name or "resume" in name.lower():
            name = email.split("@")[0].title() if email else "Job Applicant"

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "github": github,
            "skills": skills,
            "experience_level": exp_level,
            "raw_text": self.raw_text,
            "summary": lines[1:4] if len(lines) > 3 else lines
        }

    def _extract_email(self) -> str:
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', self.raw_text)
        return match.group(0) if match else ""

    def _extract_phone(self) -> str:
        match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', self.raw_text)
        return match.group(0) if match else ""

    def _extract_linkedin(self) -> str:
        match = re.search(r'(https?://)?(www\.)?linkedin\.com/in/[\w\-]+/?', self.raw_text, re.IGNORECASE)
        return match.group(0) if match else ""

    def _extract_github(self) -> str:
        match = re.search(r'(https?://)?(www\.)?github\.com/[\w\-]+/?', self.raw_text, re.IGNORECASE)
        return match.group(0) if match else ""

    def _extract_skills(self) -> List[str]:
        found_skills = []
        text_upper = self.raw_text.upper()
        for skill in self.COMMON_SKILLS:
            # Case insensitive exact word match
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, self.raw_text, re.IGNORECASE):
                found_skills.append(skill)
        return sorted(list(set(found_skills)))

    def _determine_experience_level(self) -> str:
        text_lower = self.raw_text.lower()
        if "lead" in text_lower or "principal" in text_lower or "architect" in text_lower or "head of" in text_lower:
            return "Senior / Lead"
        elif "senior" in text_lower or "sr." in text_lower or "5+" in text_lower or "7+" in text_lower:
            return "Senior"
        elif "mid" in text_lower or "3+" in text_lower or "4+" in text_lower:
            return "Mid-Level"
        elif "junior" in text_lower or "entry" in text_lower or "intern" in text_lower or "graduate" in text_lower:
            return "Junior / Entry"
        return "Mid-Senior"
