"""ProRAG-FL exception-path structured reasoning module."""

from prorag_fl.reasoning.client import (
    MockReasoningClient,
    OpenAIReasoningClient,
    RawReasoningResponse,
    ReasoningClient,
    calculate_token_cost_usd,
)
from prorag_fl.reasoning.engine import ReasoningEngine
from prorag_fl.reasoning.grounding import (
    GroundingCheckResult,
    verify_evidence_grounding,
)
from prorag_fl.reasoning.prompt_builder import (
    PROMPT_VERSION,
    SYSTEM_PROMPT_CONTRACT,
    assemble_reasoning_prompt,
    build_user_prompt,
    package_evidence_structurally,
)
from prorag_fl.reasoning.sanitizer import (
    APPROVED_EVENT_FIELDS,
    FORBIDDEN_KEYWORDS,
    SanitizerViolationError,
    pseudonymize_event_id,
    sanitize_security_event,
)

__all__ = [
    "ReasoningEngine",
    "ReasoningClient",
    "MockReasoningClient",
    "OpenAIReasoningClient",
    "RawReasoningResponse",
    "calculate_token_cost_usd",
    "verify_evidence_grounding",
    "GroundingCheckResult",
    "assemble_reasoning_prompt",
    "build_user_prompt",
    "package_evidence_structurally",
    "SYSTEM_PROMPT_CONTRACT",
    "PROMPT_VERSION",
    "sanitize_security_event",
    "pseudonymize_event_id",
    "SanitizerViolationError",
    "APPROVED_EVENT_FIELDS",
    "FORBIDDEN_KEYWORDS",
]
