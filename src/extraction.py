"""Builds the extraction user text and turns a validated reply into `CvFacts`.

Pure. It does not call the LLM (`llm_client` does), read the system prompt (`file_reader` does) or
calculate anything (`attributes` does). It imports `LlmOutputError` from `ports`, which holds
exceptions and protocols only.
Implements EXT-002 to EXT-004, EXT-006, EXT-009, EXT-010, MIS-001, NFR-001, DEC-005, DEC-015,
DEC-016.
"""

from src.llm_schemas import CvFactsReply, EducationReply, JobReply
from src.ports import LlmOutputError
from src.prompt_data import Tag, wrap
from src.records import CvFacts, Document, Education, Job, YearMonth


def extraction_user_text(cv: Document) -> str:
    """Return the user text of the extraction request: the CV as tagged, untrusted data."""
    return wrap(Tag.CV, cv.text)


def facts_from_reply(reply: CvFactsReply) -> CvFacts:
    """Map a validated extraction reply to the facts of a CV.

    Args:
        reply: The reply the LLM returned for one CV.

    Returns:
        The facts. A `null` in the reply is `None` (MIS-001).

    Raises:
        LlmOutputError: If a job is marked current and also has an end date (DEC-015). The raw
            output is the reply as JSON.
    """
    for number, job in enumerate(reply.jobs, start=1):
        if job.is_current and job.end is not None:
            raise LlmOutputError(
                f"Extraction reply marks job {number} as current and also gives an end date",
                reply.model_dump_json(),
            )
    return CvFacts(
        name=reply.name,
        current_title=reply.current_title,
        skills=list(reply.skills),
        city=reply.city,
        country=reply.country,
        highest_degree=reply.highest_degree,
        jobs=[_job(job) for job in reply.jobs],
        education=[_education(entry) for entry in reply.education],
    )


def _job(reply: JobReply) -> Job:
    """Map one job of the reply to a `Job`."""
    return Job(
        title=reply.title,
        employer=reply.employer,
        city=reply.city,
        country=reply.country,
        start=_year_month(reply.start),
        end=_year_month(reply.end),
        is_current=reply.is_current,
        description=reply.description,
    )


def _education(reply: EducationReply) -> Education:
    """Map one education entry of the reply to an `Education`."""
    return Education(
        degree=reply.degree,
        university=reply.university,
        major=reply.major,
        graduated=_year_month(reply.graduated),
    )


def _year_month(text: str | None) -> YearMonth | None:
    """Turn a `YYYY-MM` text, already checked by the schema, into a `YearMonth`."""
    if text is None:
        return None
    year, month = text.split("-")
    return YearMonth(int(year), int(month))
