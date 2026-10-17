"""Runs the start-up steps once and returns the in-memory workspace (DEC-007).

Reads the documents, extracts each CV once, calculates the attributes, embeds every document,
ranks both ways and asks for one recommendation per pair. It talks to no external system itself:
the file reader, the LLM client and the two vector stores are passed in. It builds no prompt text
(`extraction` and `recommendation` do) and serves nothing (`src/api/` does).
Implements EXT-001, JOB-001, PRG-003, MIS-002, ERR-001, ERR-002, RNK-001, RNK-002, REC-001,
NFR-001, DEC-007, DEC-008 and DEC-014.
"""

import asyncio
import logging
from collections.abc import Awaitable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from src.attributes import calculate_attributes
from src.extraction import extraction_user_text, facts_from_reply
from src.llm_schemas import CvFactsReply, RecommendationReply
from src.ports import Embedder, LlmError, StructuredCompleter, VectorIndex
from src.ranking import append_unscored
from src.recommendation import recommendation_from_reply, recommendation_user_text
from src.records import CvFacts, Document, Failure, Recommendation, Workspace, YearMonth

logger = logging.getLogger(__name__)

type _Ranking = list[tuple[str, float | None]]


class Step(StrEnum):
    """The start-up steps that call the LLM service. A failure cause names one (ERR-001)."""

    EXTRACTION = "CV extraction"
    CV_EMBEDDING = "CV embedding"
    JOB_EMBEDDING = "Job description embedding"
    RECOMMENDATION = "Recommendation"


class DocumentSource(Protocol):
    """Reads the input documents and the prompt files. `src.file_reader` implements it."""

    def read_documents(self, folder: Path) -> list[Document]:
        """Return one document per file in the folder, sorted by file name."""
        ...

    def read_text(self, path: Path) -> str:
        """Return the content of one file."""
        ...


class LlmService(StructuredCompleter, Embedder, Protocol):
    """Completes structured requests and embeds texts. `src.llm_client.LlmClient` implements it."""


@dataclass(frozen=True)
class PipelineServices:
    """The collaborators that reach external systems, passed in by the entry point."""

    files: DocumentSource
    llm: LlmService
    cv_index: VectorIndex
    job_index: VectorIndex


@dataclass(frozen=True)
class PipelineSettings:
    """The input locations and the call limit of the pipeline."""

    cv_folder: Path
    job_folder: Path
    extract_prompt_path: Path
    match_prompt_path: Path
    max_concurrency: int


@dataclass(frozen=True)
class _Prompts:
    """The system texts of the two chat requests."""

    extract: str
    match: str


def _split[K, T](keys: list[K], results: list[T | Failure]) -> tuple[dict[K, T], list[Failure]]:
    """Separate the results that succeeded, by key, from the recorded failures."""
    succeeded = {
        key: result
        for key, result in zip(keys, results, strict=True)
        if not isinstance(result, Failure)
    }
    return succeeded, [result for result in results if isinstance(result, Failure)]


class Pipeline:
    """Builds the workspace of one run. Owns the limit on LLM calls in flight (DEC-007)."""

    def __init__(self, services: PipelineServices, settings: PipelineSettings) -> None:
        """Keep the collaborators and the settings, and create the call limit."""
        self._services = services
        self._settings = settings
        self._limit = asyncio.Semaphore(settings.max_concurrency)

    async def run(self, today: YearMonth) -> Workspace:
        """Run every start-up step and return the results (DEC-007).

        Args:
            today: The current month, used for the calculated attributes.

        Returns:
            The workspace. A failed LLM call leaves its result out and adds a `Failure` (DEC-008).

        Raises:
            FileNotFoundError: If a folder or a prompt file is missing.
        """
        files = self._services.files
        cvs = files.read_documents(self._settings.cv_folder)
        jobs = files.read_documents(self._settings.job_folder)
        prompts = _Prompts(
            extract=files.read_text(self._settings.extract_prompt_path),
            match=files.read_text(self._settings.match_prompt_path),
        )
        logger.info("Read %d CVs and %d job descriptions", len(cvs), len(jobs))
        facts, extraction_failures = await self._extract_all(cvs, prompts.extract)
        rankings, embedding_failures = await self._rank_all(cvs, jobs)
        recommendations, recommendation_failures = await self._recommend_all(
            jobs, facts, prompts.match
        )
        return Workspace(
            cvs=cvs,
            jobs=jobs,
            facts=facts,
            attributes={cv_id: calculate_attributes(f, today) for cv_id, f in facts.items()},
            ranked_candidates=rankings[0],
            ranked_jobs=rankings[1],
            recommendations=recommendations,
            failures=extraction_failures + embedding_failures + recommendation_failures,
        )

    async def _guarded[T](self, step: Step, item_id: str, call: Awaitable[T]) -> T | Failure:
        """Run one LLM call within the limit. Record an `LlmError` as a failure (DEC-008).

        The failure is logged without the trace: the chained SDK error could hold a secret.
        """
        async with self._limit:
            try:
                return await call
            except LlmError as err:
                failure = Failure(item_id, f"{step}: {err}")
        logger.error("Failure recorded for %s: %s", item_id, failure.cause)
        return failure

    async def _extract_all(
        self, cvs: list[Document], prompt: str
    ) -> tuple[dict[str, CvFacts], list[Failure]]:
        """Extract the facts of each CV, once per CV (PRG-003)."""
        results = await asyncio.gather(
            *(self._guarded(Step.EXTRACTION, cv.doc_id, self._extract(cv, prompt)) for cv in cvs)
        )
        facts, failures = _split([cv.doc_id for cv in cvs], list(results))
        logger.info("Extracted the facts of %d of %d CVs", len(facts), len(cvs))
        return facts, failures

    async def _extract(self, cv: Document, prompt: str) -> CvFacts:
        """Ask for the facts of one CV and map the reply."""
        reply = await self._services.llm.complete(prompt, extraction_user_text(cv), CvFactsReply)
        return facts_from_reply(reply)

    async def _embed_all(
        self, step: Step, documents: list[Document], index: VectorIndex
    ) -> tuple[dict[str, list[float]], list[Failure]]:
        """Embed the raw text of each document (DEC-014) and store each vector by ID."""
        llm = self._services.llm
        results = await asyncio.gather(
            *(self._guarded(step, doc.doc_id, llm.embed(doc.text)) for doc in documents)
        )
        vectors, failures = _split([doc.doc_id for doc in documents], list(results))
        for doc_id, vector in vectors.items():
            index.add(doc_id, vector)
        logger.info("%s: %d of %d documents embedded", step, len(vectors), len(documents))
        return vectors, failures

    async def _rank_all(
        self, cvs: list[Document], jobs: list[Document]
    ) -> tuple[tuple[dict[str, _Ranking], dict[str, _Ranking]], list[Failure]]:
        """Rank the CVs for each job description and the job descriptions for each CV (RNK-001)."""
        cv_index = self._services.cv_index
        job_index = self._services.job_index
        cv_vectors, cv_failures = await self._embed_all(Step.CV_EMBEDDING, cvs, cv_index)
        job_vectors, job_failures = await self._embed_all(Step.JOB_EMBEDDING, jobs, job_index)
        ranked_candidates = _rankings(jobs, job_vectors, cv_index, [cv.doc_id for cv in cvs])
        ranked_jobs = _rankings(cvs, cv_vectors, job_index, [job.doc_id for job in jobs])
        return (ranked_candidates, ranked_jobs), cv_failures + job_failures

    async def _recommend_all(
        self, jobs: list[Document], facts: dict[str, CvFacts], prompt: str
    ) -> tuple[dict[tuple[str, str], Recommendation], list[Failure]]:
        """Ask for one recommendation per job description and extracted CV (REC-001)."""
        pairs = [(job, cv_id) for job in jobs for cv_id in facts]
        results = await asyncio.gather(
            *(
                self._guarded(
                    Step.RECOMMENDATION,
                    f"{job.doc_id} + {cv_id}",
                    self._recommend(job, facts[cv_id], prompt),
                )
                for job, cv_id in pairs
            )
        )
        recommendations, failures = _split(
            [(job.doc_id, cv_id) for job, cv_id in pairs], list(results)
        )
        logger.info("Received %d of %d recommendations", len(recommendations), len(pairs))
        return recommendations, failures

    async def _recommend(self, job: Document, facts: CvFacts, prompt: str) -> Recommendation:
        """Ask whether to interview one candidate for one job description and map the reply."""
        user = recommendation_user_text(job, facts)
        reply = await self._services.llm.complete(prompt, user, RecommendationReply)
        return recommendation_from_reply(reply)


def _rankings(
    queries: list[Document],
    vectors: dict[str, list[float]],
    index: VectorIndex,
    all_ids: list[str],
) -> dict[str, _Ranking]:
    """Rank every stored item for each query document. None is dropped (MIS-002, RNK-002)."""
    return {
        query.doc_id: append_unscored(
            index.nearest(vectors[query.doc_id]) if query.doc_id in vectors else [], all_ids
        )
        for query in queries
    }
