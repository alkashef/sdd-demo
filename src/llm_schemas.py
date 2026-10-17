"""The reply shapes the LLM must return, as `pydantic` models (design section 3, LLM contract).

The SDK validates a reply against these. It does not map a reply to records (`extraction` does).
Every field is required and may be `null`, because the LLM must say "unknown" rather than guess.
Implements EXT-002 to EXT-004, EXT-006, EXT-009, EXT-010, MIS-001, DEC-011, DEC-015.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

type YearMonthText = Annotated[str, StringConstraints(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]


class _Reply(BaseModel):
    """Base of the reply models: an unknown field is rejected."""

    model_config = ConfigDict(extra="forbid")


class JobReply(_Reply):
    """One job in a CV. A date is `YYYY-MM`, or `null` when the CV gives no month (DEC-015)."""

    title: str | None
    employer: str | None
    city: str | None
    country: str | None
    start: YearMonthText | None
    end: YearMonthText | None
    is_current: bool
    description: str | None


class EducationReply(_Reply):
    """One education entry in a CV."""

    degree: str | None
    university: str | None
    major: str | None
    graduated: YearMonthText | None


class CvFactsReply(_Reply):
    """The facts of one CV (EXT-002 to EXT-010)."""

    name: str | None
    current_title: str | None
    skills: list[str]
    city: str | None
    country: str | None
    highest_degree: str | None
    jobs: list[JobReply]
    education: list[EducationReply]
