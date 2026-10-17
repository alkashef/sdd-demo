"""Typed, frozen records of the in-memory data model (design section 3).

Holds data only. It does no calculation (`attributes` does) and reads nothing (`file_reader` does).
Implements DEC-005, DEC-009 and DEC-015; a missing value is `None` (MIS-001).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    """A plain-text CV or job description. `doc_id` is the file name (DEC-009)."""

    doc_id: str
    text: str


@dataclass(frozen=True)
class YearMonth:
    """A calendar month."""

    year: int
    month: int


@dataclass(frozen=True)
class Job:
    """One job in a CV.

    A job with an `end` has ended. With no `end`, `is_current` true means "Present" and false
    means the end is unknown (DEC-015).
    """

    title: str | None
    employer: str | None
    city: str | None
    country: str | None
    start: YearMonth | None
    end: YearMonth | None
    is_current: bool
    description: str | None


@dataclass(frozen=True)
class Education:
    """One education entry in a CV."""

    degree: str | None
    university: str | None
    major: str | None
    graduated: YearMonth | None


@dataclass(frozen=True)
class CvFacts:
    """The facts the LLM extracted from one CV. Every field except the lists may be `None`."""

    name: str | None
    current_title: str | None
    skills: list[str]
    city: str | None
    country: str | None
    highest_degree: str | None
    jobs: list[Job]
    education: list[Education]


@dataclass(frozen=True)
class CalculatedAttributes:
    """The attributes the code calculates from `CvFacts`. Each may be `None` (MIS-001)."""

    total_months: int | None
    job_count: int | None
    average_job_months: float | None
    gaps: list[int] | None
    months_since_graduation: int | None
    currently_employed: bool | None


@dataclass(frozen=True)
class Recommendation:
    """Whether to interview a candidate for a job, with the reason."""

    interview: bool
    reason: str


@dataclass(frozen=True)
class Failure:
    """A failed LLM call. `item_id` is a file name, or `<job ID> + <CV ID>` for a pair."""

    item_id: str
    cause: str


@dataclass(frozen=True)
class Workspace:
    """Everything one run produced, held in memory.

    `facts` and `attributes` have no entry for a CV whose extraction failed. A score is `None`
    for an item with no vector. Each ranked list is (ID, score), best first.
    """

    cvs: list[Document]
    jobs: list[Document]
    facts: dict[str, CvFacts]
    attributes: dict[str, CalculatedAttributes]
    ranked_candidates: dict[str, list[tuple[str, float | None]]]
    ranked_jobs: dict[str, list[tuple[str, float | None]]]
    recommendations: dict[tuple[str, str], Recommendation]
    failures: list[Failure]
