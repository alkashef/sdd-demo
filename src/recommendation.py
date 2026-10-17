"""Builds the recommendation user text and turns a validated reply into a `Recommendation`.

Pure. It does not call the LLM (`llm_client` does) or read the system prompt (`file_reader` does).
The request carries the job description and the candidate facts, never the name or the address.
Implements REC-001, NFR-001, DEC-006, DEC-016.
"""

import json

from src.llm_schemas import RecommendationReply
from src.prompt_data import Tag, wrap
from src.records import CvFacts, Document, Education, Job, Recommendation, YearMonth


def recommendation_user_text(job_description: Document, facts: CvFacts) -> str:
    """Return the user text of the recommendation request.

    Args:
        job_description: The job description to match against.
        facts: The extracted facts of one candidate. Name, city and country are left out (DEC-006).

    Returns:
        The tagged job description, then the tagged facts as JSON (DEC-016).
    """
    facts_json = json.dumps(_facts_data(facts), indent=2, ensure_ascii=False)
    return (
        f"{wrap(Tag.JOB_DESCRIPTION, job_description.text)}\n"
        f"{wrap(Tag.CANDIDATE_FACTS, facts_json)}"
    )


def recommendation_from_reply(reply: RecommendationReply) -> Recommendation:
    """Map a validated recommendation reply to a `Recommendation`."""
    return Recommendation(interview=reply.interview, reason=reply.reason)


def _facts_data(facts: CvFacts) -> dict[str, object]:
    """Return the facts the LLM may see, as plain JSON data."""
    return {
        "current_title": facts.current_title,
        "skills": facts.skills,
        "highest_degree": facts.highest_degree,
        "jobs": [_job_data(job) for job in facts.jobs],
        "education": [_education_data(entry) for entry in facts.education],
    }


def _job_data(job: Job) -> dict[str, object]:
    """Return one job as JSON data, with `is_current` beside `end` (DEC-015)."""
    return {
        "title": job.title,
        "employer": job.employer,
        "city": job.city,
        "country": job.country,
        "start": _month_text(job.start),
        "end": _month_text(job.end),
        "is_current": job.is_current,
        "description": job.description,
    }


def _education_data(entry: Education) -> dict[str, object]:
    """Return one education entry as JSON data."""
    return {
        "degree": entry.degree,
        "university": entry.university,
        "major": entry.major,
        "graduated": _month_text(entry.graduated),
    }


def _month_text(month: YearMonth | None) -> str | None:
    """Return a month as `YYYY-MM`, or `None` when unknown."""
    if month is None:
        return None
    return f"{month.year:04d}-{month.month:02d}"
