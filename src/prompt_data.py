"""Wraps a document in a fixed tag so that the LLM reads it as data, not as instructions.

Standard library only. It builds no prompt text of its own (`extraction` and `recommendation` do)
and reads no prompt file (`file_reader` does). There is no template substitution.
Implements DEC-016, NFR-001.
"""

import re
from enum import StrEnum


class Tag(StrEnum):
    """The tag names that mark untrusted data in a user text (DEC-016)."""

    CV = "cv"
    JOB_DESCRIPTION = "job_description"
    CANDIDATE_FACTS = "candidate_facts"


def wrap(tag: Tag, content: str) -> str:
    """Put the content between an opening and a closing tag.

    Args:
        tag: The tag to wrap the content in.
        content: The document text. Its copies of any `Tag` are escaped first.

    Returns:
        The tagged text, with the content on its own lines.
    """
    return f"<{tag}>\n{_escape_tags(content)}\n</{tag}>"


def _escape_tags(content: str) -> str:
    """Replace the angle bracket of any opening or closing `Tag` in the content by `&lt;`."""
    names = "|".join(tag.value for tag in Tag)
    return re.sub(rf"<(?=\s*/?\s*(?:{names})(?!\w))", "&lt;", content, flags=re.IGNORECASE)
