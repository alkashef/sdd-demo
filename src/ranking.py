"""Appends the items that have no score to a ranked list, so that none is dropped.

Pure. It computes no score (`vector_store` does) and ignores the calculated attributes.
Implements MIS-002 and RNK-002.
"""

from collections.abc import Iterable


def append_unscored(
    scored: list[tuple[str, float]], all_ids: Iterable[str]
) -> list[tuple[str, float | None]]:
    """Return the scored items in their order, then every other ID with a `None` score, by ID.

    Args:
        scored: (ID, score) pairs, best first.
        all_ids: Every ID that must appear in the ranking.

    Returns:
        The ranked list. An ID in `all_ids` but not in `scored` comes last with a `None` score.
    """
    ranked: list[tuple[str, float | None]] = list(scored)
    scored_ids = {item_id for item_id, _ in scored}
    ranked.extend((item_id, None) for item_id in sorted(set(all_ids) - scored_ids))
    return ranked
