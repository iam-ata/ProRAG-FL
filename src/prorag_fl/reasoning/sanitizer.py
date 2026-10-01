"""Allowlist-based event sanitizer for LLM reasoning.

Adheres strictly to instructions/16_OPENAI_REASONING.md and instructions/29_SECURITY_PRIVACY_AND_SECRETS.md:
"SecurityEvent external serialization must use an allowlist of approved fields.
A blacklist is insufficient because newly added fields could leak unintentionally.
Reject hidden label, secrets, packet payload, raw PCAP, full raw row, model tensors/private keys, unnecessary identifiers."
"""

import hashlib
from typing import Any

from prorag_fl.schemas.rag import SecurityEvent
from prorag_fl.schemas.reasoning import SanitizedSecurityEvent


class SanitizerViolationError(ValueError):
    """Raised when an event contains forbidden fields or violates the serialization firewall."""


# Strict allowlist of approved attributes from SecurityEvent
APPROVED_EVENT_FIELDS = {
    "event_id",
    "timestamp",
    "gate_decision",
    "model_predicted_class",
    "model_confidence",
    "mahalanobis_distance",
    "escalation_reason",
    "abnormal_features",
    "protocol_context",
    "device_context",
    "raw_packet_summary",
}

# Strict blacklist of forbidden keywords that must never appear in keys or serialized dicts
FORBIDDEN_KEYWORDS = {
    "ground_truth",
    "true_label",
    "y_true",
    "label",
    "target",
    "secret",
    "api_key",
    "private_key",
    "pcap",
    "raw_payload",
    "raw_row",
    "tensor",
    "weights",
}


def pseudonymize_event_id(event_id: str, salt: str = "prorag_fl_event_salt") -> str:
    """Derive an experiment-safe pseudonym identifier from an event ID."""
    digest = hashlib.sha256(f"{salt}:{event_id}".encode()).hexdigest()[:12]
    return f"pse_{digest}"


def sanitize_security_event(
    event: SecurityEvent | dict[str, Any],
    pseudonym_salt: str = "prorag_fl_event_salt",
) -> SanitizedSecurityEvent:
    """Serialize a SecurityEvent to an allowlist-approved SanitizedSecurityEvent.

    Verifies that:
    1. No forbidden keywords appear in the event keys or values.
    2. Only explicitly allowlisted fields are retained.
    3. The event ID is pseudonymized to preserve privacy.
    4. Raw payloads or ground truth labels are rejected with SanitizerViolationError.
    """
    if isinstance(event, SecurityEvent):
        raw_dict = event.model_dump()
    elif isinstance(event, dict):
        raw_dict = dict(event)
    else:
        raise SanitizerViolationError(f"Unsupported event type: {type(event)}")

    # 1. Proactive check against forbidden keywords in input dict
    for k in raw_dict:
        k_lower = k.lower()
        for forbidden in FORBIDDEN_KEYWORDS:
            if forbidden in k_lower:
                raise SanitizerViolationError(
                    f"Firewall violation: Forbidden keyword '{forbidden}' detected in field '{k}'"
                )

    # 2. Check for unexpected / non-allowlisted fields
    unapproved_keys = set(raw_dict.keys()) - APPROVED_EVENT_FIELDS
    if unapproved_keys:
        raise SanitizerViolationError(
            f"Firewall violation: Fields not on the approved allowlist: {sorted(unapproved_keys)}"
        )

    # 3. Construct allowlist-sanitized payload
    event_id = str(raw_dict.get("event_id", "evt_unknown"))
    pseudonym = pseudonymize_event_id(event_id, salt=pseudonym_salt)

    # Abnormal features validation
    raw_features = raw_dict.get("abnormal_features", {})
    if not isinstance(raw_features, dict):
        raise SanitizerViolationError("abnormal_features must be a dict of numeric values")

    cleaned_features: dict[str, float] = {}
    for feat_name, val in raw_features.items():
        feat_name_lower = str(feat_name).lower()
        for forbidden in FORBIDDEN_KEYWORDS:
            if forbidden in feat_name_lower:
                raise SanitizerViolationError(
                    f"Firewall violation: Forbidden keyword '{forbidden}' in feature '{feat_name}'"
                )
        try:
            cleaned_features[str(feat_name)] = float(val)
        except (ValueError, TypeError) as err:
            raise SanitizerViolationError(
                f"Feature '{feat_name}' value '{val}' is not a valid float: {err}"
            ) from err

    sanitized = SanitizedSecurityEvent(
        event_pseudonym=pseudonym,
        model_predicted_class=str(raw_dict["model_predicted_class"]),
        model_confidence=float(raw_dict["model_confidence"]),
        mahalanobis_distance=float(raw_dict["mahalanobis_distance"]),
        gate_decision=str(raw_dict.get("gate_decision", "escalate")),
        escalation_reason=str(raw_dict["escalation_reason"]),
        abnormal_features=cleaned_features,
        protocol_context=str(raw_dict.get("protocol_context", "Unknown")),
        device_context=str(raw_dict.get("device_context", "Generic IoT")),
        raw_packet_summary=str(raw_dict.get("raw_packet_summary", "")),
        timestamp=str(raw_dict["timestamp"]) if "timestamp" in raw_dict else None,
    )

    return sanitized
