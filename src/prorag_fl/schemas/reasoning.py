"""Pydantic schemas for Phase 8: OpenAI Structured Reasoning & Exception Path Interpreter.

Strictly adheres to instructions/16_OPENAI_REASONING.md and instructions/29_SECURITY_PRIVACY_AND_SECRETS.md:
- Strict output schema with extra="forbid"
- Allowlist-based sanitized event schema
- Execution and audit record tracking tokens, cost, latency, retries, and grounding validity
- Never allows raw ground truth, secrets, or packet payloads
"""

from pydantic import BaseModel, ConfigDict, Field


class StructuredReasoningOutput(BaseModel):
    """Authoritative structured output schema produced by the reasoning LLM.

    Adheres strictly to instructions/16_OPENAI_REASONING.md:
    No free-form response bypasses validation.
    """

    model_config = ConfigDict(extra="forbid")

    attack_family: str = Field(
        ...,
        description="Identified threat or attack family (e.g. Mirai, DDoS-ICMP, Buffer_Overflow, Recon-PortScan, Benign)",
    )
    mitre_techniques: list[str] = Field(
        default_factory=list,
        description="List of verified MITRE ATT&CK technique IDs (e.g. ['T1059', 'T1498'])",
    )
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="List of explicit evidence IDs from the supplied top-5 evidence cited to support the conclusion",
    )
    evidence_sufficient: bool = Field(
        ...,
        description="True if supplied evidence was sufficient to reach a confident interpretation; False otherwise",
    )
    reasoning_summary: str = Field(
        ...,
        description="Concise factual explanation grounded exclusively in supplied telemetry and verified evidence",
    )
    recommended_action: str = Field(
        ...,
        description="Operational mitigation recommendation (e.g. Block IP, Rate Limit, Patch CVE, Terminate Session)",
    )


class SanitizedSecurityEvent(BaseModel):
    """Allowlist-based serialization of a SecurityEvent for LLM consumption.

    Strictly follows instructions/29_SECURITY_PRIVACY_AND_SECRETS.md:
    "SecurityEvent external serialization must use an allowlist of approved fields.
    A blacklist is insufficient because newly added fields could leak unintentionally."
    """

    model_config = ConfigDict(extra="forbid")

    event_pseudonym: str = Field(..., description="Pseudonymized experiment-safe event identifier")
    model_predicted_class: str = Field(
        ..., description="1D-CNN classifier initial class prediction"
    )
    model_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Temperature-calibrated prediction confidence"
    )
    mahalanobis_distance: float = Field(
        ..., ge=0.0, description="Regularized Mahalanobis distance to training in-distribution"
    )
    escalation_reason: str = Field(
        ..., description="Reason for escalation: low_confidence, high_mahalanobis, or both"
    )
    abnormal_features: dict[str, float] = Field(
        default_factory=dict,
        description="Key non-confidential telemetry features that deviated significantly",
    )
    gate_decision: str = Field(
        default="escalate", description="Routing decision: direct or escalate"
    )
    protocol_context: str = Field(
        default="Unknown", description="High-level protocol context (e.g. TCP, UDP, MQTT)"
    )
    device_context: str = Field(
        default="Generic IoT", description="High-level device context (e.g. Smart Meter, Camera)"
    )
    raw_packet_summary: str = Field(
        default="", description="Sanitized, high-level textual summary of the packet header"
    )
    timestamp: str | None = Field(default=None, description="Time context for event evaluation")


class ReasoningExecutionRecord(BaseModel):
    """Comprehensive auditable record of a structured reasoning invocation.

    Adheres strictly to instructions/16_OPENAI_REASONING.md logging contract:
    Model ID, prompt hash, evidence IDs, input/output tokens, latency, retries,
    grounding verification, and calculated cost without logging any secrets.
    """

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(..., description="Unique UUID for this reasoning request")
    event_pseudonym: str = Field(..., description="Event pseudonym identifier")
    model_id: str = Field(..., description="Exact model name/revision used")
    prompt_version: str = Field(..., description="Prompt template version identifier")
    prompt_hash: str = Field(..., description="SHA-256 hash of the complete assembled prompt")
    supplied_evidence_ids: list[str] = Field(
        default_factory=list, description="Evidence IDs provided to the model in top-5"
    )
    cited_evidence_ids: list[str] = Field(
        default_factory=list, description="Evidence IDs cited by the model in output"
    )
    grounding_valid: bool = Field(
        default=True,
        description="True if all cited_evidence_ids are a strict subset of supplied_evidence_ids",
    )
    unsupported_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Any evidence IDs hallucinated or not present in supplied_evidence_ids",
    )
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    latency_ms: float = Field(default=0.0, ge=0.0)
    retries: int = Field(default=0, ge=0)
    status: str = Field(
        ...,
        description="Outcome status: SUCCESS, REASONING_UNAVAILABLE, PARSING_FAILED, UNGROUNDED_EVIDENCE, INJECTION_REJECTED",
    )
    structured_output: StructuredReasoningOutput | None = Field(
        default=None, description="Validated output if parsing succeeded"
    )
    calculated_cost_usd: float = Field(
        default=0.0, ge=0.0, description="Calculated USD cost based on token counts"
    )
    error_message: str | None = Field(
        default=None, description="Detailed error description if execution failed"
    )
