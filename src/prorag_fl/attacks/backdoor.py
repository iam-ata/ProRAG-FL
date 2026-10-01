"""Tabular Backdoor Trigger Attack for Network Intrusion Detection.

Implements deterministic backdoor trigger embedding for tabular network flow traffic:
- TabularBackdoorAttacker: Configurable trigger patterns on selected modifiable flow features.
- Poisoned local training set generation.
- Triggered evaluation test set synthesis to compute Attack Success Rate (ASR).

Adheres strictly to instructions/18_ATTACKS_AND_THREAT_MODEL.md.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np

from prorag_fl.attacks.schemas import AttackManifest


class TabularBackdoorAttacker:
    """Embeds deterministic watermark triggers into tabular network features."""

    def __init__(
        self,
        target_class: int = 0,
        trigger_features: dict[int, float] | None = None,
        poison_fraction: float = 0.3,
        seed: int = 42,
    ) -> None:
        self.target_class = target_class
        # Default trigger: high-watermark deviations on feature 0 and feature 2
        self.trigger_features = trigger_features or {0: 5.0, 2: 5.0}
        self.poison_fraction = poison_fraction
        self.seed = seed

    def embed_trigger(self, x: np.ndarray) -> np.ndarray:
        """Embed the deterministic trigger pattern into feature vectors."""
        x_triggered = np.copy(x)
        for feat_idx, val in self.trigger_features.items():
            if feat_idx < x_triggered.shape[1]:
                x_triggered[:, feat_idx] = val
        return x_triggered

    def poison_train_data(
        self,
        x_train: np.ndarray,
        y_train: np.ndarray,
        client_id: str = "malicious_backdoor_client",
    ) -> tuple[np.ndarray, np.ndarray, AttackManifest]:
        """Poison a fraction of local training samples with trigger and target label."""
        rng = np.random.default_rng(self.seed)
        n_samples = len(y_train)
        num_to_poison = int(n_samples * self.poison_fraction)

        x_p = np.copy(x_train)
        y_p = np.copy(y_train)

        # Select samples that are NOT already the target class
        non_target_indices = np.where(y_train != self.target_class)[0]
        if len(non_target_indices) > 0 and num_to_poison > 0:
            actual_poison_count = min(num_to_poison, len(non_target_indices))
            selected_indices = rng.choice(
                non_target_indices, size=actual_poison_count, replace=False
            )

            for feat_idx, val in self.trigger_features.items():
                if feat_idx < x_p.shape[1]:
                    x_p[selected_indices, feat_idx] = val
            y_p[selected_indices] = self.target_class
            total_poisoned = actual_poison_count
        else:
            total_poisoned = 0

        config_dict = {
            "attack_type": "tabular_backdoor",
            "target_class": self.target_class,
            "trigger_features": {str(k): float(v) for k, v in self.trigger_features.items()},
            "poison_fraction": self.poison_fraction,
            "seed": self.seed,
        }
        cfg_hash = hashlib.sha256(json.dumps(config_dict, sort_keys=True).encode()).hexdigest()[:16]

        manifest = AttackManifest(
            attack_id=f"atk_bd_{cfg_hash}",
            attack_type="tabular_backdoor",
            target_class=self.target_class,
            poison_fraction=self.poison_fraction,
            malicious_client_ids=[client_id],
            total_poisoned_samples=total_poisoned,
            config_hash=cfg_hash,
            parameters=config_dict,
        )

        return x_p, y_p, manifest

    def create_triggered_test_set(
        self,
        x_test: np.ndarray,
        y_test: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Synthesize a triggered copy of test samples (excluding target class) to evaluate ASR.

        Returns:
            (x_triggered, y_true_clean)
        """
        non_target_mask = y_test != self.target_class
        x_eligible = x_test[non_target_mask]
        y_eligible = y_test[non_target_mask]

        if len(x_eligible) == 0:
            return np.empty((0, x_test.shape[1]), dtype=np.float32), np.empty(0, dtype=np.int64)

        x_triggered = self.embed_trigger(x_eligible)
        return x_triggered, y_eligible

    def evaluate_asr(self, predictions_on_triggered: np.ndarray) -> float:
        """Compute Attack Success Rate: fraction of triggered samples predicted as target_class."""
        if len(predictions_on_triggered) == 0:
            return 0.0
        successes = np.sum(predictions_on_triggered == self.target_class)
        return float(successes / len(predictions_on_triggered))
