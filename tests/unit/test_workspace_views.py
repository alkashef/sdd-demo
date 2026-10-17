import pytest

from src.records import (
    CalculatedAttributes,
    CvFacts,
    Document,
    Failure,
    Job,
    Recommendation,
    Workspace,
    YearMonth,
)
from src.workspace_views import (
    NotFoundError,
    candidate_detail,
    candidate_list,
    failure_list,
    job_detail,
    job_list,
    ranked_candidates,
    ranked_jobs,
)


def _job(country: str, employer: str, start: YearMonth, end: YearMonth | None) -> Job:
    return Job("Role", employer, "Cairo", country, start, end, end is None, None)


def _facts(name: str | None, jobs: list[Job]) -> CvFacts:
    return CvFacts(name, "Analyst", ["SQL"], "Cairo", "Egypt", "BSc", jobs, [])


_OLD_JOB = _job("Egypt", "Acme", YearMonth(2018, 1), YearMonth(2019, 5))
_LAST_JOB = _job("Kenya", "Beta", YearMonth(2019, 6), None)
_ATTRIBUTES = CalculatedAttributes(100, 2, 50.0, [], 80, True)


@pytest.fixture
def workspace() -> Workspace:
    return Workspace(
        cvs=[
            Document("a.txt", "CV of Ann"),
            Document("b.txt", "CV of nobody"),
            Document("c.txt", "CV that failed"),
        ],
        jobs=[
            Document("j1.txt", "Data Analyst\nWe need numbers."),
            Document("j2.txt", "Engineer\nWe need bridges."),
        ],
        facts={
            "a.txt": _facts("Ann", [_OLD_JOB, _LAST_JOB]),
            "b.txt": _facts(None, []),
        },
        attributes={
            "a.txt": _ATTRIBUTES,
            "b.txt": CalculatedAttributes(None, 0, None, None, None, None),
        },
        ranked_candidates={
            "j1.txt": [("b.txt", 0.9), ("a.txt", 0.5), ("c.txt", None)],
            "j2.txt": [("a.txt", 0.4), ("b.txt", 0.3), ("c.txt", None)],
        },
        ranked_jobs={
            "a.txt": [("j2.txt", 0.7), ("j1.txt", 0.6)],
            "b.txt": [("j1.txt", 0.2), ("j2.txt", 0.1)],
            "c.txt": [("j1.txt", None), ("j2.txt", None)],
        },
        recommendations={("j1.txt", "a.txt"): Recommendation(True, "Strong fit.")},
        failures=[Failure("c.txt", "CV extraction: timeout")],
    )


def test_lst_001_job_list_has_id_and_title(workspace):
    jobs = job_list(workspace)

    assert [(job.job_id, job.title) for job in jobs] == [
        ("j1.txt", "Data Analyst"),
        ("j2.txt", "Engineer"),
    ]


def test_lst_002_candidate_list_has_id_and_name(workspace):
    candidates = candidate_list(workspace)

    assert [candidate.candidate_id for candidate in candidates] == ["a.txt", "b.txt", "c.txt"]
    assert candidates[0].name == "Ann"


def test_job_003_job_detail_has_raw_text(workspace):
    detail = job_detail(workspace, "j1.txt")

    assert (detail.job_id, detail.title) == ("j1.txt", "Data Analyst")
    assert detail.text == "Data Analyst\nWe need numbers."


def test_dec_020_job_detail_unknown_id_raises_not_found(workspace):
    with pytest.raises(NotFoundError, match=r"job description 'nope\.txt'"):
        job_detail(workspace, "nope.txt")


def test_dec_020_ranked_candidates_unknown_id_raises_not_found(workspace):
    with pytest.raises(NotFoundError, match=r"job description 'nope\.txt'"):
        ranked_candidates(workspace, "nope.txt")


def test_job_002_ranked_candidates_best_first_with_score(workspace):
    ranked = ranked_candidates(workspace, "j1.txt")

    assert [(item.candidate_id, item.score) for item in ranked] == [
        ("b.txt", 0.9),
        ("a.txt", 0.5),
        ("c.txt", None),
    ]


def test_rnk_003_ranked_candidate_has_extracted_and_calculated_attributes(workspace):
    ann = ranked_candidates(workspace, "j1.txt")[1]

    assert ann.name == "Ann"
    assert ann.calculated == _ATTRIBUTES
    assert ann.extracted is not None
    assert ann.extracted.current_title == "Analyst"
    assert ann.extracted.skills == ["SQL"]
    assert (ann.extracted.city, ann.extracted.country) == ("Cairo", "Egypt")
    assert ann.extracted.highest_degree == "BSc"
    assert ann.extracted.countries == ["Egypt", "Kenya"]
    assert ann.extracted.employers == ["Acme", "Beta"]
    assert ann.extracted.last_job == _LAST_JOB


def test_rec_001_ranked_candidate_has_recommendation(workspace):
    ranked = ranked_candidates(workspace, "j1.txt")

    assert ranked[1].recommendation == Recommendation(True, "Strong fit.")
    assert ranked[0].recommendation is None


def test_cnd_001_candidate_detail_has_raw_text(workspace):
    detail = candidate_detail(workspace, "a.txt")

    assert (detail.candidate_id, detail.text) == ("a.txt", "CV of Ann")


def test_cnd_001_candidate_detail_unknown_id_raises_not_found(workspace):
    with pytest.raises(NotFoundError, match=r"candidate 'nope\.txt'"):
        candidate_detail(workspace, "nope.txt")


def test_cnd_002_candidate_detail_has_attributes(workspace):
    detail = candidate_detail(workspace, "a.txt")

    assert detail.name == "Ann"
    assert detail.calculated == _ATTRIBUTES
    assert detail.extracted is not None
    assert detail.extracted.employers == ["Acme", "Beta"]


def test_cnd_003_ranked_jobs_best_first_without_recommendation(workspace):
    ranked = ranked_jobs(workspace, "a.txt")

    assert [(item.job_id, item.title, item.score) for item in ranked] == [
        ("j2.txt", "Engineer", 0.7),
        ("j1.txt", "Data Analyst", 0.6),
    ]
    assert not hasattr(ranked[0], "recommendation")


def test_cnd_003_ranked_jobs_unknown_id_raises_not_found(workspace):
    with pytest.raises(NotFoundError, match=r"candidate 'nope\.txt'"):
        ranked_jobs(workspace, "nope.txt")


def test_mis_001_missing_value_is_none(workspace):
    nobody = candidate_detail(workspace, "b.txt")

    assert nobody.name is None
    assert nobody.extracted is not None
    assert nobody.extracted.last_job is None
    assert nobody.extracted.countries == []
    assert nobody.calculated is not None
    assert nobody.calculated.total_months is None


def test_mis_002_candidate_without_facts_stays_in_lists(workspace):
    listed = {item.candidate_id: item for item in candidate_list(workspace)}
    in_ranking = {item.candidate_id: item for item in ranked_candidates(workspace, "j1.txt")}

    assert listed["c.txt"].name is None
    assert in_ranking["c.txt"].extracted is None
    assert in_ranking["c.txt"].calculated is None
    assert candidate_detail(workspace, "c.txt").text == "CV that failed"


def test_dec_015_last_job_has_is_current(workspace):
    extracted = candidate_detail(workspace, "a.txt").extracted

    assert extracted is not None
    assert extracted.last_job is not None
    assert extracted.last_job.end is None
    assert extracted.last_job.is_current is True


def test_err_001_failure_list_has_item_and_cause(workspace):
    assert failure_list(workspace) == [Failure("c.txt", "CV extraction: timeout")]
