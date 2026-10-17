"""The router of the job descriptions: the list, one text and the ranked candidates.

Each handler calls one `workspace_views` function and returns its result. It holds no logic.
Implements LST-001, JOB-002, JOB-003 and DEC-020.
"""

from fastapi import APIRouter

from src.api.schemas import JobDetailOut, JobSummaryOut, RankedCandidateOut
from src.records import Workspace
from src.workspace_views import job_detail, job_list, ranked_candidates


def create_jobs_router(workspace: Workspace) -> APIRouter:
    """Return the router of the job descriptions, reading from this workspace."""
    router = APIRouter(prefix="/api/jobs")

    @router.get("", response_model=list[JobSummaryOut])
    async def list_jobs() -> object:
        return job_list(workspace)

    @router.get("/{job_id}", response_model=JobDetailOut)
    async def get_job(job_id: str) -> object:
        return job_detail(workspace, job_id)

    @router.get("/{job_id}/ranked-candidates", response_model=list[RankedCandidateOut])
    async def get_ranked_candidates(job_id: str) -> object:
        return ranked_candidates(workspace, job_id)

    return router
