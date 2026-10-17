import json

import pytest

from src.evaluation import (
    EvaluationFileError,
    EvaluationLimits,
    GoldJob,
    check_dates,
    check_ranking,
    evaluate,
    format_report,
    parse_gold_jobs,
    parse_ground_truth,
)
from src.records import CvFacts, Job, Workspace, YearMonth

LIMITS = EvaluationLimits(top_k=3, min_relevant_in_top_k=2, min_date_match_percent=90)
CV_SENTENCE = "Invented private sentence about Zed Quux"


def _job(start: tuple[int, int], end: tuple[int, int] | None, *, current: bool = False) -> Job:
    return Job(
        title=CV_SENTENCE,
        employer=CV_SENTENCE,
        city=None,
        country=None,
        start=YearMonth(*start),
        end=YearMonth(*end) if end else None,
        is_current=current,
        description=CV_SENTENCE,
    )


def _facts(jobs: list[Job]) -> CvFacts:
    return CvFacts(CV_SENTENCE, None, [], None, None, None, jobs, [])


def _gold(start: tuple[int, int], end: tuple[int, int] | None, *, current: bool = False) -> GoldJob:
    return GoldJob(YearMonth(*start), YearMonth(*end) if end else None, current)


def _workspace(
    ranked: dict[str, list[str]] | None = None, facts: dict[str, CvFacts] | None = None
) -> Workspace:
    ranked_candidates: dict[str, list[tuple[str, float | None]]] = {
        job_id: [(cv_id, 1.0 - index / 10) for index, cv_id in enumerate(cv_ids)]
        for job_id, cv_ids in (ranked or {}).items()
    }
    return Workspace(
        cvs=[],
        jobs=[],
        facts=facts or {},
        attributes={},
        ranked_candidates=ranked_candidates,
        ranked_jobs={},
        recommendations={},
        failures=[],
    )


def _gold_json(cvs: dict[str, list[dict[str, object]]]) -> str:
    return json.dumps({"attribution": "Invented", "cvs": cvs})


def test_nfr_004_passes_when_two_of_top_three_are_labeled_relevant():
    workspace = _workspace({"j1.txt": ["a.txt", "x.txt", "b.txt", "c.txt"]})
    relevant = {"j1.txt": {"a.txt", "b.txt", "c.txt"}}

    check = check_ranking(workspace, relevant, LIMITS)

    assert check.passed
    assert [(item.job_id, item.relevant_in_top_k) for item in check.jobs] == [("j1.txt", 2)]


def test_nfr_004_fails_when_only_one_is_relevant():
    workspace = _workspace({"j1.txt": ["a.txt", "x.txt", "y.txt", "b.txt"]})
    relevant = {"j1.txt": {"a.txt", "b.txt"}}

    check = check_ranking(workspace, relevant, LIMITS)

    assert not check.passed
    assert check.jobs[0].relevant_in_top_k == 1


def test_nfr_004_one_failing_job_fails_the_check():
    workspace = _workspace(
        {"j1.txt": ["a.txt", "b.txt", "x.txt"], "j2.txt": ["x.txt", "y.txt", "a.txt"]}
    )
    relevant = {"j1.txt": {"a.txt", "b.txt"}, "j2.txt": {"a.txt"}}

    check = check_ranking(workspace, relevant, LIMITS)

    assert not check.passed
    assert [item.relevant_in_top_k for item in check.jobs] == [2, 1]


def test_nfr_004_fails_with_no_labeled_job_description():
    workspace = _workspace({"j1.txt": ["a.txt", "b.txt", "c.txt"]})

    check = check_ranking(workspace, {"other.txt": {"a.txt"}}, LIMITS)

    assert not check.passed
    assert check.jobs == []


def test_nfr_005_match_needs_same_start_end_and_is_current():
    facts = {"a.txt": _facts([_job((2020, 1), (2021, 6)), _job((2022, 1), None, current=True)])}
    gold = {
        "a.txt": [
            _gold((2020, 1), (2021, 6)),
            _gold((2022, 1), None, current=True),
            _gold((2020, 1), (2021, 7)),
            _gold((2021, 2), (2021, 6)),
            _gold((2022, 1), None),
        ]
    }

    check = check_dates(_workspace(facts=facts), gold, LIMITS)

    assert (check.matched, check.total) == (2, 5)
    assert not check.passed


def test_nfr_005_failed_extraction_counts_as_misses():
    facts = {"a.txt": _facts([_job((2020, 1), (2021, 6))])}
    gold = {
        "a.txt": [_gold((2020, 1), (2021, 6))],
        "failed.txt": [_gold((2019, 1), (2019, 12)), _gold((2018, 1), (2018, 12))],
    }

    check = check_dates(_workspace(facts=facts), gold, LIMITS)

    assert (check.matched, check.total) == (1, 3)


def test_nfr_005_extra_extracted_jobs_not_penalized():
    facts = {"a.txt": _facts([_job((2020, 1), (2021, 6)), _job((2010, 1), (2010, 12))])}
    gold = {"a.txt": [_gold((2020, 1), (2021, 6))]}

    check = check_dates(_workspace(facts=facts), gold, LIMITS)

    assert (check.matched, check.total) == (1, 1)
    assert check.passed


def test_nfr_005_exactly_at_the_limit_passes():
    facts = {"a.txt": _facts([_job((2020, 1), (2020, 2))])}
    gold = {"a.txt": [_gold((2020, 1), (2020, 2))] * 9 + [_gold((2000, 1), (2000, 2))]}

    check = check_dates(_workspace(facts=facts), gold, LIMITS)

    assert (check.matched, check.total) == (9, 10)
    assert check.passed


def test_nfr_005_fails_with_no_gold_jobs():
    check = check_dates(_workspace(), {}, LIMITS)

    assert (check.matched, check.total) == (0, 0)
    assert not check.passed


def test_dec_017_ground_truth_parser_adds_txt_suffix():
    text = "job_id\tcv_id\n29243\t11695\n29243\t15087\n\n32447\t367\n"

    assert parse_ground_truth(text) == {
        "29243.txt": {"11695.txt", "15087.txt"},
        "32447.txt": {"367.txt"},
    }


@pytest.mark.parametrize(
    "text",
    [
        "",
        "wrong\theader\n1\t2\n",
        "job_id\tcv_id\n1\n",
        "job_id\tcv_id\n1\t\n",
        "job_id\tcv_id\n1\t2\t3\n",
    ],
)
def test_dec_017_ground_truth_parser_refuses_wrong_format(text):
    with pytest.raises(EvaluationFileError):
        parse_ground_truth(text)


def test_dec_017_gold_parser_reads_jobs():
    text = _gold_json(
        {
            "a.txt": [
                {"start": "2020-01", "end": "2021-06", "is_current": False},
                {"start": "2022-01", "end": None, "is_current": True},
            ]
        }
    )

    assert parse_gold_jobs(text) == {
        "a.txt": [_gold((2020, 1), (2021, 6)), _gold((2022, 1), None, current=True)]
    }


@pytest.mark.parametrize(
    "text",
    [
        "not json",
        "[]",
        json.dumps({"cvs": []}),
        json.dumps({"cvs": {"a.txt": {}}}),
        json.dumps({"cvs": {"a.txt": ["x"]}}),
        _gold_json({"a.txt": [{"start": "2020-13", "end": None, "is_current": True}]}),
        _gold_json({"a.txt": [{"start": "2020-01", "end": "June", "is_current": False}]}),
        _gold_json({"a.txt": [{"start": None, "end": None, "is_current": False}]}),
        _gold_json({"a.txt": [{"start": "2020-01", "end": None, "is_current": "yes"}]}),
    ],
)
def test_dec_017_gold_parser_refuses_wrong_format(text):
    with pytest.raises(EvaluationFileError):
        parse_gold_jobs(text)


def test_dec_017_report_has_counts_never_cv_content():
    facts = {"a.txt": _facts([_job((2020, 1), (2021, 6))])}
    workspace = _workspace({"j1.txt": ["a.txt", "b.txt", "c.txt"]}, facts)
    truth = {"j1.txt": {"a.txt", "b.txt"}}
    gold = {"a.txt": [_gold((2020, 1), (2021, 6))]}

    report = evaluate(workspace, truth, gold, LIMITS)
    text = format_report(report)

    assert report.passed
    assert "j1.txt: 2 of top 3 relevant (need 2)" in text
    assert "1 of 1 gold jobs matched (100.0%, need 90%)" in text
    assert "NFR-004: PASS" in text
    assert "NFR-005: PASS" in text
    assert CV_SENTENCE not in text


def test_dec_017_report_shows_failure_when_a_check_fails():
    workspace = _workspace({"j1.txt": ["x.txt", "y.txt", "z.txt"]})

    report = evaluate(workspace, {"j1.txt": {"a.txt"}}, {"a.txt": [_gold((2020, 1), None)]}, LIMITS)
    text = format_report(report)

    assert not report.passed
    assert "NFR-004: FAIL" in text
    assert "NFR-005: FAIL" in text


def test_dec_017_report_with_nothing_to_check_says_so():
    text = format_report(evaluate(_workspace(), {}, {}, LIMITS))

    assert "no labeled job description" in text
    assert "no gold jobs" in text
