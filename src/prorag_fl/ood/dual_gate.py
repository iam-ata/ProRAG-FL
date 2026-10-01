"""Dual Escalation Gate combining Calibrated Confidence and Mahalanobis OOD Detection."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, average_precision_score, f1_score, roc_auc_score

from prorag_fl.calibration.temperature_scaling import TemperatureScaler
from prorag_fl.ood.mahalanobis import MahalanobisOODDetector
from prorag_fl.schemas.calibration import GateDecision, GateEvaluationMetrics, GateThresholds


class DualGate:
    """Escalation routing gate conforming to 11_CALIBRATION_AND_OOD.md:

        G(x) = I[ C(x) < tau_c OR M(x) > tau_m ]

    If G(x) == 0 (direct route): Accept fast, local/centralized IDS prediction.
    If G(x) == 1 (escalated): Route to provenance-aware RAG reasoning workflow.
    """

    def __init__(
        self,
        temperature_scaler: TemperatureScaler,
        mahalanobis_detector: MahalanobisOODDetector,
        tau_c: float | None = None,
        tau_m: float | None = None,
    ) -> None:
        self.temperature_scaler = temperature_scaler
        self.mahalanobis_detector = mahalanobis_detector
        self.tau_c = float(tau_c if tau_c is not None else temperature_scaler.tau_c)
        self.tau_m = float(tau_m if tau_m is not None else mahalanobis_detector.tau_m)

    def route_batch(
        self,
        logits: torch.Tensor,
        embeddings: torch.Tensor | np.ndarray,
        event_ids: list[str] | None = None,
        class_names: list[str] | None = None,
    ) -> list[GateDecision]:
        """Make routing decisions for a batch of traffic flow representations.

        Args:
            logits: Classifier logits [B, C].
            embeddings: 128-D latent embeddings [B, 128].
            event_ids: Optional list of sample identifiers.
            class_names: Optional mapping from class index to name.

        Returns:
            List of GateDecision objects.
        """
        # Step 1: Calibrated confidence C(x)
        with torch.no_grad():
            confs_t, preds_t = self.temperature_scaler.predict_confidence(logits)
            confs = confs_t.cpu().numpy()
            preds = preds_t.cpu().numpy()

        # Step 2: Mahalanobis distance M(x)
        distances = self.mahalanobis_detector.compute_distance(embeddings)

        n_samples = len(confs)
        if event_ids is None:
            event_ids = [f"event_{i}" for i in range(n_samples)]

        decisions: list[GateDecision] = []

        for i in range(n_samples):
            c_val = float(confs[i])
            m_val = float(distances[i])
            pred_id = int(preds[i])

            if class_names and pred_id < len(class_names):
                pred_name = class_names[pred_id]
            else:
                pred_name = f"Class_{pred_id}"

            low_conf = c_val < self.tau_c
            high_dist = m_val > self.tau_m
            escalate = low_conf or high_dist

            if low_conf and high_dist:
                reason = "both"
            elif low_conf:
                reason = "low_confidence"
            elif high_dist:
                reason = "high_mahalanobis"
            else:
                reason = "direct"

            decisions.append(
                GateDecision(
                    event_id=event_ids[i],
                    escalate=escalate,
                    confidence=c_val,
                    mahalanobis_distance=m_val,
                    predicted_class_id=pred_id,
                    predicted_class_name=pred_name,
                    reason=reason,
                )
            )

        return decisions

    def evaluate(
        self,
        decisions: list[GateDecision],
        true_labels: np.ndarray | list[int],
        is_held_out: np.ndarray | list[bool],
        dataset_name: str = "dataset",
    ) -> GateEvaluationMetrics:
        """Evaluate gate routing metrics on a test set containing both known and held-out zero-day traffic."""
        y_true = np.asarray(true_labels, dtype=np.int64)
        held_out_mask = np.asarray(is_held_out, dtype=bool)

        escalate_flags = np.array([d.escalate for d in decisions], dtype=bool)
        pred_ids = np.array([d.predicted_class_id for d in decisions], dtype=np.int64)
        distances = np.array([d.mahalanobis_distance for d in decisions], dtype=np.float64)
        confs = np.array([d.confidence for d in decisions], dtype=np.float64)

        # 1. Known traffic metrics
        known_mask = ~held_out_mask
        num_known = int(known_mask.sum())
        num_held_out = int(held_out_mask.sum())

        if num_known > 0:
            known_escalated = escalate_flags[known_mask]
            direct_route_rate = float((~known_escalated).mean())
            false_escalation_rate = float(known_escalated.mean())

            # Performance on directly routed decisions
            direct_mask = known_mask & (~escalate_flags)
            if direct_mask.sum() > 0:
                direct_acc = float(accuracy_score(y_true[direct_mask], pred_ids[direct_mask]))
                direct_f1 = float(
                    f1_score(
                        y_true[direct_mask], pred_ids[direct_mask], average="macro", zero_division=0
                    )
                )
            else:
                direct_acc = 0.0
                direct_f1 = 0.0
        else:
            direct_route_rate = 0.0
            false_escalation_rate = 0.0
            direct_acc = 0.0
            direct_f1 = 0.0

        # 2. Held-out zero-day attack metrics
        if num_held_out > 0:
            held_out_escalated = escalate_flags[held_out_mask]
            held_out_recall = float(held_out_escalated.mean())
        else:
            held_out_recall = 0.0

        # 3. AUROC / AUPR metrics (treating held_out as binary anomaly class = 1)
        m_auroc: float | None = None
        m_aupr: float | None = None
        c_auroc: float | None = None

        if num_held_out > 0 and num_known > 0:
            binary_targets = held_out_mask.astype(int)
            try:
                m_auroc = float(roc_auc_score(binary_targets, distances))
                m_aupr = float(average_precision_score(binary_targets, distances))
                # 1 - Confidence is the anomaly score
                c_auroc = float(roc_auc_score(binary_targets, 1.0 - confs))
            except Exception:
                pass

        return GateEvaluationMetrics(
            dataset_name=dataset_name,
            num_known_samples=num_known,
            num_held_out_samples=num_held_out,
            direct_route_rate=direct_route_rate,
            false_escalation_rate=false_escalation_rate,
            direct_accuracy=direct_acc,
            direct_macro_f1=direct_f1,
            held_out_escalation_recall=held_out_recall,
            mahalanobis_auroc=m_auroc,
            mahalanobis_aupr=m_aupr,
            confidence_auroc=c_auroc,
        )

    def save_thresholds(
        self,
        filepath: Path | str,
        dataset_name: str,
        model_checkpoint_digest: str = "",
    ) -> Path:
        """Save gate thresholds to JSON."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        thresholds = GateThresholds(
            dataset_name=dataset_name,
            tau_c=self.tau_c,
            tau_m=self.tau_m,
            temperature=float(self.temperature_scaler.temperature.item()),
            model_checkpoint_digest=model_checkpoint_digest,
        )
        path.write_text(thresholds.model_dump_json(indent=2), encoding="utf-8")
        return path

    def load_thresholds(self, filepath: Path | str) -> DualGate:
        """Load gate thresholds from JSON."""
        path = Path(filepath)
        thresholds = GateThresholds.model_validate_json(path.read_text(encoding="utf-8"))
        self.tau_c = thresholds.tau_c
        self.tau_m = thresholds.tau_m
        return self
