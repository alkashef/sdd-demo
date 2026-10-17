"""The entry point: loads the settings, sets up logging, connects the modules and starts the server.

It only imports and connects modules and holds no logic (DEC-007): the pipeline builds the
workspace, `src.api.app` creates the app and uvicorn serves it. With `--evaluate` it prints the
evaluation report of `src.evaluation` instead of serving. It is the only module that imports
`src.config` (design section 2.1). Implements DEC-007, DEC-013, DEC-017 and NFR-002.
"""

import argparse
import asyncio
import logging
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from src import evaluation, file_reader, llm_client, vector_store
from src.api.app import create_app
from src.config import LogSettings, Settings, load_settings
from src.llm_client import LlmClient, LlmClientOptions
from src.pipeline import Pipeline, PipelineServices, PipelineSettings
from src.records import Workspace, YearMonth
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


def build_workspace(settings: Settings, services: PipelineServices, today: YearMonth) -> Workspace:
    """Run the pipeline once over the configured folders (DEC-007). The API key stays hidden."""
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
    return asyncio.run(pipeline.run(today))


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
    workspace = build_workspace(settings, services, today)
    app = create_app(workspace, settings.server.web_root)
    logger.info("Serving on %s:%d", settings.server.host, settings.server.port)
    serve(app, settings.server.host, settings.server.port)


def evaluate(settings: Settings, services: PipelineServices, today: YearMonth) -> int:
    """Check the ranking and the extracted job dates against the evaluation files (DEC-017).

    Both files are read and parsed first, so a bad file stops the run before any LLM call.

    Args:
        settings: Every setting.
        services: The file reader, the LLM client and the two vector stores.
        today: The current month, for the calculated attributes.

    Returns:
        0 when both checks pass, 1 when one fails. The report is written to the console.

    Raises:
        EvaluationFileError: If an evaluation file has a wrong format.
    """
    files = services.files
    limits = settings.evaluation
    relevant = evaluation.parse_ground_truth(files.read_text(limits.ground_truth_path))
    gold = evaluation.parse_gold_jobs(files.read_text(limits.gold_jobs_path))
    workspace = build_workspace(settings, services, today)
    report = evaluation.evaluate(
        workspace,
        relevant,
        gold,
        evaluation.EvaluationLimits(
            limits.top_k, limits.min_relevant_in_top_k, limits.min_date_match_percent
        ),
    )
    sys.stdout.write(f"{evaluation.format_report(report)}\n")
    return 0 if report.passed else 1


def _serve_with_uvicorn(app: FastAPI, host: str, port: int) -> None:
    """Serve the app with uvicorn (DEC-002)."""
    uvicorn.run(app, host=host, port=port)


def _wants_evaluation() -> bool:
    """Return True when the command line has `--evaluate`."""
    parser = argparse.ArgumentParser(description="CV matcher: serve the app or evaluate it.")
    parser.add_argument(
        "--evaluate", action="store_true", help="print the NFR-004 and NFR-005 report and exit"
    )
    return bool(parser.parse_args().evaluate)


def _create_services(settings: Settings) -> PipelineServices:
    """Create the real file reader, LLM client and vector stores."""
    llm = settings.llm
    chroma = vector_store.create_client()
    return PipelineServices(
        files=file_reader,
        llm=LlmClient(
            llm_client.create_client(llm.api_key, llm.base_url),
            LlmClientOptions(llm.model, llm.embedding_model, llm.max_tokens, llm.timeout_seconds),
        ),
        cv_index=VectorStore(chroma, "cvs"),
        job_index=VectorStore(chroma, "job_descriptions"),
    )


def main() -> None:
    """Create the real collaborators and start the app, or evaluate it with `--evaluate`.

    Log any error once and stop. The exit code is 1 when an evaluation check fails.
    """
    evaluating = _wants_evaluation()
    settings = load_settings(Path("config/.env"))
    configure_logging(settings.log)
    services = _create_services(settings)
    today = date.today()
    month = YearMonth(today.year, today.month)
    try:
        if evaluating:
            sys.exit(evaluate(settings, services, month))
        start(settings, services, month, _serve_with_uvicorn)
    except Exception:
        logger.exception("The app stopped on an error")
        raise


if __name__ == "__main__":
    main()
