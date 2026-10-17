from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
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


def _job(end: YearMonth | None, *, is_current: bool) -> Job:
    return Job("Analyst", "Acme", "Cairo", "Egypt", YearMonth(2019, 6), end, is_current, "Reports")


def _facts(name: str | None, last: Job) -> CvFacts:
    return CvFacts(name, "Analyst", ["SQL"], "Cairo", "Egypt", "BSc", [last], [])


@pytest.fixture
def workspace() -> Workspace:
    return Workspace(
        cvs=[
            Document("a.txt", "CV of Ann"),
            Document("b.txt", "CV of nobody"),
            Document("c.txt", "CV that failed"),
            Document("d.txt", "CV of Dan"),
        ],
        jobs=[
            Document("j1.txt", "Data Analyst\nWe need numbers."),
            Document("j2.txt", "Engineer\nWe need bridges."),
        ],
        facts={
            "a.txt": _facts("Ann", _job(None, is_current=True)),
            "b.txt": _facts(None, _job(YearMonth(2020, 1), is_current=False)),
            "d.txt": _facts("Dan", _job(None, is_current=False)),
        },
        attributes={
            "a.txt": CalculatedAttributes(100, 1, 50.5, [3], 80, True),
            "b.txt": CalculatedAttributes(None, 1, None, None, None, None),
            "d.txt": CalculatedAttributes(None, 1, None, None, None, None),
        },
        ranked_candidates={
            "j1.txt": [("b.txt", 0.9), ("a.txt", 0.5), ("d.txt", 0.4), ("c.txt", None)],
            "j2.txt": [("a.txt", 0.4), ("b.txt", 0.3), ("d.txt", 0.2), ("c.txt", None)],
        },
        ranked_jobs={
            "a.txt": [("j2.txt", 0.7), ("j1.txt", 0.6)],
            "b.txt": [("j1.txt", 0.2), ("j2.txt", 0.1)],
            "c.txt": [("j1.txt", None), ("j2.txt", None)],
            "d.txt": [("j1.txt", 0.3), ("j2.txt", 0.2)],
        },
        recommendations={("j1.txt", "a.txt"): Recommendation(True, "Strong fit.")},
        failures=[Failure("c.txt", "CV extraction: timeout")],
    )


@pytest.fixture
def web_root(tmp_path: Path) -> Path:
    (tmp_path / "index.html").write_text("<h1>Front end</h1>", encoding="utf-8")
    return tmp_path


@pytest.fixture
def client(workspace: Workspace, web_root: Path) -> TestClient:
    return TestClient(create_app(workspace, web_root))


def test_lst_001_api_lists_job_descriptions(client):
    response = client.get("/api/jobs")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "j1.txt", "title": "Data Analyst"},
        {"id": "j2.txt", "title": "Engineer"},
    ]


def test_lst_002_api_lists_candidates(client):
    response = client.get("/api/candidates")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "a.txt", "name": "Ann"},
        {"id": "b.txt", "name": None},
        {"id": "c.txt", "name": None},
        {"id": "d.txt", "name": "Dan"},
    ]


def test_job_003_api_returns_job_text(client):
    response = client.get("/api/jobs/j1.txt")

    assert response.status_code == 200
    assert response.json() == {
        "id": "j1.txt",
        "title": "Data Analyst",
        "text": "Data Analyst\nWe need numbers.",
    }


def test_dec_020_api_unknown_job_returns_404_with_detail(client):
    for path in ("/api/jobs/zzz.txt", "/api/jobs/zzz.txt/ranked-candidates"):
        response = client.get(path)

        assert response.status_code == 404
        assert "zzz.txt" in response.json()["detail"]


def test_dec_020_api_unknown_candidate_returns_404_with_detail(client):
    for path in (
        "/api/candidates/zzz.txt",
        "/api/candidates/zzz.txt/ranked-jobs",
    ):
        response = client.get(path)

        assert response.status_code == 404
        assert "zzz.txt" in response.json()["detail"]


def test_job_002_api_returns_ranked_candidates(client):
    response = client.get("/api/jobs/j1.txt/ranked-candidates")

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body] == ["b.txt", "a.txt", "d.txt", "c.txt"]
    ann = body[1]
    assert ann["name"] == "Ann"
    assert ann["score"] == 0.5
    assert ann["recommendation"] == {"interview": True, "reason": "Strong fit."}
    assert ann["extracted"]["skills"] == ["SQL"]
    assert ann["extracted"]["countries"] == ["Egypt"]
    assert ann["extracted"]["employers"] == ["Acme"]
    assert ann["calculated"] == {
        "total_months": 100,
        "job_count": 1,
        "average_job_months": 50.5,
        "gaps": [3],
        "months_since_graduation": 80,
        "currently_employed": True,
    }


def test_cnd_001_api_returns_raw_cv(client):
    response = client.get("/api/candidates/a.txt")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "a.txt"
    assert body["text"] == "CV of Ann"


def test_cnd_002_api_returns_attributes(client):
    body = client.get("/api/candidates/a.txt").json()

    assert body["name"] == "Ann"
    assert body["extracted"]["current_title"] == "Analyst"
    assert body["extracted"]["highest_degree"] == "BSc"
    assert body["calculated"]["total_months"] == 100
    assert body["calculated"]["currently_employed"] is True


def test_cnd_003_api_returns_ranked_jobs(client):
    response = client.get("/api/candidates/a.txt/ranked-jobs")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "j2.txt", "title": "Engineer", "score": 0.7},
        {"id": "j1.txt", "title": "Data Analyst", "score": 0.6},
    ]


def test_err_001_api_returns_failure_list(client):
    response = client.get("/api/failures")

    assert response.status_code == 200
    assert response.json() == [{"item_id": "c.txt", "cause": "CV extraction: timeout"}]


def test_mis_001_api_missing_value_is_null(client):
    failed = client.get("/api/candidates/c.txt").json()
    unnamed = client.get("/api/candidates/b.txt").json()
    ranked = client.get("/api/jobs/j1.txt/ranked-candidates").json()

    assert failed["name"] is None
    assert failed["extracted"] is None
    assert failed["calculated"] is None
    assert unnamed["extracted"]["name"] is None
    assert unnamed["calculated"]["total_months"] is None
    assert ranked[3]["score"] is None
    assert ranked[3]["recommendation"] is None


def test_dec_015_api_last_job_has_end_and_is_current(client):
    current = client.get("/api/candidates/a.txt").json()["extracted"]["last_job"]
    ended = client.get("/api/candidates/b.txt").json()["extracted"]["last_job"]
    unknown = client.get("/api/candidates/d.txt").json()["extracted"]["last_job"]

    assert (current["end"], current["is_current"]) == (None, True)
    assert (ended["end"], ended["is_current"]) == ({"year": 2020, "month": 1}, False)
    assert (unknown["end"], unknown["is_current"]) == (None, False)


def test_dec_002_health_and_static_front_end_served(client):
    health = client.get("/health")
    page = client.get("/")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert page.status_code == 200
    assert "<h1>Front end</h1>" in page.text


def test_dec_002_api_routes_win_over_static_mount(client):
    assert client.get("/api/jobs").headers["content-type"] == "application/json"
