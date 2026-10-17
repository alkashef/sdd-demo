"""The entry point: loads the settings, sets up logging, connects the modules and starts the server.

It only imports and connects modules and holds no logic (DEC-007): the pipeline builds the
workspace, `src.api.app` creates the app and uvicorn serves it. It is the only module that imports
`src.config` (design section 2.1). Implements DEC-007, DEC-013 and NFR-002.
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import date
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from src import file_reader, llm_client, vector_store
from src.api.app import create_app
from src.config import LogSettings, Settings, load_settings
from src.llm_client import LlmClient, LlmClientOptions
from src.pipeline import Pipeline, PipelineServices, PipelineSettings
from src.records import YearMonth
from src.vector_store import VectorStore

logger = logging.getLogger(__name__)

type ServerRunner = Callable[[FastAPI, str, int], None]


def configure_logging(settings: LogSettings) -> None:
    """Log plain text, one line per event, to the console and to the log file."""
    settings.file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=settings.level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(settings.file, encoding="utf-8")],
        force=True,
    )


def start(
    settings: Settings, services: PipelineServices, today: YearMonth, serve: ServerRunner
) -> None:
    """Run the pipeline, create the app over the workspace and hand it to the server.

    Args:
        settings: Every setting. The API key is hidden from its text (NFR-002).
        services: The file reader, the LLM client and the two vector stores.
        today: The current month, for the calculated attributes.
        serve: Serves the app on a host and a port. Blocks until the server stops.
    """
    logger.info("Starting with settings: %s", settings)
    data = settings.data
    pipeline = Pipeline(
        services,
        PipelineSettings(
            data.cv_folder,
            data.job_folder,
            data.extract_prompt_path,
            data.match_prompt_path,
            settings.llm.max_concurrency,
        ),
    )
    workspace = asyncio.run(pipeline.run(today))
    app = create_app(workspace, settings.server.web_root)
    logger.info("Serving on %s:%d", settings.server.host, settings.server.port)
    serve(app, settings.server.host, settings.server.port)


def _serve_with_uvicorn(app: FastAPI, host: str, port: int) -> None:
    """Serve the app with uvicorn (DEC-002)."""
    uvicorn.run(app, host=host, port=port)


def main() -> None:
    """Create the real collaborators and start the app. Log any error once and stop."""
    settings = load_settings(Path("config/.env"))
    configure_logging(settings.log)
    llm = settings.llm
    chroma = vector_store.create_client()
    services = PipelineServices(
        files=file_reader,
        llm=LlmClient(
            llm_client.create_client(llm.api_key, llm.base_url),
            LlmClientOptions(llm.model, llm.embedding_model, llm.max_tokens, llm.timeout_seconds),
        ),
        cv_index=VectorStore(chroma, "cvs"),
        job_index=VectorStore(chroma, "job_descriptions"),
    )
    today = date.today()
    try:
        start(settings, services, YearMonth(today.year, today.month), _serve_with_uvicorn)
    except Exception:
        logger.exception("The app stopped on an error")
        raise


if __name__ == "__main__":
    main()
