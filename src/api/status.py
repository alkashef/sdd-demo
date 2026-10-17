"""The router of the status endpoints: liveness and the failure list.

Each handler calls one function and returns its result. It holds no logic. Implements ERR-001.
"""

from fastapi import APIRouter

from src.api.schemas import FailureOut
from src.records import Workspace
from src.workspace_views import failure_list


def create_status_router(workspace: Workspace) -> APIRouter:
    """Return the router of `/health` and `/api/failures`, reading from this workspace."""
    router = APIRouter()

    @router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/api/failures", response_model=list[FailureOut])
    async def get_failures() -> object:
        return failure_list(workspace)

    return router
