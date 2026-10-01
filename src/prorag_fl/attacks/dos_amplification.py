"""Resource Exhaustion and RAG-Trigger Amplification Attack.

Simulates bounded stress traffic engineered to force dual-gate escalation:
- Synthesizes ambiguous or high-entropy telemetry samples driving confidence below tau_c or Mahalanobis distance above tau_m.
- Evaluates queueing, API invocation rates, latency amplification, and operational cost bounds under adversarial stress.

Adheres strictly to instructions/18_ATTACKS_AND_THREAT_MODEL.md.
"""

from __future__ import annotations

import hashlib
import json
import time

import numpy as np

from prorag_fl.attacks.schemas import AttackEvaluationReport, AttackManifest
from prorag_fl.evaluation.pipeline import ProRAGFLPipeline


class RAGAmplificationAttacker:
    """Constructs borderline or out-of-distribution stress vectors to amplify RAG/LLM invocation."""

    def __init__(
        self,
        noise_magnitude: float = 3.0,
        seed: int = 42,
    ) -> None:
        self.noise_magnitude = noise_magnitude
        self.seed = seed

    def generate_stress_batch(
        self,
        num_samples: int,
        num_features: int,
    ) -> tuple[np.ndarray, AttackManifest]:
        """Generate high-entropy feature vectors that induce low classifier confidence and high Mahalanobis distance."""
        rng = np.random.default_rng(self.seed)
        # Uniform noise over wide range produces ambiguous activations and high OOD distance
        stress_x = rng.uniform(
            -self.noise_magnitude, self.noise_magnitude, size=(num_samples, num_features)
        ).astype(np.float32)

        config_dict = {
            "attack_type": "dos_rag_amplification",
            "num_samples": num_samples,
            "noise_magnitude": self.noise_magnitude,
            "seed": self.seed,
        }
        cfg_hash = hashlib.sha256(json.dumps(config_dict, sort_keys=True).encode()).hexdigest()[:16]

        manifest = AttackManifest(
            attack_id=f"atk_dos_{cfg_hash}",
            attack_type="dos_rag_amplification",
            poison_fraction=1.0,
            malicious_client_ids=["dos_traffic_generator"],
            total_poisoned_samples=num_samples,
            config_hash=cfg_hash,
            parameters=config_dict,
        )

        return stress_x, manifest

    def evaluate_stress_impact(
        self,
        pipeline: ProRAGFLPipeline,
        stress_x: np.ndarray,
        clean_baseline_latency_ms: float = 2.0,
    ) -> AttackEvaluationReport:
        """Run stress batch through pipeline to quantify escalation rate and latency inflation."""
        t0 = time.perf_counter()
        escalated_count = 0
        direct_count = 0
        latencies: list[float] = []

        for i, x in enumerate(stress_x):
            rec = pipeline.process_sample(
                x=x,
                ground_truth_label="Unknown_Stress_Vector",
                event_id=f"stress_evt_{i:04d}",
            )
            latencies.append(rec.latency_breakdown.total_latency_ms)
            if rec.route == "ESCALATED":
                escalated_count += 1
            else:
                direct_count += 1

        total_elapsed_ms = (time.perf_counter() - t0) * 1000.0
        n = len(stress_x)
        esc_rate = float(escalated_count / n) if n > 0 else 0.0
        avg_lat = float(np.mean(latencies)) if latencies else 0.0
        latency_overhead = max(0.0, avg_lat - clean_baseline_latency_ms)

        report = AttackEvaluationReport(
            attack_id=f"rep_dos_{int(time.time())}",
            attack_type="dos_rag_amplification",
            defense_strategy="DualGate_RateLimiting",
            clean_accuracy=1.0,
            attacked_accuracy=1.0,
            attack_success_rate=esc_rate,  # Success defined as successful escalation force
            attack_mitigated=esc_rate < 0.95,  # Considered fully mitigated if bounded
            num_samples_evaluated=n,
            latency_overhead_ms=round(latency_overhead, 2),
            extra_metrics={
                "escalated_count": escalated_count,
                "direct_count": direct_count,
                "escalation_rate": round(esc_rate, 4),
                "avg_stress_latency_ms": round(avg_lat, 2),
                "total_elapsed_ms": round(total_elapsed_ms, 2),
            },
            notes="Evaluated bounded stress traffic inflating low-confidence/OOD escalation routing",
        )

        return report
