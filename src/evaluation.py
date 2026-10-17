"""Parses the two evaluation files and checks a finished workspace against them (DEC-017).

Pure and synchronous. It reads no file (`file_reader` does), calls no service (`pipeline` and
`llm_client` do) and prints nothing (`main.py` does). The report holds counts, job description
IDs and pass or fail, never CV content.
Implements NFR-004 and NFR-005.
"""

import json
import re
from dataclasses import dataclass
from enum import StrEnum

from src.records import Job, Workspace, YearMonth


class _Format(StrEnum):
    """The fixed text formats of the two evaluation files."""

    TRUTH_HEADER = "job_id\tcv_id"
    FILE_SUFFIX = ".txt"
    MONTH = r"(\d{4})-(0[1-9]|1[0-2])"


class EvaluationFileError(ValueError):
    """An evaluation file has a wrong format. The run stops before any LLM call."""


@dataclass(frozen=True)
class EvaluationLimits:
    """The limits of the two checks (design section 2.3)."""

    top_k: int
    min_relevant_in_top_k: int
    min_date_match_percent: int


@dataclass(frozen=True)
class GoldJob:
    """One reviewed job of a CV, as written in `gold_jobs.json`."""

    start: YearMonth
    end: YearMonth | None
    is_current: bool


@dataclass(frozen=True)
class JobRanking:
    """How many labeled-relevant CVs one job description has among its top K."""

    job_id: str
    relevant_in_top_k: int


@dataclass(frozen=True)
class RankingCheck:
    """The result of NFR-004. It fails when no job description has a label."""

    top_k: int
    minimum: int
    jobs: list[JobRanking]

    @property
    def passed(self) -> bool:
        """Return True when there is a job to check and every job reaches the minimum."""
        return bool(self.jobs) and all(job.relevant_in_top_k >= self.minimum for job in self.jobs)


@dataclass(frozen=True)
class DateCheck:
    """The result of NFR-005. It fails when there is no gold job."""

    matched: int
    total: int
    min_percent: int

    @property
    def percent(self) -> float:
        """Return the share of matched gold jobs, from 0 to 100 (0 when there is none)."""
        return 100 * self.matched / self.total if self.total else 0.0

    @property
    def passed(self) -> bool:
        """Return True when there is a gold job and the matched share reaches the minimum."""
        return self.total > 0 and 100 * self.matched >= self.min_percent * self.total


@dataclass(frozen=True)
class EvaluationReport:
    """Both checks."""

    ranking: RankingCheck
    dates: DateCheck

    @property
    def passed(self) -> bool:
        """Return True when both checks pass."""
        return self.ranking.passed and self.dates.passed


def parse_ground_truth(text: str) -> dict[str, set[str]]:
    """Parse `ground_truth.tsv` into the relevant CV file names per job description file name.

    Args:
        text: A `job_id<TAB>cv_id` header, then one labeled-relevant pair per line.

    Returns:
        Job description file name to the set of relevant CV file names. The dataset IDs get a
        `.txt` suffix to match the file names.

    Raises:
        EvaluationFileError: If the header is wrong or a line is not two non-empty fields.
    """
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines or lines[0].strip() != _Format.TRUTH_HEADER:
        raise EvaluationFileError("Ground truth file must start with a 'job_id<TAB>cv_id' header.")
    relevant: dict[str, set[str]] = {}
    columns = len(_Format.TRUTH_HEADER.split("\t"))
    for number, line in enumerate(lines[1:], start=2):
        fields = line.split("\t")
        if len(fields) != columns or not all(field.strip() for field in fields):
            raise EvaluationFileError(f"Ground truth line {number} must be 'job_id<TAB>cv_id'.")
        job_id, cv_id = (field.strip() + _Format.FILE_SUFFIX for field in fields)
        relevant.setdefault(job_id, set()).add(cv_id)
    return relevant


def _month(value: object, where: str) -> YearMonth:
    match = re.fullmatch(_Format.MONTH, value) if isinstance(value, str) else None
    if match is None:
        raise EvaluationFileError(f"Gold file {where} must be a month written YYYY-MM.")
    return YearMonth(int(match.group(1)), int(match.group(2)))


def _gold_job(entry: object, where: str) -> GoldJob:
    if not isinstance(entry, dict):
        raise EvaluationFileError(f"Gold file {where} must be an object.")
    is_current = entry.get("is_current")
    if not isinstance(is_current, bool):
        raise EvaluationFileError(f"Gold file {where} 'is_current' must be true or false.")
    end = entry.get("end")
    return GoldJob(
        _month(entry.get("start"), f"{where} 'start'"),
        None if end is None else _month(end, f"{where} 'end'"),
        is_current,
    )


def parse_gold_jobs(text: str) -> dict[str, list[GoldJob]]:
    """Parse `gold_jobs.json` into the reviewed jobs per CV file name.

    Args:
        text: A JSON object whose `cvs` maps each CV file name to a list of jobs, each with
            `start`, `end` (a month or null) and `is_current`.

    Returns:
        CV file name to its gold jobs.

    Raises:
        EvaluationFileError: If the text is not JSON or does not have this shape.
    """
    try:
        document = json.loads(text)
    except json.JSONDecodeError as err:
        raise EvaluationFileError("Gold file is not valid JSON.") from err
    cvs = document.get("cvs") if isinstance(document, dict) else None
    if not isinstance(cvs, dict):
        raise EvaluationFileError("Gold file must be an object with a 'cvs' object.")
    gold: dict[str, list[GoldJob]] = {}
    for cv_id, entries in cvs.items():
        if not isinstance(entries, list):
            raise EvaluationFileError(f"Gold file entry '{cv_id}' must be a list of jobs.")
        gold[cv_id] = [_gold_job(entry, f"entry '{cv_id}'") for entry in entries]
    return gold


def check_ranking(
    workspace: Workspace, relevant: dict[str, set[str]], limits: EvaluationLimits
) -> RankingCheck:
    """Count the labeled-relevant CVs among the top K of each job description (NFR-004).

    Args:
        workspace: The finished workspace, with the candidates ranked per job description.
        relevant: The relevant CV file names per job description file name.
        limits: The K and the minimum.

    Returns:
        One entry per job description that is both labeled and ranked, ordered by ID.
    """
    jobs = [
        JobRanking(
            job_id,
            sum(
                cv_id in labels for cv_id, _ in workspace.ranked_candidates[job_id][: limits.top_k]
            ),
        )
        for job_id, labels in sorted(relevant.items())
        if job_id in workspace.ranked_candidates
    ]
    return RankingCheck(limits.top_k, limits.min_relevant_in_top_k, jobs)


def _same_dates(job: Job, gold: GoldJob) -> bool:
    return (job.start, job.end, job.is_current) == (gold.start, gold.end, gold.is_current)


def check_dates(
    workspace: Workspace, gold: dict[str, list[GoldJob]], limits: EvaluationLimits
) -> DateCheck:
    """Count the gold jobs whose dates the extraction reproduced (NFR-005).

    A gold job matches when the extracted CV has a job with the same start, end and current
    marker. A CV with no extracted facts counts all its gold jobs as misses, and extra extracted
    jobs are not penalized.

    Args:
        workspace: The finished workspace.
        gold: The reviewed jobs per CV file name.
        limits: The minimum match percent.

    Returns:
        The matched and total counts.
    """
    matched = 0
    total = 0
    for cv_id, gold_jobs in gold.items():
        facts = workspace.facts.get(cv_id)
        extracted = facts.jobs if facts else []
        total += len(gold_jobs)
        matched += sum(
            any(_same_dates(job, gold_job) for job in extracted) for gold_job in gold_jobs
        )
    return DateCheck(matched, total, limits.min_date_match_percent)


def evaluate(
    workspace: Workspace,
    relevant: dict[str, set[str]],
    gold: dict[str, list[GoldJob]],
    limits: EvaluationLimits,
) -> EvaluationReport:
    """Run both checks on a finished workspace."""
    return EvaluationReport(
        check_ranking(workspace, relevant, limits), check_dates(workspace, gold, limits)
    )


def _verdict(passed: bool) -> str:
    return "PASS" if passed else "FAIL"


def _ranking_lines(check: RankingCheck) -> list[str]:
    lines = [f"NFR-004: {_verdict(check.passed)}"]
    if not check.jobs:
        lines.append("  no labeled job description to check")
    lines.extend(
        f"  {job.job_id}: {job.relevant_in_top_k} of top {check.top_k} relevant "
        f"(need {check.minimum})"
        for job in check.jobs
    )
    return lines


def _date_lines(check: DateCheck) -> list[str]:
    lines = [f"NFR-005: {_verdict(check.passed)}"]
    if check.total == 0:
        lines.append("  no gold jobs to check")
    else:
        lines.append(
            f"  {check.matched} of {check.total} gold jobs matched "
            f"({check.percent:.1f}%, need {check.min_percent}%)"
        )
    return lines


def format_report(report: EvaluationReport) -> str:
    """Return the report as plain text: counts and pass or fail per check, no CV content."""
    return "\n".join([*_ranking_lines(report.ranking), *_date_lines(report.dates)])
