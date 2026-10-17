# sdd-demo

## What it does

CV Matcher reads a folder of plain-text CVs and a folder of plain-text job descriptions. At start-up it extracts facts from each CV with an LLM, calculates attributes from them (employment period, gaps, time since graduation), ranks the CVs for each job description (and the job descriptions for each CV) by embedding similarity, and asks the LLM for one interview recommendation per pair. It then serves the results as a JSON API on `127.0.0.1`. Requirements: `docs/spec.md`. Design: `docs/design.md`.

The browser page that shows the results is not built yet (`src/web/` does not exist), so `python main.py` stops at start-up until it is.

## Stack

Python 3.12, conda environment `sdd-demo`, pytest 9.1.1, ruff 0.17.1, mypy 2.4.0, python-dotenv 1.2.4 (settings), chromadb 1.5.9 (in-memory vector store), pydantic 2.14.1 (LLM reply schemas), openai 3.33.0 (LLM client), fastapi 0.143.3 and uvicorn 0.54.0 (HTTP API), httpx 0.28.1 (API test client), pytest-asyncio 1.4.0 (async tests). Node 22 runs the JavaScript checks.

## File structure

| Path | Holds |
| --- | --- |
| `main.py` | The entry point: loads settings, sets up logging, connects the modules, starts the server. |
| `src/` | All source code. `src/api/` is the HTTP layer. |
| `tests/` | `unit/` and `e2e/` tests. |
| `docs/` | Workflow, spec, design, and plan. |
| `config/` | `.env` (never committed) and `.env.example`. |
| `scripts/` | `check.py` (the checks), `milestones-runner.py`, `cleanup.py`, `lock.py`. |
| `.claude/` | Claude Code settings, including the hook that checks each edit. |
| `.githooks/` | `pre-commit`: refuses a commit unless the checks pass. |
| `.vscode/` | Shared editor settings. |
| `data/` | Input data. `data/sample/` holds the sample CVs and job descriptions. |
| `models/` | Not used: the app has no local model. |
| `prompts/` | LLM prompt files. |
| `logs/` | The log file (created at run time, never committed). |

## Setup

```bash
conda create -n sdd-demo python=3.12
conda activate sdd-demo
pip install -r requirements.txt -c constraints.txt
```

Copy `config/.env.example` to `config/.env` and fill in the values. Every key and its meaning is in the settings table of `docs/design.md`. Only `OPENAI_API_KEY` is empty in the example. A real environment variable overrides `config/.env`. A missing or invalid value stops the app at start-up and names the key.

External dependency: the OpenAI API (`docs/design.md`, DEC-003 and DEC-006). It is the only service the app calls.

1. Create an API key in your OpenAI account and put it in `OPENAI_API_KEY` in `config/.env`. The key is never logged.
2. Check that the key works and that the account can use the models named in `LLM_MODEL` and `EMBEDDING_MODEL`. The model IDs are untested until the first run (DEC-003).
3. Know what is sent: the full CV text and job description text leave the machine for extraction, embedding and recommendation (DEC-006). The sample data is synthetic. Do not point the app at real personal data without deciding that first.
4. A start-up makes about 53 calls for the sample (13 embeddings, 10 extractions, 30 recommendations). Check your rate limits and cost first.

After a fresh clone, turn on the pre-commit hook, which refuses a commit unless the checks pass:

```bash
git config core.hooksPath .githooks
```

## How to run

```bash
python main.py
```

The app reads the folders named in `config/.env`, runs every LLM call, then serves on `SERVER_HOST:SERVER_PORT` (default `127.0.0.1:8000`). The terminal shows the progress. `GET /health` reports liveness; the other endpoints are in section 4 of `docs/design.md`. The log is written to `LOG_FILE`.

## How to test

```bash
python -m pytest --cov=src --cov-branch --cov-fail-under=80
```

`python scripts/check.py` runs every check (ruff, mypy, pytest, and the JavaScript checks). The tests use fakes: they need no `config/.env`, no network and no API key.
