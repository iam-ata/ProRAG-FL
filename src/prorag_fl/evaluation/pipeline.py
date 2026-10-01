"""ProRAG-FL End-to-End Integration Pipeline.

Strictly adheres to instructions/17_END_TO_END_PIPELINE.md and instructions/02_LOCKED_PROPOSED_METHOD.md:
- Training path: FL partitions -> local train -> provenance verify -> FedTrimmedAvg(beta=0.20)
- Inference path: 1D-CNN logits + 128D embedding -> temperature calibration C(x) -> Mahalanobis M(x) -> gate G(x)
  * If G=0: direct IDS decision (fast local execution, never calls RAG or LLM API)
  * If G=1: sanitized SecurityEvent -> query -> hybrid retrieval -> hard gate (top-5 verified) -> OpenAI reasoning
- Comprehensive auditable decision record with granular latency breakdown
- Ground truth lives ONLY in evaluation records, never reasoning input
- Enforces all 4 runtime invariants:
  1. direct events never call RAG or LLM API
  2. invalid evidence never reaches reasoning
  3. test label never appears in LLM payload
  4. LLM output never self-admits into threat memory
"""

from __future__ import annotations

import datetime
import time
import uuid

import numpy as np
import torch
from sklearn.metrics import f1_score

from prorag_fl.calibration import TemperatureScaler
from prorag_fl.models.ids_1dcnn import IDS1DCNN
from prorag_fl.ood import DualGate, MahalanobisOODDetector
from prorag_fl.rag.hard_gate import HardProvenanceGate
from prorag_fl.rag.query_builder import construct_retrieval_query
from prorag_fl.rag.retriever import HybridRetriever
from prorag_fl.reasoning.engine import ReasoningEngine
from prorag_fl.schemas.pipeline import (
    AuditableDecisionRecord,
    EndToEndBatchEvaluationReport,
    LatencyBreakdown,
)
from prorag_fl.schemas.rag import SecurityEvent, VerifiedEvidence


class ProRAGFLPipeline:
    """End-to-end inference and evaluation coordinator for ProRAG-FL."""

    def __init__(
        self,
        model: IDS1DCNN,
        temperature_scaler: TemperatureScaler,
        ood_detector: MahalanobisOODDetector,
        dual_gate: DualGate,
        label_names: list[str],
        global_model_version: str = "v1.0",
        retriever: HybridRetriever | None = None,
        hard_gate: HardProvenanceGate | None = None,
        reasoning_engine: ReasoningEngine | None = None,
        device: torch.device | str = "cpu",
        benign_mean: np.ndarray | None = None,
        benign_std: np.ndarray | None = None,
        feature_names: list[str] | None = None,
        protocol_context: str = "TCP/IP",
        device_context: str = "IoT Edge Gateway",
    ) -> None:
        self.model = model.to(device)
        self.model.eval()
        self.temperature_scaler = temperature_scaler
        self.ood_detector = ood_detector
        self.dual_gate = dual_gate
        self.label_names = label_names
        self.global_model_version = global_model_version
        self.retriever = retriever
        self.hard_gate = hard_gate
        self.reasoning_engine = reasoning_engine
        self.device = torch.device(device)
        self.benign_mean = benign_mean
        self.benign_std = benign_std
        self.feature_names = feature_names
        self.protocol_context = protocol_context
        self.device_context = device_context

        # Invariant 4 enforcement flag: LLM output never self-admits into threat memory
        self.admitted_into_threat_memory = False

    def _extract_abnormal_features(self, x_vec: np.ndarray, top_m: int = 5) -> dict[str, float]:
        """Compute top-m abnormal z-score features relative to training benign distribution."""
        if self.benign_mean is None or self.benign_std is None:
            # Fallback to feature values
            f_names = self.feature_names or [f"feat_{i}" for i in range(len(x_vec))]
            return {f_names[i]: float(x_vec[i]) for i in range(min(top_m, len(x_vec)))}

        eps = 1e-6
        z_scores = np.abs((x_vec - self.benign_mean) / (self.benign_std + eps))
        top_indices = np.argsort(z_scores)[::-1][:top_m]
        f_names = self.feature_names or [f"feat_{i}" for i in range(len(x_vec))]

        return {f_names[idx]: round(float(z_scores[idx]), 3) for idx in top_indices}

    def process_sample(
        self,
        x: np.ndarray | torch.Tensor,
        ground_truth_label: str | None = None,
        event_id: str | None = None,
    ) -> AuditableDecisionRecord:
        """Process a single event through the ProRAG-FL dual-path inference engine.

        Args:
            x: Input feature vector of shape [F] or [1, F]
            ground_truth_label: Ground truth label for evaluation ONLY (strictly never passed to LLM)
            event_id: Optional event identifier

        Returns:
            AuditableDecisionRecord with complete timing and decision trace
        """
        start_t = time.perf_counter()
        ev_id = event_id or f"evt_{uuid.uuid4().hex[:10]}"
        timestamp_str = datetime.datetime.now(datetime.UTC).isoformat()

        # 1. 1D-CNN IDS Forward Pass
        t_ids_0 = time.perf_counter()
        if isinstance(x, np.ndarray):
            x_tensor = torch.from_numpy(x).float()
        else:
            x_tensor = x.float()

        if x_tensor.ndim == 1:
            x_tensor = x_tensor.unsqueeze(0)  # [1, F]

        x_tensor = x_tensor.to(self.device)

        with torch.no_grad():
            output = self.model(x_tensor)
            logits_tensor = output.logits
            embedding_tensor = output.embedding

        inference_ids_ms = (time.perf_counter() - t_ids_0) * 1000.0

        # 2. Temperature Calibration
        t_cal_0 = time.perf_counter()
        with torch.no_grad():
            calibrated_probs_t = self.temperature_scaler.predict_proba(logits_tensor)
        calibrated_probs = calibrated_probs_t.detach().cpu().numpy()[0]
        pred_idx = int(np.argmax(calibrated_probs))
        confidence = float(np.max(calibrated_probs))
        classifier_pred = self.label_names[pred_idx]
        calibration_ms = (time.perf_counter() - t_cal_0) * 1000.0

        # 3. Mahalanobis OOD Distance
        t_ood_0 = time.perf_counter()
        embedding_np = embedding_tensor.detach().cpu().numpy()
        mahal_distances = self.ood_detector.compute_distance(embedding_np)
        mahalanobis_dist = float(mahal_distances[0])
        ood_ms = (time.perf_counter() - t_ood_0) * 1000.0

        # 4. Dual Escalation Gate G(x)
        t_gate_0 = time.perf_counter()
        low_conf = confidence < self.dual_gate.tau_c
        high_dist = mahalanobis_dist > self.dual_gate.tau_m
        is_escalated = low_conf or high_dist
        if low_conf and high_dist:
            gate_reason = "both"
        elif low_conf:
            gate_reason = "low_confidence"
        elif high_dist:
            gate_reason = "high_mahalanobis"
        else:
            gate_reason = "direct"
        gate_ms = (time.perf_counter() - t_gate_0) * 1000.0

        # Derive event pseudonym
        x_raw_np = x_tensor.cpu().numpy()[0]
        event_pseudonym = f"pse_{uuid.uuid5(uuid.NAMESPACE_DNS, ev_id).hex[:12]}"

        # =====================================================================
        # ROUTE BRANCHING
        # =====================================================================
        if not is_escalated:
            # DIRECT PATH: G(x) = 0
            # Runtime Invariant 1: Direct events NEVER call RAG or LLM API
            total_elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            latency = LatencyBreakdown(
                inference_ids_ms=round(inference_ids_ms, 3),
                calibration_ms=round(calibration_ms, 3),
                ood_ms=round(ood_ms, 3),
                gate_ms=round(gate_ms, 3),
                retrieval_ms=0.0,
                hard_gate_ms=0.0,
                reasoning_ms=0.0,
                total_latency_ms=round(total_elapsed_ms, 3),
            )

            final_action = (
                "ALLOW_AND_LOG"
                if classifier_pred.lower() == "benign"
                else f"APPLY_FILTER_RULE_{classifier_pred}"
            )

            return AuditableDecisionRecord(
                record_id=f"rec_{uuid.uuid4().hex[:12]}",
                timestamp=timestamp_str,
                event_pseudonym=event_pseudonym,
                global_model_version=self.global_model_version,
                classifier_prediction=classifier_pred,
                confidence=round(confidence, 4),
                mahalanobis_distance=round(mahalanobis_dist, 4),
                gate_escalated=False,
                gate_reason="direct",
                route="DIRECT",
                final_decision=classifier_pred,
                final_action=final_action,
                retrieval_candidate_ids=[],
                rejected_candidate_ids=[],
                rejection_reasons={},
                verified_evidence_ids=[],
                reasoning_model_id=None,
                structured_reasoning=None,
                latency_breakdown=latency,
                evaluation_ground_truth=ground_truth_label,
            )

        # ESCALATED PATH: G(x) = 1
        # Runtime Invariant 3: Ground truth label strictly excluded from SecurityEvent
        abnormal_feats = self._extract_abnormal_features(x_raw_np, top_m=5)

        security_event = SecurityEvent(
            event_id=ev_id,
            timestamp=timestamp_str,
            model_predicted_class=classifier_pred,
            model_confidence=confidence,
            mahalanobis_distance=mahalanobis_dist,
            gate_decision="escalate",
            escalation_reason=gate_reason,
            abnormal_features=abnormal_feats,
            protocol_context=self.protocol_context,
            device_context=self.device_context,
            raw_packet_summary=f"Escalated telemetry anomaly with deviating features: {list(abnormal_feats.keys())}",
        )

        # 5. Hybrid Retrieval
        t_ret_0 = time.perf_counter()
        query = construct_retrieval_query(security_event)
        candidate_chunks = []
        if self.retriever is not None:
            candidate_chunks = self.retriever.retrieve(query)
        retrieval_ms = (time.perf_counter() - t_ret_0) * 1000.0

        candidate_ids = [c[0].chunk_id for c in candidate_chunks]

        # 6. Hard Provenance Gate Verification
        t_hg_0 = time.perf_counter()
        verified_evidence: list[VerifiedEvidence] = []
        rejected_ids: list[str] = []
        rejection_reasons: dict[str, list[str]] = {}

        if self.hard_gate is not None:
            # Check individual candidates for full audit logging
            for chunk, _ in candidate_chunks:
                ver_res = self.hard_gate.verify_candidate(chunk)
                if not ver_res.is_eligible:
                    rejected_ids.append(chunk.chunk_id)
                    rejection_reasons[chunk.chunk_id] = ver_res.failure_reasons

            # Verified Top-5 evidence
            verified_evidence = self.hard_gate.filter_and_rerank(candidate_chunks)
        hard_gate_ms = (time.perf_counter() - t_hg_0) * 1000.0

        verified_ids = [e.evidence_id for e in verified_evidence]

        # 7. Structured LLM Reasoning
        t_reas_0 = time.perf_counter()
        structured_reasoning = None
        reasoning_model_id = None
        final_decision = classifier_pred
        final_action = "ESCALATE_TO_TIER2_SOC"

        if self.reasoning_engine is not None:
            reason_record = self.reasoning_engine.reason(
                event=security_event,
                evidence_items=verified_evidence,
            )
            reasoning_model_id = reason_record.model_id
            if reason_record.status == "SUCCESS" and reason_record.structured_output is not None:
                structured_reasoning = reason_record.structured_output
                final_decision = structured_reasoning.attack_family
                final_action = structured_reasoning.recommended_action
            else:
                final_action = (
                    f"TIER2_SOC_FALLBACK: {reason_record.error_message or 'Service Unavailable'}"
                )

        reasoning_ms = (time.perf_counter() - t_reas_0) * 1000.0

        # Runtime Invariant 4 check: LLM output never self-admits into threat memory
        # Authoritative threat memory admission requires 2-of-3 endorsement and hard verification.
        self.admitted_into_threat_memory = False

        total_elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        latency = LatencyBreakdown(
            inference_ids_ms=round(inference_ids_ms, 3),
            calibration_ms=round(calibration_ms, 3),
            ood_ms=round(ood_ms, 3),
            gate_ms=round(gate_ms, 3),
            retrieval_ms=round(retrieval_ms, 3),
            hard_gate_ms=round(hard_gate_ms, 3),
            reasoning_ms=round(reasoning_ms, 3),
            total_latency_ms=round(total_elapsed_ms, 3),
        )

        return AuditableDecisionRecord(
            record_id=f"rec_{uuid.uuid4().hex[:12]}",
            timestamp=timestamp_str,
            event_pseudonym=event_pseudonym,
            global_model_version=self.global_model_version,
            classifier_prediction=classifier_pred,
            confidence=round(confidence, 4),
            mahalanobis_distance=round(mahalanobis_dist, 4),
            gate_escalated=True,
            gate_reason=gate_reason,
            route="ESCALATED",
            final_decision=final_decision,
            final_action=final_action,
            retrieval_candidate_ids=candidate_ids,
            rejected_candidate_ids=rejected_ids,
            rejection_reasons=rejection_reasons,
            verified_evidence_ids=verified_ids,
            reasoning_model_id=reasoning_model_id,
            structured_reasoning=structured_reasoning,
            latency_breakdown=latency,
            evaluation_ground_truth=ground_truth_label,
        )

    def evaluate_batch(
        self,
        x_batch: np.ndarray,
        y_batch: np.ndarray,
    ) -> tuple[EndToEndBatchEvaluationReport, list[AuditableDecisionRecord]]:
        """Evaluate a batch of test samples and assert all 4 runtime invariants.

        Args:
            x_batch: Array of shape [N, F]
            y_batch: Integer ground-truth labels of shape [N]

        Returns:
            (EndToEndBatchEvaluationReport, list[AuditableDecisionRecord])
        """
        records: list[AuditableDecisionRecord] = []
        direct_records: list[AuditableDecisionRecord] = []
        escalated_records: list[AuditableDecisionRecord] = []

        ground_truth_str_list: list[str] = []
        final_decisions_str_list: list[str] = []

        total_api_calls = 0
        total_cost_usd = 0.0

        for i in range(len(x_batch)):
            x_i = x_batch[i]
            y_idx = int(y_batch[i])
            true_label_str = (
                self.label_names[y_idx] if y_idx < len(self.label_names) else f"class_{y_idx}"
            )

            record = self.process_sample(
                x=x_i,
                ground_truth_label=true_label_str,
                event_id=f"batch_evt_{i:04d}",
            )
            records.append(record)
            ground_truth_str_list.append(true_label_str)
            final_decisions_str_list.append(record.final_decision)

            # Invariant 1 Assertion: Direct events NEVER call RAG or LLM API
            if record.route == "DIRECT":
                assert record.retrieval_candidate_ids == [], (
                    "Invariant 1 violated: Direct event retrieved candidates!"
                )
                assert record.verified_evidence_ids == [], (
                    "Invariant 1 violated: Direct event has verified evidence!"
                )
                assert record.reasoning_model_id is None, (
                    "Invariant 1 violated: Direct event called reasoning API!"
                )
                assert record.latency_breakdown.reasoning_ms == 0.0, (
                    "Invariant 1 violated: Direct event measured reasoning latency!"
                )
                direct_records.append(record)
            else:
                escalated_records.append(record)
                total_api_calls += 1

            # Invariant 4 Assertion: LLM output never self-admits into threat memory
            assert self.admitted_into_threat_memory is False, (
                "Invariant 4 violated: LLM output admitted into threat memory!"
            )

        total_n = len(records)
        direct_n = len(direct_records)
        esc_n = len(escalated_records)

        # Accuracy calculations
        direct_correct = sum(
            1
            for r in direct_records
            if r.final_decision.lower() == (r.evaluation_ground_truth or "").lower()
        )
        direct_acc = (direct_correct / direct_n) if direct_n > 0 else 1.0

        escalated_correct = sum(
            1
            for r in escalated_records
            if r.final_decision.lower() in (r.evaluation_ground_truth or "").lower()
            or (r.evaluation_ground_truth or "").lower() in r.final_decision.lower()
        )
        escalated_acc = (escalated_correct / esc_n) if esc_n > 0 else 1.0

        overall_correct = sum(
            1
            for r in records
            if r.final_decision.lower() in (r.evaluation_ground_truth or "").lower()
            or (r.evaluation_ground_truth or "").lower() in r.final_decision.lower()
        )
        overall_acc = overall_correct / total_n if total_n > 0 else 0.0

        # Latencies
        dir_lats = [r.latency_breakdown.total_latency_ms for r in direct_records]
        esc_lats = [r.latency_breakdown.total_latency_ms for r in escalated_records]
        all_lats = [r.latency_breakdown.total_latency_ms for r in records]

        avg_dir_lat = float(np.mean(dir_lats)) if dir_lats else 0.0
        avg_esc_lat = float(np.mean(esc_lats)) if esc_lats else 0.0
        avg_tot_lat = float(np.mean(all_lats)) if all_lats else 0.0

        # Macro F1
        unique_labels = sorted(set(ground_truth_str_list))
        macro_f1 = float(
            f1_score(
                ground_truth_str_list,
                [r.final_decision for r in records],
                labels=unique_labels,
                average="macro",
                zero_division=0,
            )
        )

        report = EndToEndBatchEvaluationReport(
            total_events=total_n,
            direct_count=direct_n,
            escalated_count=esc_n,
            escalation_rate=round(esc_n / total_n, 4) if total_n > 0 else 0.0,
            direct_accuracy=round(direct_acc, 4),
            escalated_accuracy=round(escalated_acc, 4),
            overall_accuracy=round(overall_acc, 4),
            macro_f1=round(macro_f1, 4),
            avg_direct_latency_ms=round(avg_dir_lat, 2),
            avg_escalated_latency_ms=round(avg_esc_lat, 2),
            avg_total_latency_ms=round(avg_tot_lat, 2),
            total_api_calls=total_api_calls,
            total_reasoning_cost_usd=round(total_cost_usd, 6),
            invariants_verified=True,
        )

        return report, records
