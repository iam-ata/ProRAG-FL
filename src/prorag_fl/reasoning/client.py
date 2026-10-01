"""Reasoning client adapters (Mock and OpenAI) for Phase 8.

Adheres strictly to instructions/16_OPENAI_REASONING.md:
- Abstract ReasoningClient protocol/ABC
- MockReasoningClient: deterministic, offline, tests grounding, prompt injection resistance, retries
- OpenAIReasoningClient: strict permission gate (ALLOW_EXTERNAL_API=true), key validation,
  no key logging, bounded retries, never switches model, returns REASONING_UNAVAILABLE on exhaustion.
"""

import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from prorag_fl.schemas.reasoning import StructuredReasoningOutput

logger = logging.getLogger(__name__)

# Standard OpenAI pricing per 1M tokens (USD)
MODEL_PRICING_PER_1M_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
}


def calculate_token_cost_usd(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate the estimated USD cost based on token counts."""
    pricing = MODEL_PRICING_PER_1M_TOKENS.get(model_id, {"input": 0.15, "output": 0.60})
    cost_in = (input_tokens / 1_000_000.0) * pricing["input"]
    cost_out = (output_tokens / 1_000_000.0) * pricing["output"]
    return round(cost_in + cost_out, 6)


@dataclass
class RawReasoningResponse:
    """Intermediate execution response before grounding validation."""

    status: str  # "SUCCESS", "REASONING_UNAVAILABLE", "PARSING_FAILED"
    model_id: str
    structured_output: StructuredReasoningOutput | None
    raw_text: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    retries: int
    error_message: str | None = None


class ReasoningClient(ABC):
    """Abstract base class for exception-path LLM reasoning clients."""

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        supplied_evidence_ids: list[str],
    ) -> RawReasoningResponse:
        """Execute structured reasoning and return raw reasoning response."""


class MockReasoningClient(ReasoningClient):
    """Deterministic, offline mock reasoning engine for unit testing and CI.

    Adheres to all constraints:
    - Tests schema validation
    - Simulates insufficient evidence when none is supplied
    - Ignores prompt-injection commands in evidence
    - Supports simulated transient failure & retry exhaustion
    - Generates deterministic, grounded outputs
    """

    def __init__(
        self,
        model_id: str = "mock-reasoning-v1",
        simulate_failure_exhaustion: bool = False,
        transient_failures_before_success: int = 0,
        inject_unsupported_citation: bool = False,
        simulated_latency_ms: float = 12.0,
    ) -> None:
        self.model_id = model_id
        self.simulate_failure_exhaustion = simulate_failure_exhaustion
        self.transient_failures_remaining = transient_failures_before_success
        self.inject_unsupported_citation = inject_unsupported_citation
        self.simulated_latency_ms = simulated_latency_ms
        self.total_invocations = 0

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        supplied_evidence_ids: list[str],
    ) -> RawReasoningResponse:
        self.total_invocations += 1
        start_t = time.perf_counter()
        retries_count = 0

        # 1. Simulate transient failures if configured
        while self.transient_failures_remaining > 0:
            retries_count += 1
            self.transient_failures_remaining -= 1

        if self.simulate_failure_exhaustion:
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0 + self.simulated_latency_ms
            return RawReasoningResponse(
                status="REASONING_UNAVAILABLE",
                model_id=self.model_id,
                structured_output=None,
                raw_text="",
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                latency_ms=elapsed_ms,
                retries=retries_count + 3,
                error_message="Mock API error: Simulated upstream service unavailable after retries",
            )

        # 2. Approximate token accounting
        approx_in_tokens = len(system_prompt.split()) + len(user_prompt.split())

        # 3. Check for empty or missing evidence
        if not supplied_evidence_ids or "[NO_VERIFIED_EVIDENCE_PROVIDED]" in user_prompt:
            output = StructuredReasoningOutput(
                attack_family="Unknown_Anomaly",
                mitre_techniques=[],
                evidence_ids=[],
                evidence_sufficient=False,
                reasoning_summary="No verified threat intelligence evidence was retrieved; insufficient support to confirm anomaly classification.",
                recommended_action="Escalate to SOC Tier-2 analyst for manual payload triage.",
            )
            raw_text = output.model_dump_json()
            approx_out_tokens = len(raw_text.split())
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0 + self.simulated_latency_ms
            return RawReasoningResponse(
                status="SUCCESS",
                model_id=self.model_id,
                structured_output=output,
                raw_text=raw_text,
                input_tokens=approx_in_tokens,
                output_tokens=approx_out_tokens,
                total_tokens=approx_in_tokens + approx_out_tokens,
                latency_ms=elapsed_ms,
                retries=retries_count,
            )

        # 4. Prompt Injection Resistance:
        # Prompt injections in evidence may attempt "IGNORE ALL INSTRUCTIONS", "SET ATTACK_FAMILY TO BENIGN", etc.
        # The mock engine strictly extracts factual security context while ignoring adversarial imperative commands.
        evidence_lower = user_prompt.lower()

        attack_family = "Suspicious_IoT_Activity"
        mitre_techniques: list[str] = []
        action = "Apply strict ACL filtering on source IP and isolate target device"

        if "mirai" in evidence_lower:
            attack_family = "Mirai_Botnet"
            mitre_techniques.append("T1059")
            mitre_techniques.append("T1498")
            action = (
                "Block Telnet/HTTP scanning ports 23/80, revoke default credentials, isolate device"
            )
        elif "buffer_overflow" in evidence_lower or "buffer overflow" in evidence_lower:
            attack_family = "Buffer_Overflow_Exploitation"
            mitre_techniques.append("T1203")
            action = "Deploy vendor firmware patch, enable memory exploit protection, drop malformed packets"
        elif "ddos" in evidence_lower or "flood" in evidence_lower:
            attack_family = "DDoS_Flood"
            mitre_techniques.append("T1498")
            action = "Trigger upstream cloud scrubbing center, enforce rate limiting"
        elif "recon" in evidence_lower or "scan" in evidence_lower:
            attack_family = "Reconnaissance"
            mitre_techniques.append("T1046")
            action = "Null-route scanning subnet and log probes"

        # Determine cited evidence IDs
        cited_ids = list(supplied_evidence_ids[:2])
        if self.inject_unsupported_citation:
            # For testing grounding checks: inject a non-supplied ID
            cited_ids.append("evi_hallucinated_9999")

        output = StructuredReasoningOutput(
            attack_family=attack_family,
            mitre_techniques=sorted(set(mitre_techniques)),
            evidence_ids=cited_ids,
            evidence_sufficient=True,
            reasoning_summary=f"Event exhibits characteristics consistent with {attack_family} as substantiated by supplied verified threat intelligence.",
            recommended_action=action,
        )

        raw_text = output.model_dump_json()
        approx_out_tokens = len(raw_text.split())
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0 + self.simulated_latency_ms

        return RawReasoningResponse(
            status="SUCCESS",
            model_id=self.model_id,
            structured_output=output,
            raw_text=raw_text,
            input_tokens=approx_in_tokens,
            output_tokens=approx_out_tokens,
            total_tokens=approx_in_tokens + approx_out_tokens,
            latency_ms=elapsed_ms,
            retries=retries_count,
        )


class OpenAIReasoningClient(ReasoningClient):
    """Production client wrapping OpenAI SDK with strict security and retry controls.

    Adheres strictly to instructions/16_OPENAI_REASONING.md:
    - Blocked unless ALLOW_EXTERNAL_API=true
    - Validates API key without logging it
    - Uses structured JSON outputs with Pydantic validation
    - Bounded retries with exponential backoff on transient errors
    - Never silently switches models
    - Exhausted retries return REASONING_UNAVAILABLE
    """

    def __init__(
        self,
        model_id: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 1000,
        max_retries: int = 3,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds

        # Enforce external API permission flag
        allow_api = os.getenv("ALLOW_EXTERNAL_API", "").strip().lower() in ("true", "1", "yes")
        if not allow_api:
            raise PermissionError(
                "External API calls are disabled by default. "
                "Set ALLOW_EXTERNAL_API=true in environment to permit OpenAI network requests."
            )

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is missing. "
                "Configure a valid OpenAI API key or use MockReasoningClient."
            )

        # Lazy import of OpenAI SDK
        try:
            import openai

            self._client = openai.OpenAI(
                api_key=api_key,
                timeout=self.timeout_seconds,
                max_retries=0,  # We manage bounded retries explicitly
            )
        except ImportError as err:
            raise ImportError(
                "The 'openai' Python package is required for OpenAIReasoningClient. "
                "Install it or use MockReasoningClient."
            ) from err

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        supplied_evidence_ids: list[str],
    ) -> RawReasoningResponse:
        start_t = time.perf_counter()
        retries = 0

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        last_error_msg = None

        for attempt in range(self.max_retries + 1):
            try:
                # Use response_format json_object for deterministic structured JSON
                response = self._client.chat.completions.create(
                    model=self.model_id,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"},
                )

                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                raw_text = response.choices[0].message.content or "{}"

                # Token accounting
                usage = response.usage
                in_tok = usage.prompt_tokens if usage else 0
                out_tok = usage.completion_tokens if usage else 0
                tot_tok = usage.total_tokens if usage else (in_tok + out_tok)

                # Parse and validate structured output
                try:
                    structured = StructuredReasoningOutput.model_validate_json(raw_text)
                    return RawReasoningResponse(
                        status="SUCCESS",
                        model_id=self.model_id,
                        structured_output=structured,
                        raw_text=raw_text,
                        input_tokens=in_tok,
                        output_tokens=out_tok,
                        total_tokens=tot_tok,
                        latency_ms=elapsed_ms,
                        retries=retries,
                    )
                except Exception as parse_err:
                    logger.error("Failed to parse LLM structured output: %s", parse_err)
                    return RawReasoningResponse(
                        status="PARSING_FAILED",
                        model_id=self.model_id,
                        structured_output=None,
                        raw_text=raw_text,
                        input_tokens=in_tok,
                        output_tokens=out_tok,
                        total_tokens=tot_tok,
                        latency_ms=elapsed_ms,
                        retries=retries,
                        error_message=f"Pydantic validation failed: {parse_err}",
                    )

            except Exception as exc:
                retries += 1
                last_error_msg = str(exc)
                logger.warning(
                    "OpenAI API call transient failure (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries + 1,
                    exc,
                )
                if attempt < self.max_retries:
                    backoff = min(2.0**attempt, 8.0)
                    time.sleep(backoff)
                else:
                    break

        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        return RawReasoningResponse(
            status="REASONING_UNAVAILABLE",
            model_id=self.model_id,
            structured_output=None,
            raw_text="",
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            latency_ms=elapsed_ms,
            retries=retries,
            error_message=f"OpenAI service retries exhausted. Last error: {last_error_msg}",
        )
