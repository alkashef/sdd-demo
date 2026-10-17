"""The router of the candidates: the list, one CV with its attributes and the ranked jobs.

Each handler calls one `workspace_views` function and returns its result. It holds no logic.
Implements LST-002, CND-001, CND-002 and CND-003.
"""

from fastapi import APIRouter

from src.api.schemas import CandidateDetailOut, CandidateSummaryOut, RankedJobOut
from src.records import Workspace
from src.workspace_views import candidate_detail, candidate_list, ranked_jobs


def create_candidates_router(workspace: Workspace) -> APIRouter:
    """Return the router of the candidates, reading from this workspace."""
    router = APIRouter(prefix="/api/candidates")

    @router.get("", response_model=list[CandidateSummaryOut])
    async def list_candidates() -> object:
        return candidate_list(workspace)

    @router.get("/{candidate_id}", response_model=CandidateDetailOut)
    async def get_candidate(candidate_id: str) -> object:
        return candidate_detail(workspace, candidate_id)

    @router.get("/{candidate_id}/ranked-jobs", response_model=list[RankedJobOut])
    async def get_ranked_jobs(candidate_id: str) -> object:
        return ranked_jobs(workspace, candidate_id)

    return router
