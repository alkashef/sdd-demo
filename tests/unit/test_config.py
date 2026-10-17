from pathlib import Path

import pytest

from src.config import ConfigError, load_settings

_EXAMPLE = Path(__file__).resolve().parents[2] / "config" / ".env.example"
_FAKE_KEY = "sk-invented-secret"


def _example_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in _EXAMPLE.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            key, _, value = line.partition("=")
            values[key] = value
    return values


def _write_env(tmp_path: Path, overrides: dict[str, str | None]) -> Path:
    values = _example_values()
    values["OPENAI_API_KEY"] = _FAKE_KEY
    for key, value in overrides.items():
        if value is None:
            del values[key]
        else:
            values[key] = value
    env_file = tmp_path / ".env"
    env_file.write_text("\n".join(f"{k}={v}" for k, v in values.items()), encoding="utf-8")
    return env_file


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _example_values():
        monkeypatch.delenv(key, raising=False)


def test_nfr_002_api_key_not_in_settings_repr(tmp_path: Path) -> None:
    settings = load_settings(_write_env(tmp_path, {}))

    assert settings.llm.api_key == _FAKE_KEY
    assert _FAKE_KEY not in repr(settings)


def test_design_2_3_missing_value_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="LLM_MODEL"):
        load_settings(_write_env(tmp_path, {"LLM_MODEL": None}))


def test_design_2_3_empty_secret_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        load_settings(_write_env(tmp_path, {"OPENAI_API_KEY": ""}))


def test_design_2_3_invalid_number_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="SERVER_PORT"):
        load_settings(_write_env(tmp_path, {"SERVER_PORT": "abc"}))


def test_design_2_3_out_of_range_number_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="EVAL_MIN_DATE_MATCH_PERCENT"):
        load_settings(_write_env(tmp_path, {"EVAL_MIN_DATE_MATCH_PERCENT": "101"}))
    with pytest.raises(ConfigError, match="LLM_MAX_TOKENS"):
        load_settings(_write_env(tmp_path, {"LLM_MAX_TOKENS": "0"}))


def test_design_2_3_environment_overrides_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SERVER_PORT", "9100")

    settings = load_settings(_write_env(tmp_path, {"SERVER_PORT": "8000"}))

    assert settings.server.port == 9100


def test_design_2_3_values_are_typed_and_grouped(tmp_path: Path) -> None:
    settings = load_settings(_write_env(tmp_path, {}))

    assert settings.llm.max_tokens == 2048
    assert settings.data.cv_folder == Path("data/sample/cvs")
    assert settings.evaluation.min_date_match_percent == 90
    assert settings.server.host == "127.0.0.1"
    assert settings.log.file == Path("logs/app.log")


def test_design_2_3_env_example_lists_every_setting() -> None:
    design = (Path(__file__).resolve().parents[2] / "docs" / "design.md").read_text(
        encoding="utf-8"
    )
    documented = {
        line.split("`")[1]
        for line in design.split("### 2.3 Settings")[1].split("## 3.")[0].splitlines()
        if line.startswith("| `")
    }

    assert set(_example_values()) == documented


def test_dec_013_env_example_host_is_127_0_0_1() -> None:
    assert _example_values()["SERVER_HOST"] == "127.0.0.1"
