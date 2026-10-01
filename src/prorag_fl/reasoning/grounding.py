"""Grounding verification for LLM reasoning citations.

Adheres strictly to instructions/16_OPENAI_REASONING.md:
"After response:
- returned evidence IDs must be subset of supplied Top-5;
- unsupported identifiers are flagged;
- do not silently repair the answer and score the repaired version."
"""

from pydantic import BaseModel, ConfigDict, Field

from prorag_fl.schemas.reasoning import StructuredReasoningOutput


class GroundingCheckResult(BaseModel):
    """Result of verifying that LLM citations are strictly grounded in supplied evidence."""

    model_config = ConfigDict(extra="forbid")

    is_grounded: bool = Field(
        ...,
        description="True if cited evidence IDs are a strict subset of supplied evidence IDs",
    )
    supplied_evidence_ids: list[str] = Field(default_factory=list)
    cited_evidence_ids: list[str] = Field(default_factory=list)
    unsupported_evidence_ids: list[str] = Field(default_factory=list)
    error_message: str | None = Field(default=None)


def verify_evidence_grounding(
    output: StructuredReasoningOutput,
    supplied_evidence_ids: list[str],
) -> GroundingCheckResult:
    """Verify that cited evidence IDs are strictly supported by the supplied top-5 evidence.

    Never silently repairs hallucinated citations; records the exact discrepancy.
    """
    supplied_set = set(supplied_evidence_ids)
    cited = list(output.evidence_ids)
    cited_set = set(cited)

    unsupported = sorted(cited_set - supplied_set)

    if unsupported:
        return GroundingCheckResult(
            is_grounded=False,
            supplied_evidence_ids=supplied_evidence_ids,
            cited_evidence_ids=cited,
            unsupported_evidence_ids=unsupported,
            error_message=(
                f"Ungrounded citation: Model cited evidence IDs {unsupported} "
                f"which were not present in the supplied evidence set {sorted(supplied_set)}."
            ),
        )

    return GroundingCheckResult(
        is_grounded=True,
        supplied_evidence_ids=supplied_evidence_ids,
        cited_evidence_ids=cited,
        unsupported_evidence_ids=[],
        error_message=None,
    )
