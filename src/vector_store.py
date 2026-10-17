"""The only module that talks to Chroma: an in-memory collection of vectors.

Adds vectors by ID and returns every stored item nearest to a query vector by cosine similarity.
It computes no embedding (`llm_client` does) and decides no rank for items without a vector
(`ranking` does). Our code supplies the vectors, so Chroma downloads no model.
Implements RNK-001, JOB-002, CND-003, DEC-004 and DEC-011; `VectorStore` implements `VectorIndex`.
"""

from collections.abc import Sequence

from chromadb import EphemeralClient
from chromadb.api import ClientAPI
from chromadb.config import Settings


def create_client() -> ClientAPI:
    """Return the in-memory Chroma client, with telemetry off (DEC-004)."""
    return EphemeralClient(settings=Settings(anonymized_telemetry=False))


class VectorStore:
    """One Chroma collection that finds stored items by cosine similarity.

    Owns the collection named at construction. The name must be new on the client.
    """

    def __init__(self, client: ClientAPI, collection_name: str) -> None:
        """Create the collection on the client, with the cosine distance."""
        self._collection = client.create_collection(
            collection_name, configuration={"hnsw": {"space": "cosine"}}
        )

    def add(self, item_id: str, vector: list[float]) -> None:
        """Store the vector under the ID."""
        embeddings: list[Sequence[float]] = [vector]
        self._collection.add(ids=[item_id], embeddings=embeddings)

    def nearest(self, vector: list[float]) -> list[tuple[str, float]]:
        """Return every stored item as (ID, similarity), best first, ties by ID."""
        count = self._collection.count()
        if count == 0:
            return []
        query: list[Sequence[float]] = [vector]
        result = self._collection.query(query_embeddings=query, n_results=count)
        distances = result["distances"]
        if distances is None:
            raise ValueError("Chroma returned no distances for the query")
        items = [
            (item_id, 1.0 - distance)
            for item_id, distance in zip(result["ids"][0], distances[0], strict=True)
        ]
        return sorted(items, key=lambda item: (-item[1], item[0]))
