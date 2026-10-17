import asyncio
import logging
from pathlib import Path

import pytest

from src.llm_schemas import CvFactsReply, JobReply, RecommendationReply
from src.pipeline import Pipeline, PipelineServices, PipelineSettings
from src.ports import LlmError, LlmOutputError
from src.records import Document, Failure, Recommendation, YearMonth

CV_FOLDER = Path("cvs")
JOB_FOLDER = Path("jobs")
EXTRACT_PROMPT = Path("extract.md")
MATCH_PROMPT = Path("match.md")
TODAY = YearMonth(2026, 10)

CVS = [
    Document("a.txt", "CV alpha: Python developer"),
    Document("b.txt", "CV bravo: nurse"),
    Document("c.txt", "CV charlie: data engineer"),
]
JOBS = [
    Document("j1.txt", "Job one: backend developer"),
    Document("j2.txt", "Job two: hospital nurse"),
]
VECTORS = {
    "CV alpha: Python developer": [1.0, 0.0],
    "CV bravo: nurse": [0.0, 1.0],
    "CV charlie: data engineer": [0.8, 0.2],
    "Job one: backend developer": [1.0, 0.1],
    "Job two: hospital nurse": [0.1, 1.0],
}


def _reply(name: str, start: str = "2020-01") -> CvFactsReply:
    job = JobReply(
        title="Worker",
        employer="Acme",
        city=None,
        country=None,
        start=start,
        end=None,
        is_current=True,
        description=None,
    )
    return CvFactsReply(
        name=name,
        current_title="Worker",
        skills=["Skill"],
        city=None,
        country=None,
        highest_degree=None,
        jobs=[job],
        education=[],
    )


class FakeFiles:
    def __init__(self, cvs: list[Document], jobs: list[Document]) -> None:
        self.folders = {CV_FOLDER: cvs, JOB_FOLDER: jobs}
        self.texts = {EXTRACT_PROMPT: "EXTRACT PROMPT", MATCH_PROMPT: "MATCH PROMPT"}
        self.read_folders: list[Path] = []

    def read_documents(self, folder: Path) -> list[Document]:
        self.read_folders.append(folder)
        return self.folders[folder]

    def read_text(self, path: Path) -> str:
        return self.texts[path]


class FakeLlm:
    def __init__(self, start: str = "2020-01") -> None:
        self.start = start
        self.fail_on: dict[str, Exception] = {}
        self.current_with_end: set[str] = set()
        self.completions: list[tuple[str, str, type]] = []
        self.embedded: list[str] = []
        self.in_flight = 0
        self.max_in_flight = 0

    async def _enter(self, user: str) -> None:
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.in_flight -= 1
        for marker, error in self.fail_on.items():
            if marker in user:
                raise error

    async def complete(self, system: str, user: str, schema: type) -> object:
        self.completions.append((system, user, schema))
        await self._enter(f"{schema.__name__} {user}")
        if schema is CvFactsReply:
            word = next(cv.text for cv in CVS if cv.text in user).split()[1].rstrip(":")
            reply = _reply(f"Name {word}", self.start)
            if word in self.current_with_end:
                job = reply.jobs[0].model_copy(update={"end": "2021-01"})
                return reply.model_copy(update={"jobs": [job]})
            return reply
        job = next(job for job in JOBS if job.text in user)
        return RecommendationReply(interview=True, reason=f"Fits {job.doc_id}")

    async def embed(self, text: str) -> list[float]:
        self.embedded.append(text)
        await self._enter(f"embed {text}")
        return VECTORS[text]


class FakeIndex:
    def __init__(self) -> None:
        self.vectors: dict[str, list[float]] = {}
        self.queries: list[list[float]] = []

    def add(self, item_id: str, vector: list[float]) -> None:
        self.vectors[item_id] = vector

    def nearest(self, vector: list[float]) -> list[tuple[str, float]]:
        self.queries.append(vector)
        scores = [
            (item_id, sum(a * b for a, b in zip(stored, vector, strict=True)))
            for item_id, stored in self.vectors.items()
        ]
        return sorted(scores, key=lambda item: (-item[1], item[0]))


def _pipeline(
    llm: FakeLlm,
    *,
    cv_index: FakeIndex | None = None,
    job_index: FakeIndex | None = None,
    files: FakeFiles | None = None,
    max_concurrency: int = 4,
) -> Pipeline:
    services = PipelineServices(
        files=files or FakeFiles(CVS, JOBS),
        llm=llm,
        cv_index=cv_index or FakeIndex(),
        job_index=job_index or FakeIndex(),
    )
    settings = PipelineSettings(
        cv_folder=CV_FOLDER,
        job_folder=JOB_FOLDER,
        extract_prompt_path=EXTRACT_PROMPT,
        match_prompt_path=MATCH_PROMPT,
        max_concurrency=max_concurrency,
    )
    return Pipeline(services, settings)


def _extractions(llm: FakeLlm) -> list[str]:
    return [user for _, user, schema in llm.completions if schema is CvFactsReply]


async def test_ext_001_every_cv_is_read_and_extracted():
    files = FakeFiles(CVS, JOBS)
    llm = FakeLlm()

    workspace = await _pipeline(llm, files=files).run(TODAY)

    assert CV_FOLDER in files.read_folders
    assert workspace.cvs == CVS
    assert sorted(workspace.facts) == ["a.txt", "b.txt", "c.txt"]
    assert workspace.facts["b.txt"].name == "Name bravo"
    assert sorted(workspace.attributes) == ["a.txt", "b.txt", "c.txt"]
    assert all(system == "EXTRACT PROMPT" for system, _, s in llm.completions if s is CvFactsReply)


async def test_job_001_every_job_description_is_read():
    files = FakeFiles(CVS, JOBS)

    workspace = await _pipeline(FakeLlm(), files=files).run(TODAY)

    assert JOB_FOLDER in files.read_folders
    assert workspace.jobs == JOBS
    assert sorted(workspace.ranked_candidates) == ["j1.txt", "j2.txt"]


async def test_prg_003_one_extraction_per_cv():
    llm = FakeLlm()

    await _pipeline(llm).run(TODAY)

    extractions = _extractions(llm)
    assert len(extractions) == len(CVS)
    for cv in CVS:
        assert sum(cv.text in user for user in extractions) == 1


async def test_rnk_001_both_rankings_come_from_the_vector_store():
    cv_index = FakeIndex()
    job_index = FakeIndex()

    workspace = await _pipeline(FakeLlm(), cv_index=cv_index, job_index=job_index).run(TODAY)

    assert cv_index.vectors == {cv.doc_id: VECTORS[cv.text] for cv in CVS}
    assert job_index.vectors == {job.doc_id: VECTORS[job.text] for job in JOBS}
    assert workspace.ranked_candidates["j1.txt"] == [
        ("a.txt", pytest.approx(1.0)),
        ("c.txt", pytest.approx(0.82)),
        ("b.txt", pytest.approx(0.1)),
    ]
    assert workspace.ranked_candidates["j2.txt"][0][0] == "b.txt"
    assert workspace.ranked_jobs["b.txt"] == [
        ("j2.txt", pytest.approx(1.0)),
        ("j1.txt", pytest.approx(0.1)),
    ]
    assert workspace.ranked_jobs["a.txt"][0][0] == "j1.txt"


async def test_rnk_002_rank_unchanged_by_calculated_attributes():
    first = await _pipeline(FakeLlm(start="2010-01")).run(TODAY)
    second = await _pipeline(FakeLlm(start="2026-01")).run(TODAY)

    assert first.attributes != second.attributes
    assert first.ranked_candidates == second.ranked_candidates
    assert first.ranked_jobs == second.ranked_jobs


async def test_rec_001_one_recommendation_per_job_cv_pair():
    llm = FakeLlm()

    workspace = await _pipeline(llm).run(TODAY)

    pairs = {(job.doc_id, cv.doc_id) for job in JOBS for cv in CVS}
    assert set(workspace.recommendations) == pairs
    assert workspace.recommendations[("j2.txt", "a.txt")] == Recommendation(True, "Fits j2.txt")
    requests = [(s, u) for s, u, schema in llm.completions if schema is RecommendationReply]
    assert len(requests) == len(pairs)
    assert all(system == "MATCH PROMPT" for system, _ in requests)


async def test_mis_002_failed_extraction_keeps_candidate_in_every_ranking():
    llm = FakeLlm()
    llm.fail_on["CvFactsReply <cv>\nCV bravo"] = LlmError("Chat request failed: timed out.")

    workspace = await _pipeline(llm).run(TODAY)

    assert "b.txt" not in workspace.facts
    assert "b.txt" not in workspace.attributes
    for ranking in workspace.ranked_candidates.values():
        assert "b.txt" in [cv_id for cv_id, _ in ranking]
    assert [job_id for job_id, _ in workspace.ranked_jobs["b.txt"]] == ["j2.txt", "j1.txt"]


async def test_err_002_failed_call_recorded_and_other_results_kept():
    llm = FakeLlm()
    llm.fail_on["embed CV charlie"] = LlmError("Embedding request failed: HTTP 500.")
    llm.fail_on["RecommendationReply <job_description>\nJob two"] = LlmOutputError(
        "Chat request was refused.", "raw refusal"
    )

    workspace = await _pipeline(llm).run(TODAY)

    assert {failure.item_id for failure in workspace.failures} == {
        "c.txt",
        "j2.txt + a.txt",
        "j2.txt + b.txt",
        "j2.txt + c.txt",
    }
    assert ("j2.txt", "a.txt") not in workspace.recommendations
    assert ("j1.txt", "a.txt") in workspace.recommendations
    assert workspace.ranked_candidates["j1.txt"][-1] == ("c.txt", None)
    assert workspace.ranked_jobs["c.txt"] == [("j1.txt", None), ("j2.txt", None)]
    assert "c.txt" in workspace.facts
    assert workspace.cvs == CVS


async def test_err_001_failure_cause_names_the_step():
    llm = FakeLlm()
    llm.fail_on["embed Job one"] = LlmError("Embedding request failed: timed out.")
    llm.fail_on["CvFactsReply <cv>\nCV alpha"] = LlmError("Chat request failed: HTTP 429.")

    workspace = await _pipeline(llm).run(TODAY)

    assert Failure("j1.txt", "Job description embedding: Embedding request failed: timed out.") in (
        workspace.failures
    )
    assert Failure("a.txt", "CV extraction: Chat request failed: HTTP 429.") in workspace.failures


async def test_err_001_invalid_extraction_reply_is_recorded():
    llm = FakeLlm()
    llm.current_with_end.add("alpha")

    workspace = await _pipeline(llm).run(TODAY)

    assert [failure.item_id for failure in workspace.failures] == ["a.txt"]
    assert workspace.failures[0].cause.startswith("CV extraction: ")


async def test_dec_008_non_llm_error_still_stops_the_run():
    llm = FakeLlm()
    llm.fail_on["embed CV bravo"] = RuntimeError("bug")

    with pytest.raises(RuntimeError, match="bug"):
        await _pipeline(llm).run(TODAY)


async def test_dec_007_concurrency_stays_within_the_limit():
    llm = FakeLlm()

    await _pipeline(llm, max_concurrency=2).run(TODAY)

    assert llm.max_in_flight == 2


async def test_nfr_001_job_text_and_cv_text_go_only_to_the_llm_client(caplog):
    llm = FakeLlm()
    cv_index = FakeIndex()
    job_index = FakeIndex()
    caplog.set_level(logging.INFO)

    await _pipeline(llm, cv_index=cv_index, job_index=job_index).run(TODAY)

    texts = [document.text for document in CVS + JOBS]
    assert sorted(llm.embedded) == sorted(texts)
    for document in CVS + JOBS:
        assert any(document.text in user for _, user, _ in llm.completions)
    stored = list(cv_index.vectors) + list(job_index.vectors)
    assert stored == [cv.doc_id for cv in CVS] + [job.doc_id for job in JOBS]
    for text in texts:
        assert text not in caplog.text
