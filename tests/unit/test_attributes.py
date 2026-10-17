import pytest

from src.attributes import (
    calculate_attributes,
    distinct_countries,
    distinct_employers,
    last_job,
)
from src.records import CvFacts, Education, Job, YearMonth

TODAY = YearMonth(2026, 10)


def job(
    start: YearMonth | None,
    end: YearMonth | None,
    *,
    is_current: bool = False,
    employer: str | None = None,
    country: str | None = None,
    title: str | None = None,
) -> Job:
    return Job(
        title=title,
        employer=employer,
        city=None,
        country=country,
        start=start,
        end=end,
        is_current=is_current,
        description=None,
    )


def facts(jobs: list[Job], education: list[Education] | None = None) -> CvFacts:
    return CvFacts(
        name=None,
        current_title=None,
        skills=[],
        city=None,
        country=None,
        highest_degree=None,
        jobs=jobs,
        education=education or [],
    )


def graduated(year: int, month: int) -> Education:
    return Education(degree=None, university=None, major=None, graduated=YearMonth(year, month))


def ex_001_jobs() -> list[Job]:
    return [
        job(YearMonth(2018, 1), YearMonth(2019, 5)),
        job(YearMonth(2019, 6), YearMonth(2021, 12)),
        job(YearMonth(2022, 1), None, is_current=True),
    ]


def ex_003_jobs() -> list[Job]:
    return [*ex_001_jobs()[:2], job(YearMonth(2022, 1), None)]


def test_cal_001_total_employment_period_ex_001() -> None:
    assert calculate_attributes(facts(ex_001_jobs()), TODAY).total_months == 106


def test_cal_002_job_count_ex_001() -> None:
    assert calculate_attributes(facts(ex_001_jobs()), TODAY).job_count == 3


def test_cal_003_average_time_per_job_ex_001() -> None:
    average = calculate_attributes(facts(ex_001_jobs()), TODAY).average_job_months
    assert average == pytest.approx(106 / 3)


def test_cal_004_no_gap_ex_001() -> None:
    assert calculate_attributes(facts(ex_001_jobs()), TODAY).gaps == []


def test_cal_004_gap_between_jobs() -> None:
    jobs = [
        job(YearMonth(2020, 5), YearMonth(2020, 9)),
        job(YearMonth(2018, 1), YearMonth(2018, 5)),
        job(YearMonth(2018, 8), YearMonth(2019, 12)),
    ]
    assert calculate_attributes(facts(jobs), TODAY).gaps == [2, 4]


def test_cal_004_overlap_gives_no_gap() -> None:
    jobs = [
        job(YearMonth(2018, 1), YearMonth(2019, 12)),
        job(YearMonth(2018, 3), YearMonth(2018, 4)),
        job(YearMonth(2019, 6), YearMonth(2020, 1)),
    ]
    assert calculate_attributes(facts(jobs), TODAY).gaps == []


def test_cal_005_months_since_graduation_ex_002() -> None:
    attributes = calculate_attributes(facts([], [graduated(2018, 5)]), TODAY)
    assert attributes.months_since_graduation == 102


def test_cal_005_uses_most_recent_graduation() -> None:
    education = [graduated(2010, 6), graduated(2018, 5)]
    assert calculate_attributes(facts([], education), TODAY).months_since_graduation == 102


def test_cal_007_currently_employed_ex_001() -> None:
    assert calculate_attributes(facts(ex_001_jobs()), TODAY).currently_employed is True


def test_cal_007_last_job_with_end_is_not_current() -> None:
    jobs = [job(YearMonth(2018, 1), YearMonth(2019, 5))]
    assert calculate_attributes(facts(jobs), TODAY).currently_employed is False


def test_cal_007_latest_job_decides_not_list_order() -> None:
    jobs = [
        job(YearMonth(2022, 1), None, is_current=True),
        job(YearMonth(2018, 1), YearMonth(2019, 5)),
    ]
    assert calculate_attributes(facts(jobs), TODAY).currently_employed is True


def test_cal_008_present_is_current_month_and_both_months_counted() -> None:
    jobs = [job(YearMonth(2026, 10), None, is_current=True)]
    attributes = calculate_attributes(facts(jobs), TODAY)
    assert (attributes.total_months, attributes.average_job_months) == (1, 1.0)


def test_cal_008_job_in_a_single_month_lasts_one_month() -> None:
    jobs = [job(YearMonth(2020, 3), YearMonth(2020, 3))]
    assert calculate_attributes(facts(jobs), TODAY).average_job_months == 1.0


def test_cal_009_unknown_end_gives_not_available_ex_003() -> None:
    attributes = calculate_attributes(facts(ex_003_jobs()), TODAY)
    assert (
        attributes.job_count,
        attributes.total_months,
        attributes.average_job_months,
        attributes.gaps,
        attributes.currently_employed,
    ) == (3, 106, None, None, None)


def test_cal_010_bad_job_dates_ex_004() -> None:
    jobs = [
        job(YearMonth(2018, 1), YearMonth(2019, 5)),
        job(YearMonth(2019, 6), YearMonth(2019, 3)),
    ]
    attributes = calculate_attributes(facts(jobs), TODAY)
    assert (
        attributes.job_count,
        attributes.total_months,
        attributes.average_job_months,
        attributes.gaps,
        attributes.currently_employed,
    ) == (2, None, None, None, None)


def test_cal_010_future_graduation_ex_004() -> None:
    attributes = calculate_attributes(facts([], [graduated(2030, 5)]), TODAY)
    assert attributes.months_since_graduation is None


def test_cal_010_future_graduation_among_others_gives_not_available() -> None:
    education = [graduated(2018, 5), graduated(2030, 5)]
    assert calculate_attributes(facts([], education), TODAY).months_since_graduation is None


@pytest.mark.parametrize(
    "bad_job",
    [
        job(YearMonth(2026, 11), None, is_current=True),
        job(YearMonth(2026, 1), YearMonth(2026, 11)),
        job(None, YearMonth(2020, 1)),
    ],
)
def test_cal_010_future_or_missing_job_date_gives_not_available(bad_job: Job) -> None:
    jobs = [job(YearMonth(2018, 1), YearMonth(2019, 5)), bad_job]
    attributes = calculate_attributes(facts(jobs), TODAY)
    assert (attributes.total_months, attributes.currently_employed) == (None, None)


def test_cal_010_bad_graduation_leaves_job_attributes_unchanged() -> None:
    attributes = calculate_attributes(facts(ex_001_jobs(), [graduated(2030, 5)]), TODAY)
    assert attributes.total_months == 106


def test_ext_007_distinct_job_countries() -> None:
    jobs = [
        job(None, None, country="Egypt"),
        job(None, None, country=None),
        job(None, None, country="Spain"),
        job(None, None, country="Egypt"),
    ]
    assert distinct_countries(jobs) == ["Egypt", "Spain"]


def test_ext_008_distinct_employers() -> None:
    jobs = [
        job(None, None, employer="Acme"),
        job(None, None, employer="Acme"),
        job(None, None, employer="Globex"),
        job(None, None, employer=None),
    ]
    assert distinct_employers(jobs) == ["Acme", "Globex"]


def test_ext_009_last_job_is_latest_start() -> None:
    jobs = [
        job(YearMonth(2019, 6), None, title="middle"),
        job(YearMonth(2022, 1), None, title="latest"),
        job(YearMonth(2018, 1), None, title="first"),
        job(None, None, title="undated"),
    ]
    latest = last_job(jobs)
    assert latest is not None
    assert latest.title == "latest"


def test_ext_009_no_jobs_gives_no_last_job() -> None:
    assert last_job([]) is None


def test_mis_001_missing_values_stay_none() -> None:
    attributes = calculate_attributes(facts([]), TODAY)
    assert (
        attributes.total_months,
        attributes.average_job_months,
        attributes.gaps,
        attributes.months_since_graduation,
        attributes.currently_employed,
    ) == (None, None, None, None, None)
