import unittest
import os
from parser import ResumeParser
from job_fetcher import JobFetcher
from matcher import ResumeMatcher
from auto_applier import AutoApplier

class TestJobAutomationSuite(unittest.TestCase):

    def setUp(self):
        self.sample_resume_text = """
        ALEX MERCER
        Senior Software Engineer
        Email: alex.mercer.tech@example.com | Phone: +91 9876543210
        LinkedIn: https://linkedin.com/in/alexmercer-dev | GitHub: https://github.com/alexmercer-dev

        SUMMARY:
        Results-driven Senior Software Engineer with 6+ years of experience in Python, React, Node.js, FastAPI, PostgreSQL, and AWS.

        SKILLS:
        Python, JavaScript, TypeScript, React, Node.js, FastAPI, PostgreSQL, Docker, AWS, Git, REST API
        """

    def test_resume_parser(self):
        parser = ResumeParser(text_content=self.sample_resume_text)
        data = parser.parse()

        self.assertEqual(data["email"], "alex.mercer.tech@example.com")
        self.assertEqual(data["phone"], "+91 9876543210")
        self.assertIn("Python", data["skills"])
        self.assertIn("React", data["skills"])
        self.assertIn("FastAPI", data["skills"])

    def test_job_fetcher(self):
        fetcher = JobFetcher()
        jobs = fetcher.search_jobs(location_filter="all", limit=5)
        self.assertGreater(len(jobs), 0)

        # Check job schema
        first_job = jobs[0]
        self.assertIn("id", first_job)
        self.assertIn("title", first_job)
        self.assertIn("company", first_job)
        self.assertIn("remote_type", first_job)

    def test_resume_matcher(self):
        parser = ResumeParser(text_content=self.sample_resume_text)
        resume_data = parser.parse()

        mock_job = {
            "id": "test_101",
            "title": "Python & React Engineer",
            "company": "TechCorp Global",
            "remote_type": "India Remote",
            "tags": ["Python", "React", "PostgreSQL"],
            "description": "Looking for Python and React developers for remote India position."
        }

        matcher = ResumeMatcher()
        match_info = matcher.match_resume_to_job(resume_data, mock_job)

        self.assertGreaterEqual(match_info["match_score"], 70)
        self.assertIn("Python", match_info["matching_skills"])
        self.assertIn("Dear Hiring Manager", match_info["cover_letter"])

    def test_auto_applier_history(self):
        applier = AutoApplier()
        initial_history = applier.get_history()

        test_record = {
            "job_id": "test_hist_1",
            "title": "Full Stack Dev",
            "company": "Demo Systems",
            "url": "https://example.com/apply",
            "applied_at": "2026-08-10 23:50:00",
            "status": "Submitted",
            "notes": "Unit test submission"
        }
        applier.record_application(test_record)

        updated_history = applier.get_history()
        self.assertGreater(len(updated_history), len(initial_history))
        self.assertEqual(updated_history[0]["job_id"], "test_hist_1")

    def test_cloud_support_india_jobs(self):
        cloud_resume = """
        PRIYA SHARMA
        Cloud Support Engineer & Systems Administrator
        Email: priya.sharma.cloud@example.com | Phone: +91 9123456789
        Skills: AWS, Azure, Linux, Cloud Support, Systems Administration, Docker, Troubleshooting, IAM, Networking
        """
        parser = ResumeParser(text_content=cloud_resume)
        data = parser.parse()
        self.assertIn("Cloud Support", data["skills"])
        self.assertIn("AWS", data["skills"])

        fetcher = JobFetcher()
        india_jobs = fetcher.search_jobs(keywords=data["skills"], location_filter="india", limit=5)
        self.assertGreater(len(india_jobs), 0)
        self.assertIn("India", india_jobs[0]["remote_type"] + india_jobs[0]["location"])

if __name__ == "__main__":
    unittest.main()
