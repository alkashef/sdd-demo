"""Calculates the CAL attributes and derives the EXT-007 to EXT-009 values from extracted facts.

Pure: today's month is passed in. It does not extract facts (`extraction` does) and does not rank.
Implements CAL-001 to CAL-005, CAL-007 to CAL-010, EXT-007 to EXT-009, MIS-001, DEC-005, DEC-015.
Rules: design section 3. A job with no start cannot be placed in time, so it counts as a bad job.
"""

from dataclasses import dataclass

from src.records import CalculatedAttributes, CvFacts, Education, Job, YearMonth


@dataclass(frozen=True)
class _Span:
    """The months a job covers, as month numbers. `end` is `None` when it is unknown."""

    start: int
    end: int | None
    is_current: bool


def _month_number(value: YearMonth) -> int:
    """Return a number that grows by one for each calendar month."""
    return value.year * 12 + value.month


def _span(job: Job, now: int) -> _Span | None:
    """Return the job's span, or `None` when the job is bad (CAL-010)."""
    if job.start is None:
        return None
    start = _month_number(job.start)
    is_current = job.is_current and job.end is None
    end = _month_number(job.end) if job.end is not None else None
    if is_current:
        end = now
    if start > now or (end is not None and (end < start or end > now)):
        return None
    return _Span(start, end, is_current)


def _spans(jobs: list[Job], now: int) -> list[_Span] | None:
    """Return every job's span, or `None` when there is no job or any job is bad."""
    spans = [_span(job, now) for job in jobs]
    if not spans or None in spans:
        return None
    return [span for span in spans if span is not None]


def _known_ends(spans: list[_Span] | None) -> list[tuple[int, int]] | None:
    """Return (start, end) per job in start order, or `None` when any end is unknown (CAL-009)."""
    if spans is None or any(span.end is None for span in spans):
        return None
    return sorted((span.start, span.end) for span in spans if span.end is not None)


def _gaps(ordered: list[tuple[int, int]]) -> list[int]:
    """Return the months between jobs, ignoring overlaps (CAL-004)."""
    gaps: list[int] = []
    latest_end = ordered[0][1]
    for start, end in ordered[1:]:
        if start - latest_end > 1:
            gaps.append(start - latest_end - 1)
        latest_end = max(latest_end, end)
    return gaps


def _average_months(ordered: list[tuple[int, int]]) -> float:
    """Return the mean job duration, both months counted (CAL-003, CAL-008)."""
    return sum(end - start + 1 for start, end in ordered) / len(ordered)


def _currently_employed(spans: list[_Span]) -> bool | None:
    """Return whether the job with the latest start is current (CAL-007)."""
    latest = max(spans, key=lambda span: span.start)
    if latest.is_current:
        return True
    return None if latest.end is None else False


def _months_since_graduation(education: list[Education], now: int) -> int | None:
    """Return the months since the most recent graduation, both months counted (CAL-005)."""
    dates = [_month_number(entry.graduated) for entry in education if entry.graduated is not None]
    if not dates or max(dates) > now:
        return None
    return now - max(dates) + 1


def calculate_attributes(facts: CvFacts, today: YearMonth) -> CalculatedAttributes:
    """Calculate the attributes of a CV (CAL-001 to CAL-005, CAL-007 to CAL-010).

    Args:
        facts: The extracted facts of one CV.
        today: The current month. "Present" means this month (CAL-008).

    Returns:
        The attributes. One that cannot be determined is `None`, never a guess (MIS-001).
    """
    now = _month_number(today)
    spans = _spans(facts.jobs, now)
    ordered = _known_ends(spans)
    return CalculatedAttributes(
        total_months=None if spans is None else now - min(s.start for s in spans) + 1,
        job_count=len(facts.jobs),
        average_job_months=None if ordered is None else _average_months(ordered),
        gaps=None if ordered is None else _gaps(ordered),
        months_since_graduation=_months_since_graduation(facts.education, now),
        currently_employed=None if spans is None else _currently_employed(spans),
    )


def distinct_countries(jobs: list[Job]) -> list[str]:
    """Return the countries of the jobs, each once, in order of first appearance (EXT-007)."""
    return list(dict.fromkeys(job.country for job in jobs if job.country))


def distinct_employers(jobs: list[Job]) -> list[str]:
    """Return the employers of the jobs, each once, in order of first appearance (EXT-008)."""
    return list(dict.fromkeys(job.employer for job in jobs if job.employer))


def last_job(jobs: list[Job]) -> Job | None:
    """Return the job with the latest start, or `None` when no job has a start (EXT-009)."""
    dated = [(_month_number(job.start), job) for job in jobs if job.start is not None]
    if not dated:
        return None
    return max(dated, key=lambda pair: pair[0])[1]
