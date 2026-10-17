# sdd-demo

## What it does

CV Matcher

## Stack

Python 3.12, conda environment `sdd-demo`, pytest, ruff, mypy, chromadb 1.5.9 (in-memory vector store), pydantic 2.14.1 (LLM reply schemas)

## File structure

| Path | Holds |
| --- | --- |
| `src/` | All source code. |
| `tests/` | `unit/` and `e2e/` tests. |
| `docs/` | Workflow, spec, design, and plan. |
| `config/` | `.env` (never committed) and `.env.example`. |
| `scripts/` | `check.py` (the checks), `milestones-runner.py`, `cleanup.py`, setup scripts. |
| `.claude/` | Claude Code settings, including the hook that checks each edit. |
| `.githooks/` | `pre-commit`: refuses a commit unless the checks pass. |
| `.vscode/` | Shared editor settings. |
| `data/` | Input and runtime data. |
| `models/` | Downloaded model weights (never committed). |
| `prompts/` | LLM prompt files. |

## Setup

```bash
conda create -n sdd-demo python=3.12
conda activate sdd-demo
pip install -r requirements.txt
```

Copy `config/.env.example` to `config/.env` and fill in the values.

External dependencies (LLM server, models, API keys): none yet. Explain here how to set up and check each one before the first run.

After a fresh clone, turn on the pre-commit hook, which refuses a commit unless the checks pass:

```bash
git config core.hooksPath .githooks
```

## How to run

```bash
python main.py
```

## How to test

```bash
python -m pytest --cov=src --cov-branch --cov-fail-under=80
```
