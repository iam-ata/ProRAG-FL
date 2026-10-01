"""Federated Learning Poisoning Attacks.

Implements standard, config-driven adversarial perturbations for FL:
- LabelFlippingAttacker: Targeted and untargeted label poisoning with immutable manifests.
- SignFlippingAttacker: Untargeted gradient/update inversion with explicit scaling.
- ModelReplacementAttacker: Bagdasaryan et al. (2020) model replacement attack.

Adheres strictly to instructions/18_ATTACKS_AND_THREAT_MODEL.md.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np

from prorag_fl.attacks.schemas import AttackManifest


class LabelFlippingAttacker:
    """Config-driven targeted and untargeted label flipping attack."""

    def __init__(
        self,
        source_class: int | None = None,
        target_class: int | None = None,
        poison_fraction: float = 0.5,
        num_classes: int = 3,
        seed: int = 42,
    ) -> None:
        self.source_class = source_class
        self.target_class = target_class
        self.poison_fraction = poison_fraction
        self.num_classes = num_classes
        self.seed = seed
        self.is_targeted = source_class is not None and target_class is not None

    def poison_dataset(
        self,
        x: np.ndarray,
        y: np.ndarray,
        client_id: str = "malicious_client",
    ) -> tuple[np.ndarray, np.ndarray, AttackManifest]:
        """Apply deterministic label flipping to local training partition."""
        rng = np.random.default_rng(self.seed)
        y_poisoned = np.copy(y)
        n_samples = len(y)

        if self.is_targeted:
            # Targeted label flip: only modify source_class samples
            eligible_indices = np.where(y == self.source_class)[0]
            num_to_poison = int(len(eligible_indices) * self.poison_fraction)
            if num_to_poison > 0:
                selected_indices = rng.choice(eligible_indices, size=num_to_poison, replace=False)
                y_poisoned[selected_indices] = self.target_class
            total_poisoned = num_to_poison
            attack_type = "targeted_label_flipping"
        else:
            # Untargeted label flip: cycle label (y + 1) % C
            num_to_poison = int(n_samples * self.poison_fraction)
            if num_to_poison > 0:
                selected_indices = rng.choice(
                    np.arange(n_samples), size=num_to_poison, replace=False
                )
                y_poisoned[selected_indices] = (y[selected_indices] + 1) % self.num_classes
            total_poisoned = num_to_poison
            attack_type = "untargeted_label_flipping"

        config_dict = {
            "attack_type": attack_type,
            "source_class": self.source_class,
            "target_class": self.target_class,
            "poison_fraction": self.poison_fraction,
            "num_classes": self.num_classes,
            "seed": self.seed,
        }
        cfg_hash = hashlib.sha256(json.dumps(config_dict, sort_keys=True).encode()).hexdigest()[:16]

        manifest = AttackManifest(
            attack_id=f"atk_lf_{cfg_hash}",
            attack_type=attack_type,
            source_class=self.source_class,
            target_class=self.target_class,
            poison_fraction=self.poison_fraction,
            malicious_client_ids=[client_id],
            total_poisoned_samples=total_poisoned,
            config_hash=cfg_hash,
            parameters=config_dict,
        )

        return x, y_poisoned, manifest


class SignFlippingAttacker:
    """Untargeted update poisoning via gradient sign inversion and scaling."""

    def __init__(self, scaling_factor: float = 1.0) -> None:
        self.scaling_factor = scaling_factor

    def poison_update(
        self,
        local_weights: dict[str, np.ndarray],
        global_weights: dict[str, np.ndarray],
        client_id: str = "malicious_client",
    ) -> tuple[dict[str, np.ndarray], AttackManifest]:
        """Invert update direction: w_poison = w_global - gamma * (w_local - w_global)."""
        poisoned_weights: dict[str, np.ndarray] = {}

        for k in global_weights.keys():
            diff = local_weights[k] - global_weights[k]
            poisoned_weights[k] = global_weights[k] - (self.scaling_factor * diff)

        config_dict = {
            "attack_type": "sign_flipping",
            "scaling_factor": self.scaling_factor,
        }
        cfg_hash = hashlib.sha256(json.dumps(config_dict, sort_keys=True).encode()).hexdigest()[:16]

        manifest = AttackManifest(
            attack_id=f"atk_sf_{cfg_hash}",
            attack_type="sign_flipping",
            poison_fraction=1.0,
            malicious_client_ids=[client_id],
            total_poisoned_samples=0,
            config_hash=cfg_hash,
            parameters=config_dict,
        )

        return poisoned_weights, manifest


class ModelReplacementAttacker:
    """Bagdasaryan et al. (2020) model replacement scaling attack."""

    def __init__(
        self,
        total_clients: int,
        client_learning_rate: float = 1.0,
        boost_factor: float | None = None,
    ) -> None:
        self.total_clients = total_clients
        self.client_learning_rate = client_learning_rate
        # Default scaling gamma = K / eta
        self.gamma = (
            boost_factor
            if boost_factor is not None
            else (total_clients / max(client_learning_rate, 1e-4))
        )

    def scale_update(
        self,
        target_model_weights: dict[str, np.ndarray],
        global_weights: dict[str, np.ndarray],
        client_id: str = "malicious_client",
    ) -> tuple[dict[str, np.ndarray], AttackManifest]:
        """Scale adversarial weights: w_mal = gamma * (w_target - w_global) + w_global."""
        scaled_weights: dict[str, np.ndarray] = {}

        for k in global_weights.keys():
            diff = target_model_weights[k] - global_weights[k]
            scaled_weights[k] = global_weights[k] + (self.gamma * diff)

        config_dict = {
            "attack_type": "model_replacement",
            "total_clients": self.total_clients,
            "gamma": self.gamma,
        }
        cfg_hash = hashlib.sha256(json.dumps(config_dict, sort_keys=True).encode()).hexdigest()[:16]

        manifest = AttackManifest(
            attack_id=f"atk_mr_{cfg_hash}",
            attack_type="model_replacement",
            poison_fraction=1.0,
            malicious_client_ids=[client_id],
            total_poisoned_samples=0,
            config_hash=cfg_hash,
            parameters=config_dict,
        )

        return scaled_weights, manifest
