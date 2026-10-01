"""Reasoning Engine coordinator for Phase 8.

Coordinates:
- SecurityEvent allowlist sanitization & firewall verification
- Structural prompt assembly and SHA-256 hash tracking
- Client execution (Mock or OpenAI) with bounded retries
- Post-response evidence grounding verification (never silently repairs hallucinations)
- Comprehensive auditable execution records with token accounting and cost tracking
"""

import logging
import uuid

from prorag_fl.reasoning.client import (
    MockReasoningClient,
    ReasoningClient,
    calculate_token_cost_usd,
)
from prorag_fl.reasoning.grounding import verify_evidence_grounding
from prorag_fl.reasoning.prompt_builder import assemble_reasoning_prompt
from prorag_fl.reasoning.sanitizer import (
    SanitizerViolationError,
    sanitize_security_event,
)
from prorag_fl.schemas.rag import SecurityEvent, VerifiedEvidence
from prorag_fl.schemas.reasoning import (
    ReasoningExecutionRecord,
    SanitizedSecurityEvent,
)

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """Exception-path reasoning engine coordinating the LLM decision workflow."""

    def __init__(
        self,
        client: ReasoningClient | None = None,
        model_id: str = "mock-reasoning-v1",
    ) -> None:
        self.client = client if client is not None else MockReasoningClient(model_id=model_id)
        self.model_id = model_id
        self.execution_history: list[ReasoningExecutionRecord] = []

    def reason(
        self,
        event: SecurityEvent | dict,
        evidence_items: list[VerifiedEvidence],
    ) -> ReasoningExecutionRecord:
        """Execute structured exception-path reasoning over an escalated security event.

        Args:
            event: The escalated SecurityEvent (contains telemetry and OOD metrics, never ground truth)
            evidence_items: At most top-5 verified evidence items from the Hard Provenance Gate

        Returns:
            ReasoningExecutionRecord containing complete audit metadata and structured decision
        """
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        supplied_ids = [e.evidence_id for e in evidence_items]

        # 1. Sanitize event via strict allowlist
        try:
            sanitized_event: SanitizedSecurityEvent = sanitize_security_event(event)
        except SanitizerViolationError as exc:
            logger.error("Security firewall violation during event sanitization: %s", exc)
            record = ReasoningExecutionRecord(
                request_id=request_id,
                event_pseudonym="pse_rejected",
                model_id=self.model_id,
                prompt_version="v1.0.0",
                prompt_hash="",
                supplied_evidence_ids=supplied_ids,
                cited_evidence_ids=[],
                grounding_valid=False,
                unsupported_evidence_ids=[],
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                latency_ms=0.0,
                retries=0,
                status="FIREWALL_REJECTED",
                structured_output=None,
                calculated_cost_usd=0.0,
                error_message=f"Event sanitization firewall violation: {exc}",
            )
            self.execution_history.append(record)
            return record

        # 2. Assemble structured prompt and compute deterministic hash
        sys_prompt, user_prompt, prompt_version, prompt_hash = assemble_reasoning_prompt(
            sanitized_event=sanitized_event,
            evidence_items=evidence_items,
        )

        # 3. Execute reasoning client
        raw_resp = self.client.complete(
            system_prompt=sys_prompt,
            user_prompt=user_prompt,
            supplied_evidence_ids=supplied_ids,
        )

        cost_usd = calculate_token_cost_usd(
            model_id=raw_resp.model_id,
            input_tokens=raw_resp.input_tokens,
            output_tokens=raw_resp.output_tokens,
        )

        # 4. Handle client-level failure or unavailable
        if raw_resp.status != "SUCCESS" or raw_resp.structured_output is None:
            record = ReasoningExecutionRecord(
                request_id=request_id,
                event_pseudonym=sanitized_event.event_pseudonym,
                model_id=raw_resp.model_id,
                prompt_version=prompt_version,
                prompt_hash=prompt_hash,
                supplied_evidence_ids=supplied_ids,
                cited_evidence_ids=[],
                grounding_valid=False,
                unsupported_evidence_ids=[],
                input_tokens=raw_resp.input_tokens,
                output_tokens=raw_resp.output_tokens,
                total_tokens=raw_resp.total_tokens,
                latency_ms=raw_resp.latency_ms,
                retries=raw_resp.retries,
                status=raw_resp.status,
                structured_output=None,
                calculated_cost_usd=cost_usd,
                error_message=raw_resp.error_message,
            )
            self.execution_history.append(record)
            return record

        # 5. Verify evidence grounding
        grounding_result = verify_evidence_grounding(
            output=raw_resp.structured_output,
            supplied_evidence_ids=supplied_ids,
        )

        final_status = "SUCCESS"
        error_msg = None
        if not grounding_result.is_grounded:
            final_status = "UNGROUNDED_EVIDENCE"
            error_msg = grounding_result.error_message
            logger.warning("Reasoning output failed grounding check: %s", error_msg)

        record = ReasoningExecutionRecord(
            request_id=request_id,
            event_pseudonym=sanitized_event.event_pseudonym,
            model_id=raw_resp.model_id,
            prompt_version=prompt_version,
            prompt_hash=prompt_hash,
            supplied_evidence_ids=supplied_ids,
            cited_evidence_ids=grounding_result.cited_evidence_ids,
            grounding_valid=grounding_result.is_grounded,
            unsupported_evidence_ids=grounding_result.unsupported_evidence_ids,
            input_tokens=raw_resp.input_tokens,
            output_tokens=raw_resp.output_tokens,
            total_tokens=raw_resp.total_tokens,
            latency_ms=raw_resp.latency_ms,
            retries=raw_resp.retries,
            status=final_status,
            structured_output=raw_resp.structured_output,
            calculated_cost_usd=cost_usd,
            error_message=error_msg,
        )

        self.execution_history.append(record)
        return record
