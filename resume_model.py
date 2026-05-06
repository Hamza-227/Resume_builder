"""
resume_model.py
---------------
Pydantic v2 data models for all resume sections.
Falls back to dataclasses if pydantic is not installed.

New in v4:
  - Project.link  (optional URL shown as clickable "View Project" in PDF)
  - All dummy data is fully generic — no real person / company names
"""

from __future__ import annotations
from typing import List, Optional

try:
    from pydantic import BaseModel, field_validator, model_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    from dataclasses import dataclass, field, asdict
    import json
    PYDANTIC_AVAILABLE = False

    class _BaseModel:
        def model_dump(self):
            return asdict(self)
        @classmethod
        def model_validate(cls, data: dict):
            return cls(**data)
        def model_dump_json(self):
            return json.dumps(self.model_dump())

    BaseModel = _BaseModel


# ─────────────────────────────────────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────────────────────────────────────

if PYDANTIC_AVAILABLE:

    class ContactInfo(BaseModel):
        name: str
        phone: str
        city: str
        email: str
        linkedin:  Optional[str] = None
        github:    Optional[str] = None
        website:   Optional[str] = None
        portfolio: Optional[str] = None

        @field_validator("email")
        @classmethod
        def email_valid(cls, v: str) -> str:
            if "@" not in v:
                raise ValueError("Invalid email address")
            return v.strip()

        @field_validator("name")
        @classmethod
        def name_not_empty(cls, v: str) -> str:
            if not v.strip():
                raise ValueError("Name cannot be empty")
            return v.strip()

    class ExperienceEntry(BaseModel):
        title:      str
        company:    str
        start_date: str
        end_date:   str          # "Present" if current
        location:   str
        bullets:    List[str]    # 2–4 achievement bullets

        @field_validator("bullets")
        @classmethod
        def at_least_one_bullet(cls, v: List[str]) -> List[str]:
            cleaned = [b.strip() for b in v if b.strip()]
            if not cleaned:
                raise ValueError("At least one bullet point is required")
            return cleaned

    class EducationEntry(BaseModel):
        institution: str
        degree:      str
        start_date:  str
        end_date:    str

    class Project(BaseModel):
        name:        str
        description: str             # 2–3 metric-driven sentences
        link:        Optional[str] = None   # ← NEW: GitHub / live URL

    class Skills(BaseModel):
        languages_tools: List[str]
        techniques:      List[str]
        soft_skills:     List[str]

    class Certification(BaseModel):
        name: str
        link: Optional[str] = None

    class Resume(BaseModel):
        contact:       ContactInfo
        summary:       str
        experience:    List[ExperienceEntry]
        education:     List[EducationEntry]
        projects:      List[Project]
        skills:        Skills
        certifications: List[Certification]

        @field_validator("summary")
        @classmethod
        def summary_not_empty(cls, v: str) -> str:
            if not v.strip():
                raise ValueError("Summary cannot be empty")
            return v.strip()

        @model_validator(mode="after")
        def at_least_one_experience(self) -> "Resume":
            if not self.experience:
                raise ValueError("At least one experience entry is required")
            return self

else:
    # ── Dataclass fallback ────────────────────────────────────────────────────
    @dataclass
    class ContactInfo(_BaseModel):
        name: str = ""
        phone: str = ""
        city: str = ""
        email: str = ""
        linkedin:  Optional[str] = None
        github:    Optional[str] = None
        website:   Optional[str] = None
        portfolio: Optional[str] = None

    @dataclass
    class ExperienceEntry(_BaseModel):
        title:      str = ""
        company:    str = ""
        start_date: str = ""
        end_date:   str = ""
        location:   str = ""
        bullets: List[str] = field(default_factory=list)

    @dataclass
    class EducationEntry(_BaseModel):
        institution: str = ""
        degree:      str = ""
        start_date:  str = ""
        end_date:    str = ""

    @dataclass
    class Project(_BaseModel):
        name:        str = ""
        description: str = ""
        link:        Optional[str] = None   # ← NEW

    @dataclass
    class Skills(_BaseModel):
        languages_tools: List[str] = field(default_factory=list)
        techniques:      List[str] = field(default_factory=list)
        soft_skills:     List[str] = field(default_factory=list)

    @dataclass
    class Certification(_BaseModel):
        name: str = ""
        link: Optional[str] = None

    @dataclass
    class Resume(_BaseModel):
        contact:        ContactInfo      = field(default_factory=ContactInfo)
        summary:        str              = ""
        experience:     List[ExperienceEntry] = field(default_factory=list)
        education:      List[EducationEntry]  = field(default_factory=list)
        projects:       List[Project]         = field(default_factory=list)
        skills:         Skills                = field(default_factory=Skills)
        certifications: List[Certification]   = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# SAMPLE RESUME  ── 100 % generic dummy data, no real people or companies
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_RESUME = Resume(
    contact=ContactInfo(
        name      = "Jordan Smith",
        phone     = "+1 (555) 234-5678",
        city      = "Austin, TX",
        email     = "jordan.smith@email.com",
        linkedin  = "https://linkedin.com/in/yourprofile",
        github    = "https://github.com/yourusername",
        website   = "https://yourwebsite.com",
        portfolio = "https://yourportfolio.com",
    ),
    summary=(
        "Senior Software Engineer with 7+ years of experience designing and delivering "
        "scalable backend systems and data pipelines. Proficient in Python, cloud-native "
        "architecture, and machine learning integration. Passionate about building "
        "high-impact products and mentoring engineering teams."
    ),
    experience=[
        ExperienceEntry(
            title      = "Senior Software Engineer",
            company    = "Horizon Tech Inc.",
            start_date = "Mar 2022",
            end_date   = "Present",
            location   = "Austin, TX",
            bullets=[
                "Designed and deployed a real-time data processing pipeline handling 5M+ events/day, "
                "reducing system latency by 42% and saving $180K/year in infrastructure costs.",
                "Led a cross-functional team of 6 engineers to migrate monolithic services to "
                "microservices on AWS, improving deployment frequency from bi-weekly to daily.",
                "Implemented automated CI/CD workflows using GitHub Actions and Terraform, cutting "
                "release cycle time by 60% and eliminating manual deployment errors.",
            ],
        ),
        ExperienceEntry(
            title      = "Software Engineer",
            company    = "Nexus Digital Solutions",
            start_date = "Jun 2019",
            end_date   = "Feb 2022",
            location   = "Dallas, TX",
            bullets=[
                "Built RESTful APIs serving 2M+ daily active users with 99.9% uptime using "
                "Django and PostgreSQL on Google Cloud Platform.",
                "Developed an ML-based recommendation engine increasing user engagement by 35% "
                "and contributing to $1.2M additional annual revenue.",
                "Mentored 3 junior engineers through code reviews and weekly 1-on-1 sessions, "
                "reducing bug escape rate to production by 28%.",
            ],
        ),
        ExperienceEntry(
            title      = "Junior Developer",
            company    = "Bright Code Agency",
            start_date = "Aug 2017",
            end_date   = "May 2019",
            location   = "Houston, TX",
            bullets=[
                "Developed and maintained 12 client-facing web applications using React and "
                "Node.js, improving average page load speed by 50%.",
                "Automated regression test suites using Pytest and Selenium, achieving 85% "
                "test coverage and reducing QA cycles by 3 days per sprint.",
            ],
        ),
    ],
    education=[
        EducationEntry(
            institution = "University of Texas at Austin",
            degree      = "M.S. Computer Science — Specialization in AI & Systems",
            start_date  = "Sep 2015",
            end_date    = "May 2017",
        ),
        EducationEntry(
            institution = "State University College of Engineering",
            degree      = "B.S. Computer Science",
            start_date  = "Aug 2011",
            end_date    = "May 2015",
        ),
    ],
    projects=[
        Project(
            name        = "OpenMetrics Dashboard",
            description = (
                "Built an open-source real-time analytics dashboard using FastAPI, React, and "
                "ClickHouse, enabling teams to monitor KPIs with sub-second query response. "
                "Reached 1,200 GitHub stars within 3 months of release."
            ),
            link = "https://github.com/yourusername/openmetrics-dashboard",
        ),
        Project(
            name        = "AutoResume AI",
            description = (
                "Developed an AI-powered resume tailoring tool using GPT-4 and Python that "
                "automatically rewrites bullet points to match job descriptions, increasing "
                "interview callback rates by 40% in user testing across 200+ applicants."
            ),
            link = "https://github.com/yourusername/autoresume-ai",
        ),
        Project(
            name        = "CloudCost Optimizer",
            description = (
                "Created a CLI tool that analyzes AWS billing data and recommends right-sizing "
                "actions, helping 3 companies reduce cloud spend by an average of 31% "
                "in the first month of deployment."
            ),
            link = None,   # no link — still renders cleanly
        ),
    ],
    skills=Skills(
        languages_tools = [
            "Python", "JavaScript", "SQL", "Go",
            "React", "Django", "FastAPI", "Docker", "Kubernetes",
            "AWS", "GCP", "Terraform", "PostgreSQL", "Redis",
        ],
        techniques = [
            "Microservices Architecture", "CI/CD", "Machine Learning",
            "REST API Design", "System Design", "Data Pipelines",
            "Agile / Scrum", "Test-Driven Development",
        ],
        soft_skills = [
            "Technical Leadership", "Cross-functional Collaboration",
            "Mentorship", "Problem Solving", "Clear Communication",
        ],
    ),
    certifications=[
        Certification(
            name = "AWS Certified Solutions Architect – Associate",
            link = "https://aws.amazon.com/certification/certified-solutions-architect-associate/",
        ),
        Certification(
            name = "Google Professional Cloud Developer",
            link = "https://cloud.google.com/certification/cloud-developer",
        ),
        Certification(
            name = "Certified Kubernetes Administrator (CKA)",
            link = "https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/",
        ),
    ],
)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def resume_to_dict(resume: "Resume") -> dict:
    if PYDANTIC_AVAILABLE:
        return resume.model_dump()
    from dataclasses import asdict
    return asdict(resume)


def resume_from_dict(data: dict) -> "Resume":
    if PYDANTIC_AVAILABLE:
        return Resume.model_validate(data)
    contact        = ContactInfo(**data["contact"])
    experience     = [ExperienceEntry(**e) for e in data.get("experience", [])]
    education      = [EducationEntry(**e)  for e in data.get("education", [])]
    projects       = [Project(**p)         for p in data.get("projects", [])]
    skills         = Skills(**data["skills"])
    certifications = [Certification(**c)   for c in data.get("certifications", [])]
    return Resume(
        contact=contact, summary=data.get("summary", ""),
        experience=experience, education=education,
        projects=projects, skills=skills, certifications=certifications,
    )
