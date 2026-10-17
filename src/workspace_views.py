"""Builds the data of each read from the workspace: lists, details and rankings.

Pure: it only reads a finished `Workspace`. It ranks nothing (`pipeline` did) and knows no HTTP
(`src/api/` maps these results to responses). A missing value is `None` (MIS-001).
Implements LST-001, LST-002, JOB-002, JOB-003, CND-001 to CND-003, RNK-003, REC-001, MIS-001,
MIS-002, ERR-001, DEC-015 and DEC-020.
"""

from dataclasses import dataclass

from src.attributes import distinct_countries, distinct_employers, last_job
from src.records import (
    CalculatedAttributes,
    CvFacts,
    Document,
    Failure,
    Job,
    Recommendation,
    Workspace,
)


class NotFoundError(LookupError):
    """An ID that matches no job description or candidate of the workspace (DEC-020)."""


@dataclass(frozen=True)
class JobSummary:
    """A job description in a list: its ID and title (LST-001)."""

    job_id: str
    title: str


@dataclass(frozen=True)
class JobDetail:
    """A job description with its raw text (JOB-003)."""

    job_id: str
    title: str
    text: str


@dataclass(frozen=True)
class CandidateSummary:
    """A candidate in a list: the file name and the name, `None` when not extracted (LST-002)."""

    candidate_id: str
    name: str | None


@dataclass(frozen=True)
class ExtractedAttributes:
    """The extracted attributes of a candidate (EXT-002 to EXT-010).

    `last_job` carries `end` and `is_current` so that the end can be shown as "Present" or as
    unknown (DEC-015).
    """

    name: str | None
    current_title: str | None
    skills: list[str]
    city: str | None
    country: str | None
    highest_degree: str | None
    countries: list[str]
    employers: list[str]
    last_job: Job | None


@dataclass(frozen=True)
class RankedCandidate:
    """A candidate in the ranking of one job description (JOB-002, RNK-003, REC-001).

    `extracted`, `calculated` and `recommendation` are `None` when the LLM call for them failed.
    """

    candidate_id: str
    name: str | None
    score: float | None
    recommendation: Recommendation | None
    extracted: ExtractedAttributes | None
    calculated: CalculatedAttributes | None


@dataclass(frozen=True)
class CandidateDetail:
    """A candidate with the raw CV and the attributes (CND-001, CND-002)."""

    candidate_id: str
    name: str | None
    text: str
    extracted: ExtractedAttributes | None
    calculated: CalculatedAttributes | None


@dataclass(frozen=True)
class RankedJob:
    """A job description in the ranking of one candidate. It has no recommendation (CND-003)."""

    job_id: str
    title: str
    score: float | None


def _title(job: Document) -> str:
    """Return the title of a job description: its first line."""
    return next(iter(job.text.splitlines()), "").strip()


def _find_job(workspace: Workspace, job_id: str) -> Document:
    """Return the job description with this ID, or raise `NotFoundError`."""
    for job in workspace.jobs:
        if job.doc_id == job_id:
            return job
    raise NotFoundError(f"No job description '{job_id}'")


def _find_cv(workspace: Workspace, candidate_id: str) -> Document:
    """Return the CV with this ID, or raise `NotFoundError`."""
    for cv in workspace.cvs:
        if cv.doc_id == candidate_id:
            return cv
    raise NotFoundError(f"No candidate '{candidate_id}'")


def _name(workspace: Workspace, candidate_id: str) -> str | None:
    """Return the extracted name, or `None` when the CV has no facts or no name (MIS-002)."""
    facts = workspace.facts.get(candidate_id)
    return None if facts is None else facts.name


def _extracted(facts: CvFacts | None) -> ExtractedAttributes | None:
    """Return the extracted attributes of a CV, or `None` when its extraction failed."""
    if facts is None:
        return None
    return ExtractedAttributes(
        name=facts.name,
        current_title=facts.current_title,
        skills=facts.skills,
        city=facts.city,
        country=facts.country,
        highest_degree=facts.highest_degree,
        countries=distinct_countries(facts.jobs),
        employers=distinct_employers(facts.jobs),
        last_job=last_job(facts.jobs),
    )


def job_list(workspace: Workspace) -> list[JobSummary]:
    """Return the job descriptions with ID and title (LST-001)."""
    return [JobSummary(job.doc_id, _title(job)) for job in workspace.jobs]


def candidate_list(workspace: Workspace) -> list[CandidateSummary]:
    """Return every candidate with ID and name, also one whose extraction failed (LST-002)."""
    return [CandidateSummary(cv.doc_id, _name(workspace, cv.doc_id)) for cv in workspace.cvs]


def job_detail(workspace: Workspace, job_id: str) -> JobDetail:
    """Return one job description with its raw text (JOB-003).

    Args:
        workspace: The finished workspace.
        job_id: The file name of the job description.

    Returns:
        The ID, the title and the text as read.

    Raises:
        NotFoundError: If no job description has this ID (DEC-020).
    """
    job = _find_job(workspace, job_id)
    return JobDetail(job.doc_id, _title(job), job.text)


def ranked_candidates(workspace: Workspace, job_id: str) -> list[RankedCandidate]:
    """Return all candidates for a job description, best match first (JOB-002, RNK-003, REC-001).

    Args:
        workspace: The finished workspace.
        job_id: The file name of the job description.

    Returns:
        One entry per candidate, in the order the pipeline ranked them.

    Raises:
        NotFoundError: If no job description has this ID.
    """
    _find_job(workspace, job_id)
    return [
        RankedCandidate(
            candidate_id=candidate_id,
            name=_name(workspace, candidate_id),
            score=score,
            recommendation=workspace.recommendations.get((job_id, candidate_id)),
            extracted=_extracted(workspace.facts.get(candidate_id)),
            calculated=workspace.attributes.get(candidate_id),
        )
        for candidate_id, score in workspace.ranked_candidates[job_id]
    ]


def candidate_detail(workspace: Workspace, candidate_id: str) -> CandidateDetail:
    """Return one candidate with the raw CV and the attributes (CND-001, CND-002).

    Args:
        workspace: The finished workspace.
        candidate_id: The file name of the CV.

    Returns:
        The ID, the name, the text as read and the attributes.

    Raises:
        NotFoundError: If no CV has this ID.
    """
    cv = _find_cv(workspace, candidate_id)
    return CandidateDetail(
        candidate_id=cv.doc_id,
        name=_name(workspace, candidate_id),
        text=cv.text,
        extracted=_extracted(workspace.facts.get(candidate_id)),
        calculated=workspace.attributes.get(candidate_id),
    )


def ranked_jobs(workspace: Workspace, candidate_id: str) -> list[RankedJob]:
    """Return all job descriptions for a candidate, best match first (CND-003).

    Args:
        workspace: The finished workspace.
        candidate_id: The file name of the CV.

    Returns:
        One entry per job description, in the order the pipeline ranked them.

    Raises:
        NotFoundError: If no CV has this ID.
    """
    _find_cv(workspace, candidate_id)
    titles = {job.doc_id: _title(job) for job in workspace.jobs}
    return [
        RankedJob(job_id, titles[job_id], score)
        for job_id, score in workspace.ranked_jobs[candidate_id]
    ]


def failure_list(workspace: Workspace) -> list[Failure]:
    """Return the failed LLM calls, each with the item and the cause (ERR-001)."""
    return list(workspace.failures)
