"""The app factory: creates FastAPI, includes the routers and mounts the static front end.

Connects the pieces and holds no logic: the routers delegate to `workspace_views`. The only
translation here is an unknown ID, which becomes a 404 with a `detail` message. There is no
authentication and no CORS (DEC-013). Implements DEC-002 and DEC-020.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.candidates import create_candidates_router
from src.api.jobs import create_jobs_router
from src.api.status import create_status_router
from src.records import Workspace
from src.workspace_views import NotFoundError


async def _not_found(_request: Request, error: Exception) -> JSONResponse:
    """Answer an unknown job or candidate ID with 404 and a `detail` message (DEC-020)."""
    return JSONResponse(status_code=404, content={"detail": str(error)})


def create_app(workspace: Workspace, web_root: Path) -> FastAPI:
    """Create the app over a finished workspace and the folder of the static front end.

    Args:
        workspace: The finished workspace (DEC-007). The API only reads it.
        web_root: The folder of the front end, served at `/`. It must exist.

    Returns:
        The FastAPI app. The API routes are included before the static mount, so they win.
    """
    app = FastAPI(title="sdd-demo")
    app.add_exception_handler(NotFoundError, _not_found)
    app.include_router(create_status_router(workspace))
    app.include_router(create_jobs_router(workspace))
    app.include_router(create_candidates_router(workspace))
    app.mount("/", StaticFiles(directory=web_root, html=True), name="web")
    return app
