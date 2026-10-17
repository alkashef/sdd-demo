import socket
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest
import uvicorn
from playwright.sync_api import Browser, Page, Playwright, sync_playwright
from playwright.sync_api import Error as PlaywrightError

from src.api.app import create_app
from src.records import (
    CalculatedAttributes,
    CvFacts,
    Document,
    Job,
    Recommendation,
    Workspace,
    YearMonth,
)

WEB_ROOT = Path(__file__).resolve().parents[3] / "src" / "web"
BROWSER_CHANNELS = ("msedge", "chrome")
CANDIDATE_COUNT = 40


def _facts(name: str) -> CvFacts:
    last = Job("Analyst", "Acme", "Cairo", "Egypt", YearMonth(2019, 6), None, True, "Reports")
    return CvFacts(name, "Analyst", ["SQL"], "Cairo", "Egypt", "BSc", [last], [])


def _fake_workspace() -> Workspace:
    """Two job descriptions and enough candidates that the page needs to scroll."""
    ids = [f"cv{number:02d}.txt" for number in range(CANDIDATE_COUNT)]
    attributes = CalculatedAttributes(100, 1, 50.5, [3], 80, True)
    return Workspace(
        cvs=[Document(doc_id, f"CV text {doc_id}") for doc_id in ids],
        jobs=[
            Document("j1.txt", "Data Analyst\nWe need numbers."),
            Document("j2.txt", "Engineer\nWe need bridges."),
        ],
        facts={doc_id: _facts(f"Candidate {doc_id[2:4]}") for doc_id in ids},
        attributes={doc_id: attributes for doc_id in ids},
        ranked_candidates={
            "j1.txt": [(doc_id, 0.9 - index / 100) for index, doc_id in enumerate(ids)],
            "j2.txt": [],
        },
        ranked_jobs={doc_id: [("j1.txt", 0.5)] for doc_id in ids},
        recommendations={
            ("j1.txt", ids[0]): Recommendation(True, "Strong fit for the role."),
            ("j1.txt", ids[1]): Recommendation(False, "No analytics experience."),
        },
        failures=[],
    )


@pytest.fixture(scope="session")
def base_url() -> Iterator[str]:
    """Serve the real front end over a fake workspace on a free port of 127.0.0.1."""
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    server = uvicorn.Server(uvicorn.Config(create_app(_fake_workspace(), WEB_ROOT)))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{listener.getsockname()[1]}"
    server.should_exit = True
    thread.join()
    listener.close()


@pytest.fixture(scope="module")
def browser() -> Iterator[Browser]:
    """Drive the installed Edge or Chrome, headless. Playwright downloads no browser.

    Module scope: a running Playwright loop breaks pytest-asyncio tests that run after it.
    """
    with sync_playwright() as playwright:
        browser = _launch(playwright)
        yield browser
        browser.close()


def _launch(playwright: Playwright) -> Browser:
    """Launch the first installed browser of `BROWSER_CHANNELS`, or fail naming them all."""
    for channel in BROWSER_CHANNELS:
        try:
            return playwright.chromium.launch(channel=channel)
        except PlaywrightError:
            continue
    raise RuntimeError(f"No installed browser found among {BROWSER_CHANNELS}.")


@pytest.fixture
def page(browser: Browser, base_url: str) -> Iterator[Page]:
    """A fresh page on the app's start URL, 1280 by 720."""
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    page.goto(base_url)
    yield page
    page.close()
