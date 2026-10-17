"""The only module that calls the OpenAI service (design section 2, gateway).

Implements the `StructuredCompleter` and `Embedder` protocols of `ports` over the async OpenAI SDK.
It does not read prompt files, build prompt text or retry (`extraction` and `recommendation` build
the requests). It never stores the API key: `create_client` hands the key to the SDK once.
Implements ERR-001, NFR-001, NFR-002, DEC-003 and DEC-011.
"""

import logging
from dataclasses import dataclass

import openai
from openai import AsyncOpenAI
from openai.types.responses import ParsedResponse
from pydantic import ValidationError

from src.ports import LlmError, LlmOutputError, SchemaT

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LlmClientOptions:
    """The model names and limits of the client, passed in by the entry point."""

    model: str
    embedding_model: str
    max_tokens: int
    timeout_seconds: int


def create_client(api_key: str, base_url: str) -> AsyncOpenAI:
    """Create the SDK client. It never retries: a failed call fails (`.claude/rules/llm.md`)."""
    return AsyncOpenAI(api_key=api_key, base_url=base_url, max_retries=0)


class LlmClient:
    """Sends chat and embedding requests to the LLM service and maps every failure to `LlmError`."""

    def __init__(self, sdk: AsyncOpenAI, options: LlmClientOptions) -> None:
        """Keep the SDK client and the options."""
        self._sdk = sdk
        self._options = options

    async def complete(self, system: str, user: str, schema: type[SchemaT]) -> SchemaT:
        """Ask the chat model for a reply that fits the schema.

        Args:
            system: The instructions (the prompt file text).
            user: The tagged documents. Nothing else is sent.
            schema: The `pydantic` model the reply must fit.

        Returns:
            The validated reply.

        Raises:
            LlmOutputError: If the model refuses or the reply does not fit the schema. It carries
                the raw output.
            LlmError: If the service is unreachable, times out or rejects the request.
        """
        operation = f"Chat request to model {self._options.model}"
        logger.debug("%s", operation)
        try:
            response = await self._sdk.responses.parse(
                model=self._options.model,
                instructions=system,
                input=user,
                text_format=schema,
                max_output_tokens=self._options.max_tokens,
                timeout=self._options.timeout_seconds,
                store=False,
            )
        except openai.OpenAIError as err:
            raise LlmError(f"{operation} failed: {self._cause(err)}.") from err
        except ValidationError as err:
            raise LlmOutputError(
                f"{operation} returned a reply that does not fit the schema.",
                "; ".join(str(problem["input"]) for problem in err.errors()),
            ) from err
        return self._parsed(response, operation)

    async def embed(self, text: str) -> list[float]:
        """Return the embedding of the text.

        Args:
            text: The text to embed.

        Returns:
            The vector.

        Raises:
            LlmError: If the service is unreachable, times out, rejects the request or returns no
                vector.
        """
        operation = f"Embedding request to model {self._options.embedding_model}"
        logger.debug("%s", operation)
        try:
            response = await self._sdk.embeddings.create(
                model=self._options.embedding_model,
                input=text,
                timeout=self._options.timeout_seconds,
            )
        except openai.OpenAIError as err:
            raise LlmError(f"{operation} failed: {self._cause(err)}.") from err
        if not response.data:
            raise LlmError(f"{operation} returned no embedding.")
        return list(response.data[0].embedding)

    def _cause(self, err: openai.OpenAIError) -> str:
        """Describe a provider failure without the SDK message, which could hold a secret."""
        if isinstance(err, openai.APITimeoutError):
            return f"timed out after {self._options.timeout_seconds} seconds"
        if isinstance(err, openai.APIConnectionError):
            return "the service could not be reached"
        if isinstance(err, openai.APIStatusError):
            return f"the service answered HTTP {err.status_code} ({type(err).__name__})"
        return f"the SDK raised {type(err).__name__}"

    def _parsed(self, response: ParsedResponse[SchemaT], operation: str) -> SchemaT:
        """Return the parsed reply, or raise `LlmOutputError` with the raw output."""
        if response.output_parsed is not None:
            return response.output_parsed
        for item in response.output:
            if item.type != "message":
                continue
            for content in item.content:
                if content.type == "refusal":
                    raise LlmOutputError(f"{operation} was refused.", content.refusal)
        raise LlmOutputError(f"{operation} returned no reply.", response.output_text)
