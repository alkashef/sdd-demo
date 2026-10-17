import logging
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import main
from src.config import (
    DataSettings,
    EvalSettings,
    LlmSettings,
    LogSettings,
    ServerSettings,
    Settings,
)
from src.llm_schemas import CvFactsReply, EducationReply, JobReply, RecommendationReply
from src.pipeline import PipelineServices
from src.records import Document, YearMonth

TODAY = YearMonth(2026, 10)
API_KEY = "sk-invented-secret-key-0123456789"
CV_FOLDER = Path("cvs")
JOB_FOLDER = Path("jobs")
EXTRACT_PROMPT = Path("extract.md")
MATCH_PROMPT = Path("match.md")

CVS = [
    Document("ann.txt", "CV of Ann, analyst"),
    Document("bob.txt", "CV of Bob, nurse"),
]
JOBS = [
    Document("j1.txt", "Data Analyst\nWe need numbers."),
    Document("j2.txt", "Nurse\nWe need care."),
]
VECTORS = {
    "CV of Ann, analyst": [1.0, 0.0],
    "CV of Bob, nurse": [0.0, 1.0],
    "Data Analyst\nWe need numbers.": [1.0, 0.1],
    "Nurse\nWe need care.": [0.1, 1.0],
}


def _job(title: str, start: str, end: str | None, *, current: bool = False) -> JobReply:
    return JobReply(
        title=title,
        employer="Acme" if title != "Lead" else "Globex",
        city="Cairo",
        country="Egypt" if title != "Lead" else "Kenya",
        start=start,
        end=end,
        is_current=current,
        description=f"Work as {title}",
    )


def _ann_reply() -> CvFactsReply:
    """EX-001 jobs (17, 31 and 58 months) and the EX-002 graduation (May 2018)."""
    return CvFactsReply(
        name="Ann",
        current_title="Lead",
        skills=["SQL", "Python"],
        city="Cairo",
        country="Egypt",
        highest_degree="BSc",
        jobs=[
            _job("Junior", "2018-01", "2019-05"),
            _job("Analyst", "2019-06", "2021-12"),
            _job("Lead", "2022-01", None, current=True),
        ],
        education=[
            EducationReply(degree="BSc", university="Nile", major="Stats", graduated="2018-05")
        ],
    )


def _bob_reply() -> CvFactsReply:
    return CvFactsReply(
        name="Bob",
        current_title="Nurse",
        skills=[],
        city=None,
        country=None,
        highest_degree=None,
        jobs=[],
        education=[],
    )


class FakeFiles:
    def read_documents(self, folder: Path) -> list[Document]:
        return {CV_FOLDER: CVS, JOB_FOLDER: JOBS}[folder]

    def read_text(self, path: Path) -> str:
        return {EXTRACT_PROMPT: "EXTRACT", MATCH_PROMPT: "MATCH"}[path]


class FakeLlm:
    def __init__(self) -> None:
        self.extractions: list[str] = []

    async def complete(self, system: str, user: str, schema: type) -> object:
        if schema is CvFactsReply:
            self.extractions.append(user)
            return _ann_reply() if "Ann" in user else _bob_reply()
        return RecommendationReply(interview=True, reason="Fits.")

    async def embed(self, text: str) -> list[float]:
        return VECTORS[text]


class FakeIndex:
    def __init__(self) -> None:
        self.vectors: dict[str, list[float]] = {}

    def add(self, item_id: str, vector: list[float]) -> None:
        self.vectors[item_id] = vector

    def nearest(self, vector: list[float]) -> list[tuple[str, float]]:
        scores = [
            (item_id, sum(a * b for a, b in zip(stored, vector, strict=True)))
            for item_id, stored in self.vectors.items()
        ]
        return sorted(scores, key=lambda item: (-item[1], item[0]))


class ServerSpy:
    """Stands in for uvicorn: remembers the app, host and port it was asked to serve."""

    def __init__(self) -> None:
        self.app: FastAPI | None = None
        self.host = ""
        self.port = 0

    def __call__(self, app: FastAPI, host: str, port: int) -> None:
        self.app, self.host, self.port = app, host, port


def _settings(tmp_path: Path, *, host: str = "127.0.0.1", port: int = 8123) -> Settings:
    web_root = tmp_path / "web"
    web_root.mkdir(exist_ok=True)
    (web_root / "index.html").write_text("<h1>Front end</h1>", encoding="utf-8")
    return Settings(
        llm=LlmSettings(API_KEY, "https://llm.invalid/v1", "chat-model", 100, "embed-model", 5, 3),
        data=DataSettings(CV_FOLDER, JOB_FOLDER, EXTRACT_PROMPT, MATCH_PROMPT),
        evaluation=EvalSettings(Path("truth.tsv"), Path("gold.json"), 3, 2, 90),
        server=ServerSettings(web_root, host, port),
        log=LogSettings("INFO", tmp_path / "logs" / "app.log"),
    )


@pytest.fixture
def llm() -> FakeLlm:
    return FakeLlm()


@pytest.fixture
def spy(tmp_path: Path, llm: FakeLlm) -> ServerSpy:
    services = PipelineServices(FakeFiles(), llm, FakeIndex(), FakeIndex())
    server = ServerSpy()
    main.start(_settings(tmp_path), services, TODAY, server)
    return server


@pytest.fixture
def client(spy: ServerSpy) -> TestClient:
    assert spy.app is not None
    return TestClient(spy.app)


@pytest.fixture
def clean_logging() -> Iterator[None]:
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    for handler in root.handlers[:]:
        if handler not in handlers:
            handler.close()
    root.handlers[:] = handlers
    root.setLevel(level)


def test_ext_001_start_reads_cvs_and_api_lists_them_end_to_end(client):
    response = client.get("/api/candidates")

    assert response.json() == [
        {"id": "ann.txt", "name": "Ann"},
        {"id": "bob.txt", "name": "Bob"},
    ]
    assert client.get("/api/candidates/ann.txt").json()["text"] == "CV of Ann, analyst"


def test_job_001_start_reads_job_descriptions_end_to_end(client):
    response = client.get("/api/jobs")

    assert response.json() == [
        {"id": "j1.txt", "title": "Data Analyst"},
        {"id": "j2.txt", "title": "Nurse"},
    ]


def test_ext_002_to_ext_010_candidate_response_has_extracted_attributes_end_to_end(client):
    extracted = client.get("/api/candidates/ann.txt").json()["extracted"]

    assert extracted["name"] == "Ann"
    assert extracted["current_title"] == "Lead"
    assert extracted["skills"] == ["SQL", "Python"]
    assert (extracted["city"], extracted["country"]) == ("Cairo", "Egypt")
    assert extracted["highest_degree"] == "BSc"
    assert extracted["countries"] == ["Egypt", "Kenya"]
    assert extracted["employers"] == ["Acme", "Globex"]
    last_job = extracted["last_job"]
    assert (last_job["title"], last_job["employer"], last_job["is_current"]) == (
        "Lead",
        "Globex",
        True,
    )


def test_cal_001_to_cal_007_candidate_response_matches_ex_001_end_to_end(client):
    calculated = client.get("/api/candidates/ann.txt").json()["calculated"]

    assert calculated["total_months"] == 106
    assert calculated["job_count"] == 3
    assert calculated["average_job_months"] == pytest.approx(106 / 3)
    assert calculated["gaps"] == []
    assert calculated["months_since_graduation"] == 102
    assert calculated["currently_employed"] is True


def test_prg_003_start_extracts_each_cv_once_end_to_end(client, llm):
    client.get("/api/candidates/ann.txt")
    client.get("/api/jobs/j1.txt/ranked-candidates")
    client.get("/api/jobs/j2.txt/ranked-candidates")

    assert len(llm.extractions) == len(CVS)


def test_dec_013_server_started_with_host_from_settings(tmp_path, llm):
    services = PipelineServices(FakeFiles(), llm, FakeIndex(), FakeIndex())
    server = ServerSpy()

    main.start(_settings(tmp_path, host="127.0.0.1", port=8123), services, TODAY, server)

    assert server.app is not None
    assert (server.host, server.port) == ("127.0.0.1", 8123)


def test_nfr_002_log_file_has_no_api_key(tmp_path, llm, clean_logging):
    settings = _settings(tmp_path)
    main.configure_logging(settings.log)
    services = PipelineServices(FakeFiles(), llm, FakeIndex(), FakeIndex())

    main.start(settings, services, TODAY, ServerSpy())

    for handler in logging.getLogger().handlers:
        handler.flush()
    log = settings.log.file.read_text(encoding="utf-8")
    assert "Read 2 CVs and 2 job descriptions" in log
    assert API_KEY not in log
