from __future__ import annotations

from pydantic import BaseModel, Field


class Clause(BaseModel):
    """One numbered provision from Part II."""

    id: str = Field(
        ...,
        description="Clause number as in the document (e.g. '1', '12', '19'). "
        "Use a suffix like '19-Rider' if numbering restarts in a rider.",
    )
    title: str = Field(
        ...,
        description="Short heading or combined heading lines (e.g. 'Condition Of vessel').",
    )
    text: str = Field(
        ...,
        description="Full clause body, excluding strike-through or superseded text.",
    )


class ClauseExtractionResult(BaseModel):
    clauses: list[Clause]
