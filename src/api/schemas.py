"""The JSON response models of the API (design section 4).

Only describes the shape of each response. It computes nothing (`workspace_views` does) and knows
no route (the routers do). A missing value is `None`, which is `null` in the JSON (MIS-001). The
last job carries `end` and `is_current` (DEC-015). Implements LST-001, LST-002, JOB-002, JOB-003,
CND-001 to CND-003, ERR-001, MIS-001, DEC-015 and DEC-020.
"""

from pydantic import BaseModel, ConfigDict, Field


class _Response(BaseModel):
    """Base of the response models: reads the frozen dataclasses of `workspace_views`."""

    model_config = ConfigDict(from_attributes=True)


class YearMonthOut(_Response):
    """A calendar month."""

    year: int
    month: int


class JobOut(_Response):
    """One job of a CV. `end` is null for a current job and for an unknown end (DEC-015)."""

    title: str | None
    employer: str | None
    city: str | None
    country: str | None
    start: YearMonthOut | None
    end: YearMonthOut | None
    is_current: bool
    description: str | None


class ExtractedAttributesOut(_Response):
    """The extracted attributes of a candidate (EXT-002 to EXT-010)."""

    name: str | None
    current_title: str | None
    skills: list[str]
    city: str | None
    country: str | None
    highest_degree: str | None
    countries: list[str]
    employers: list[str]
    last_job: JobOut | None


class CalculatedAttributesOut(_Response):
    """The calculated attributes of a candidate (CAL requirements)."""

    total_months: int | None
    job_count: int | None
    average_job_months: float | None
    gaps: list[int] | None
    months_since_graduation: int | None
    currently_employed: bool | None


class RecommendationOut(_Response):
    """Whether to interview a candidate for a job, with the reason (REC-001)."""

    interview: bool
    reason: str


class JobSummaryOut(_Response):
    """A job description in a list (LST-001)."""

    id: str = Field(validation_alias="job_id")
    title: str


class JobDetailOut(_Response):
    """A job description with its raw text (JOB-003)."""

    id: str = Field(validation_alias="job_id")
    title: str
    text: str


class CandidateSummaryOut(_Response):
    """A candidate in a list (LST-002)."""

    id: str = Field(validation_alias="candidate_id")
    name: str | None


class RankedCandidateOut(_Response):
    """A candidate in the ranking of one job description (JOB-002, RNK-003, REC-001)."""

    id: str = Field(validation_alias="candidate_id")
    name: str | None
    score: float | None
    recommendation: RecommendationOut | None
    extracted: ExtractedAttributesOut | None
    calculated: CalculatedAttributesOut | None


class CandidateDetailOut(_Response):
    """A candidate with the raw CV and the attributes (CND-001, CND-002)."""

    id: str = Field(validation_alias="candidate_id")
    name: str | None
    text: str
    extracted: ExtractedAttributesOut | None
    calculated: CalculatedAttributesOut | None


class RankedJobOut(_Response):
    """A job description in the ranking of one candidate (CND-003)."""

    id: str = Field(validation_alias="job_id")
    title: str
    score: float | None


class FailureOut(_Response):
    """A failed LLM call: the item and the cause (ERR-001)."""

    item_id: str
    cause: str
