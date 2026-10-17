"""Loads the settings from `config/.env` and the environment (design section 2.3).

The only module that reads `config/.env` or the environment. Only the entry point imports it.
The code has no defaults: a missing, empty or invalid value raises `ConfigError`.
Implements NFR-002 (the API key is hidden from `repr`) and DEC-013 (host is a setting).
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values


class ConfigError(ValueError):
    """A setting is missing, empty or invalid."""


@dataclass(frozen=True)
class LlmSettings:
    """Settings of the LLM client."""

    api_key: str = field(repr=False)
    base_url: str
    model: str
    max_tokens: int
    embedding_model: str
    timeout_seconds: int
    max_concurrency: int


@dataclass(frozen=True)
class DataSettings:
    """Settings of the input folders and prompt files."""

    cv_folder: Path
    job_folder: Path
    extract_prompt_path: Path
    match_prompt_path: Path


@dataclass(frozen=True)
class EvalSettings:
    """Settings of the evaluation (DEC-017)."""

    ground_truth_path: Path
    gold_jobs_path: Path
    top_k: int
    min_relevant_in_top_k: int
    min_date_match_percent: int


@dataclass(frozen=True)
class ServerSettings:
    """Settings of the HTTP server."""

    web_root: Path
    host: str
    port: int


@dataclass(frozen=True)
class LogSettings:
    """Settings of logging."""

    level: str
    file: Path


@dataclass(frozen=True)
class Settings:
    """Every setting, grouped per component."""

    llm: LlmSettings
    data: DataSettings
    evaluation: EvalSettings
    server: ServerSettings
    log: LogSettings


def _text(values: Mapping[str, str | None], key: str) -> str:
    value = values.get(key)
    if value is None or not value.strip():
        raise ConfigError(f"Setting {key} is missing or empty.")
    return value.strip()


def _int(values: Mapping[str, str | None], key: str, minimum: int, maximum: int | None) -> int:
    raw = _text(values, key)
    try:
        number = int(raw)
    except ValueError as err:
        raise ConfigError(f"Setting {key} must be a whole number.") from err
    if number < minimum or (maximum is not None and number > maximum):
        bound = f"at least {minimum}" if maximum is None else f"from {minimum} to {maximum}"
        raise ConfigError(f"Setting {key} must be {bound}.")
    return number


def load_settings(env_file: Path) -> Settings:
    """Load every setting, with real environment variables overriding the file.

    Args:
        env_file: The `.env` file to read. A missing file is treated as empty.

    Returns:
        The settings, grouped per component.

    Raises:
        ConfigError: If a setting is missing, empty or invalid. The message names the key and
            never shows its value.
    """
    values: dict[str, str | None] = dict(dotenv_values(env_file, encoding="utf-8"))
    values.update(os.environ)
    return Settings(
        llm=LlmSettings(
            api_key=_text(values, "OPENAI_API_KEY"),
            base_url=_text(values, "LLM_BASE_URL"),
            model=_text(values, "LLM_MODEL"),
            max_tokens=_int(values, "LLM_MAX_TOKENS", 1, None),
            embedding_model=_text(values, "EMBEDDING_MODEL"),
            timeout_seconds=_int(values, "LLM_TIMEOUT_SECONDS", 1, None),
            max_concurrency=_int(values, "LLM_MAX_CONCURRENCY", 1, None),
        ),
        data=DataSettings(
            cv_folder=Path(_text(values, "CV_FOLDER")),
            job_folder=Path(_text(values, "JOB_FOLDER")),
            extract_prompt_path=Path(_text(values, "EXTRACT_PROMPT_PATH")),
            match_prompt_path=Path(_text(values, "MATCH_PROMPT_PATH")),
        ),
        evaluation=EvalSettings(
            ground_truth_path=Path(_text(values, "EVAL_GROUND_TRUTH_PATH")),
            gold_jobs_path=Path(_text(values, "EVAL_GOLD_JOBS_PATH")),
            top_k=_int(values, "EVAL_TOP_K", 1, None),
            min_relevant_in_top_k=_int(values, "EVAL_MIN_RELEVANT_IN_TOP_K", 0, None),
            min_date_match_percent=_int(values, "EVAL_MIN_DATE_MATCH_PERCENT", 0, 100),
        ),
        server=ServerSettings(
            web_root=Path(_text(values, "WEB_ROOT")),
            host=_text(values, "SERVER_HOST"),
            port=_int(values, "SERVER_PORT", 1, 65535),
        ),
        log=LogSettings(level=_text(values, "LOG_LEVEL"), file=Path(_text(values, "LOG_FILE"))),
    )
