"""The contracts between the pipeline and the gateways, and the LLM error types.

Holds protocols and exceptions only. It calls no service: `llm_client` implements the first two
protocols and `vector_store` implements the third.
Implements ERR-001, DEC-003, DEC-004, DEC-008 and DEC-011 (design section 4, ports).
"""

from typing import Protocol, TypeVar

SchemaT = TypeVar("SchemaT")


class LlmError(Exception):
    """A call to the LLM service failed. The pipeline records it per item (DEC-008)."""


class LlmOutputError(LlmError):
    """The LLM refused, or returned a reply that does not fit the schema. Keeps the raw output."""

    def __init__(self, message: str, raw_output: str) -> None:
        """Store the message and the raw output the service returned."""
        super().__init__(message)
        self.raw_output = raw_output


class StructuredCompleter(Protocol):
    """Asks the chat model for a reply that fits a schema."""

    async def complete(self, system: str, user: str, schema: type[SchemaT]) -> SchemaT:
        """Return an instance of the schema. Raise `LlmError` on any provider failure."""
        ...


class Embedder(Protocol):
    """Turns a text into a vector."""

    async def embed(self, text: str) -> list[float]:
        """Return the embedding of the text. Raise `LlmError` on any provider failure."""
        ...


class VectorIndex(Protocol):
    """Stores vectors by ID and finds the stored items nearest to a vector."""

    def add(self, item_id: str, vector: list[float]) -> None:
        """Store the vector under the ID."""
        ...

    def nearest(self, vector: list[float]) -> list[tuple[str, float]]:
        """Return every stored item as (ID, similarity), best first, ties by ID."""
        ...
