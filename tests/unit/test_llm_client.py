import logging
from types import SimpleNamespace
from typing import Any, cast

import openai
import pytest
from openai import AsyncOpenAI
from pydantic import BaseModel

from src.llm_client import LlmClient, LlmClientOptions, create_client
from src.ports import LlmError, LlmOutputError

API_KEY = "sk-test-secret-0123456789"


class Reply(BaseModel):
    answer: str


class FakeResponses:
    def __init__(self, result: Any = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def parse(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.result


class FakeEmbeddings:
    def __init__(self, result: Any = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.result


class FakeSdk:
    def __init__(self, responses: FakeResponses, embeddings: FakeEmbeddings) -> None:
        self.responses = responses
        self.embeddings = embeddings


def make_options() -> LlmClientOptions:
    return LlmClientOptions(
        model="chat-model-1", embedding_model="embed-model-1", max_tokens=321, timeout_seconds=17
    )


def make_client(
    responses: FakeResponses | None = None, embeddings: FakeEmbeddings | None = None
) -> LlmClient:
    sdk = FakeSdk(responses or FakeResponses(), embeddings or FakeEmbeddings())
    return LlmClient(cast(AsyncOpenAI, sdk), make_options())


def parsed_response(answer: str) -> SimpleNamespace:
    return SimpleNamespace(output_parsed=Reply(answer=answer), output=[], output_text="")


def refusal_response(text: str) -> SimpleNamespace:
    refusal = SimpleNamespace(type="refusal", refusal=text)
    message = SimpleNamespace(type="message", content=[refusal])
    return SimpleNamespace(output_parsed=None, output=[message], output_text="")


def status_error(error_type: type[openai.APIStatusError], status: int, message: str) -> Exception:
    response = SimpleNamespace(status_code=status, headers={}, request=None)
    return error_type(message, response=cast(Any, response), body=None)


async def test_dec_003_complete_returns_the_parsed_reply():
    client = make_client(FakeResponses(parsed_response("42")))

    reply = await client.complete("system text", "user text", Reply)

    assert reply == Reply(answer="42")


async def test_nfr_001_complete_sends_only_given_system_and_user_text():
    responses = FakeResponses(parsed_response("42"))
    client = make_client(responses)

    await client.complete("system text", "user text", Reply)

    call = responses.calls[0]
    assert call["instructions"] == "system text"
    assert call["input"] == "user text"
    assert call["text_format"] is Reply
    assert call["store"] is False


async def test_dec_003_model_timeout_and_token_limit_come_from_settings():
    responses = FakeResponses(parsed_response("42"))
    embeddings = FakeEmbeddings(SimpleNamespace(data=[SimpleNamespace(embedding=[0.5])]))
    client = make_client(responses, embeddings)

    await client.complete("s", "u", Reply)
    await client.embed("text")

    assert responses.calls[0]["model"] == "chat-model-1"
    assert responses.calls[0]["max_output_tokens"] == 321
    assert responses.calls[0]["timeout"] == 17
    assert embeddings.calls[0]["model"] == "embed-model-1"
    assert embeddings.calls[0]["timeout"] == 17


async def test_dec_003_embed_returns_vector():
    embeddings = FakeEmbeddings(SimpleNamespace(data=[SimpleNamespace(embedding=[0.25, -0.5])]))
    client = make_client(embeddings=embeddings)

    vector = await client.embed("some text")

    assert vector == [0.25, -0.5]
    assert embeddings.calls[0]["input"] == "some text"


async def test_err_001_provider_failure_raises_llm_error_naming_cause():
    request = SimpleNamespace(url="https://example.invalid")
    error = openai.APIConnectionError(request=cast(Any, request))
    client = make_client(FakeResponses(error=error))

    with pytest.raises(LlmError) as caught:
        await client.complete("s", "u", Reply)

    assert "chat-model-1" in str(caught.value)
    assert "could not be reached" in str(caught.value)
    assert caught.value.__cause__ is error


async def test_err_001_timeout_names_the_limit():
    request = SimpleNamespace(url="https://example.invalid")
    error = openai.APITimeoutError(request=cast(Any, request))
    client = make_client(embeddings=FakeEmbeddings(error=error))

    with pytest.raises(LlmError) as caught:
        await client.embed("text")

    assert "embed-model-1" in str(caught.value)
    assert "timed out after 17 seconds" in str(caught.value)


async def test_err_001_rejected_request_raises_llm_error():
    error = status_error(openai.AuthenticationError, 401, "bad credentials")
    client = make_client(FakeResponses(error=error))

    with pytest.raises(LlmError) as caught:
        await client.complete("s", "u", Reply)

    assert "HTTP 401" in str(caught.value)
    assert "AuthenticationError" in str(caught.value)


async def test_err_001_embedding_rejection_raises_llm_error():
    error = status_error(openai.RateLimitError, 429, "slow down")
    client = make_client(embeddings=FakeEmbeddings(error=error))

    with pytest.raises(LlmError) as caught:
        await client.embed("text")

    assert "HTTP 429" in str(caught.value)


async def test_err_001_other_sdk_error_names_its_type():
    client = make_client(FakeResponses(error=openai.OpenAIError("odd")))

    with pytest.raises(LlmError) as caught:
        await client.complete("s", "u", Reply)

    assert "OpenAIError" in str(caught.value)


async def test_err_001_embedding_without_data_raises_llm_error():
    client = make_client(embeddings=FakeEmbeddings(SimpleNamespace(data=[])))

    with pytest.raises(LlmError) as caught:
        await client.embed("text")

    assert "no embedding" in str(caught.value)


async def test_dec_011_refusal_raises_llm_output_error_with_raw_output():
    client = make_client(FakeResponses(refusal_response("I cannot help with that")))

    with pytest.raises(LlmOutputError) as caught:
        await client.complete("s", "u", Reply)

    assert caught.value.raw_output == "I cannot help with that"
    assert "refused" in str(caught.value)


async def test_dec_011_empty_reply_raises_llm_output_error_with_raw_output():
    response = SimpleNamespace(output_parsed=None, output=[], output_text="partial text")
    client = make_client(FakeResponses(response))

    with pytest.raises(LlmOutputError) as caught:
        await client.complete("s", "u", Reply)

    assert caught.value.raw_output == "partial text"


async def test_dec_011_reply_that_misses_the_schema_raises_llm_output_error():
    def invalid_reply() -> Exception:
        try:
            Reply.model_validate_json('{"wrong": 1}')
        except ValueError as err:
            return err
        raise AssertionError("the reply should be invalid")

    client = make_client(FakeResponses(error=invalid_reply()))

    with pytest.raises(LlmOutputError) as caught:
        await client.complete("s", "u", Reply)

    assert "does not fit the schema" in str(caught.value)
    assert "wrong" in caught.value.raw_output


async def test_nfr_002_api_key_not_in_error_or_log(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.DEBUG)
    error = status_error(openai.AuthenticationError, 401, f"Incorrect API key: {API_KEY}")
    client = make_client(FakeResponses(error=error), FakeEmbeddings(error=error))

    with pytest.raises(LlmError) as chat_caught:
        await client.complete("s", "u", Reply)
    with pytest.raises(LlmError) as embed_caught:
        await client.embed("text")

    assert API_KEY not in str(chat_caught.value)
    assert API_KEY not in str(embed_caught.value)
    assert API_KEY not in caplog.text


def test_dec_003_created_client_uses_base_url_and_never_retries():
    client = create_client(API_KEY, "https://llm.example.invalid/v1")

    assert str(client.base_url) == "https://llm.example.invalid/v1/"
    assert client.max_retries == 0
