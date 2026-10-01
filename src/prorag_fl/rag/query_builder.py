"""Query construction for Hybrid RAG from runtime SecurityEvent telemetry."""

from __future__ import annotations

import uuid

from prorag_fl.schemas.rag import RetrievalQuery, SecurityEvent


def construct_retrieval_query(event: SecurityEvent) -> RetrievalQuery:
    """Formulate an expressive CTI search query strictly from runtime-visible fields.

    Adheres strictly to instructions/15_HYBRID_RAG.md:
    "Create query text only from runtime-visible SecurityEvent fields:
    prediction, abnormal-feature descriptions, protocol/device context, time context.
    Never include ground-truth label."
    """
    # 1. Prediction and certainty context
    parts = [
        f"Incident Alert: Model predicted potential threat '{event.model_predicted_class}' "
        f"with confidence {event.model_confidence:.2f} and Mahalanobis OOD distance {event.mahalanobis_distance:.2f}."
    ]

    # 2. Protocol and environment context
    parts.append(
        f"Environment: {event.device_context} operating over protocol {event.protocol_context}."
    )

    # 3. Abnormal telemetry features
    if event.abnormal_features:
        feat_strs = [
            f"{name}={val:.2f}" if isinstance(val, (int, float)) else f"{name}={val}"
            for name, val in list(event.abnormal_features.items())[:6]
        ]
        parts.append(f"Abnormal flow telemetry: {', '.join(feat_strs)}.")

    # 4. Routing diagnostic
    parts.append(f"Dual-gate status: Escalated to CTI RAG due to {event.escalation_reason}.")

    if event.raw_packet_summary:
        parts.append(f"Traffic summary: {event.raw_packet_summary}.")

    query_text = " ".join(parts)
    query_id = f"qry_{uuid.uuid4().hex[:12]}"

    return RetrievalQuery(
        query_id=query_id,
        event_id=event.event_id,
        query_text=query_text,
    )
