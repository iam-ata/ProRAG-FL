"""Federated learning simulation runner using Flower and local partitioned data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import flwr as fl
import numpy as np
import torch
from flwr.common import (
    ndarrays_to_parameters,
)

from prorag_fl.core.seeding import set_seed
from prorag_fl.federated.client import FlowerIDSClient
from prorag_fl.federated.provenance_envelope import (
    ProvenanceVerifier,
    compute_ndarrays_digest,
    serialize_ndarrays,
)
from prorag_fl.federated.strategies import (
    ProvenanceGatedFedTrimmedAvg,
    create_fedavg_strategy,
    create_fedtrimmedavg_strategy,
    create_multikrum_strategy,
)
from prorag_fl.models.ids_1dcnn import IDS1DCNN
from prorag_fl.models.trainer import IDSTrainer
from prorag_fl.models.utils import create_ids_data_loader
from prorag_fl.schemas.federated import FLSimulationResult, RoundAuditLog


def run_fl_simulation(
    strategy_name: str,
    dataset_name: str,
    num_clients: int,
    num_rounds: int,
    client_train_data: dict[int, tuple[np.ndarray, np.ndarray]],
    client_val_data: dict[int, tuple[np.ndarray, np.ndarray]],
    global_val_data: tuple[np.ndarray, np.ndarray],
    num_features: int,
    num_classes: int,
    local_epochs: int = 2,
    seed: int = 13,
    checkpoint_dir: Path | str | None = None,
    tampered_client_ids: set[int] | None = None,
) -> FLSimulationResult:
    """Run an end-to-end federated learning simulation adhering to 12_FEDERATED_LEARNING.md."""
    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tampered_cids = tampered_client_ids or set()

    # 1. Base model initialization (identical for fairness across all strategies)
    init_model = IDS1DCNN(num_features=num_features, num_classes=num_classes)
    init_weights = [val.cpu().detach().numpy() for _, val in init_model.state_dict().items()]
    initial_parameters = ndarrays_to_parameters(init_weights)
    last_evaluated_weights: list[np.ndarray] = list(init_weights)

    # Global evaluation loader
    global_x, global_y = global_val_data
    global_val_loader = create_ids_data_loader(global_x, global_y, batch_size=256, shuffle=False)

    # 2. Evaluation callback after each round
    def evaluate_global_model(
        server_round: int,
        parameters: list[np.ndarray],
        config: dict[str, Any],
    ) -> tuple[float, dict[str, float]] | None:
        nonlocal last_evaluated_weights
        last_evaluated_weights = parameters
        eval_model = IDS1DCNN(num_features=num_features, num_classes=num_classes)
        trainer = IDSTrainer(model=eval_model, device=device)
        eval_model.eval()

        state_dict = dict(
            zip(
                eval_model.state_dict().keys(),
                [torch.from_numpy(p) for p in parameters],
                strict=True,
            )
        )
        eval_model.load_state_dict(state_dict)

        val_loss, val_acc, val_f1 = trainer.evaluate(global_val_loader)
        return float(val_loss), {"val_acc": float(val_acc), "val_macro_f1": float(val_f1)}

    # Config generator per fit round
    def on_fit_config(server_round: int) -> dict[str, Any]:
        return {
            "server_round": server_round,
            "global_model_version": f"v{server_round - 1}" if server_round > 1 else "v0",
            "local_epochs": local_epochs,
        }

    # 3. Instantiate chosen aggregation strategy
    authorized_cids = [f"client_{i}" for i in range(num_clients)]
    verifier = ProvenanceVerifier(authorized_client_ids=authorized_cids)

    if strategy_name.lower() in ("provenance_gated", "provenancegatedfedtrimmedavg"):
        strategy = ProvenanceGatedFedTrimmedAvg(
            verifier=verifier,
            beta=0.20,
            min_accepted_clients=max(2, int(num_clients * 0.4)),
            min_fit_clients=num_clients,
            min_available_clients=num_clients,
            evaluate_fn=evaluate_global_model,
            on_fit_config_fn=on_fit_config,
            initial_parameters=initial_parameters,
        )
    elif strategy_name.lower() in ("fedtrimmedavg", "trimmed_avg"):
        strategy = create_fedtrimmedavg_strategy(
            beta=0.20,
            min_fit_clients=num_clients,
            min_available_clients=num_clients,
            evaluate_fn=evaluate_global_model,
            on_fit_config_fn=on_fit_config,
            initial_parameters=initial_parameters,
        )
    elif strategy_name.lower() in ("multikrum", "krum"):
        strategy = create_multikrum_strategy(
            num_malicious_clients=len(tampered_cids),
            num_clients_to_keep=max(1, num_clients - len(tampered_cids) - 1),
            min_fit_clients=num_clients,
            min_available_clients=num_clients,
            evaluate_fn=evaluate_global_model,
            on_fit_config_fn=on_fit_config,
            initial_parameters=initial_parameters,
        )
    else:
        strategy = create_fedavg_strategy(
            min_fit_clients=num_clients,
            min_available_clients=num_clients,
            evaluate_fn=evaluate_global_model,
            on_fit_config_fn=on_fit_config,
            initial_parameters=initial_parameters,
        )

    # 4. Client factory function for Flower simulation
    def client_fn(cid: str) -> fl.client.Client:
        cid_int = int(cid.replace("client_", ""))
        x_tr, y_tr = client_train_data[cid_int]
        x_va, y_va = client_val_data[cid_int]

        # Check if malicious / tampered
        is_tampered = cid_int in tampered_cids
        if is_tampered:
            # Poison targets or inject extreme values
            y_tr = (y_tr + 1) % num_classes

        train_loader = create_ids_data_loader(x_tr, y_tr, batch_size=256, shuffle=True)
        val_loader = create_ids_data_loader(x_va, y_va, batch_size=256, shuffle=False)

        client_model = IDS1DCNN(num_features=num_features, num_classes=num_classes)
        client = FlowerIDSClient(
            client_id=f"client_{cid_int}",
            model=client_model,
            train_loader=train_loader,
            val_loader=val_loader,
            local_epochs=local_epochs,
            device=device,
        )
        return client.to_client()

    # 5. Launch Flower simulation
    client_resources = {"num_cpus": 1, "num_gpus": 0.1 if torch.cuda.is_available() else 0.0}

    hist = fl.simulation.start_simulation(
        client_fn=client_fn,
        num_clients=num_clients,
        config=fl.server.ServerConfig(num_rounds=num_rounds),
        strategy=strategy,
        client_resources=client_resources,
    )

    # 6. Extract logs and communication accounting
    if hasattr(strategy, "round_audit_logs") and strategy.round_audit_logs:
        round_logs = strategy.round_audit_logs
    else:
        # Construct synthetic round logs for standard baselines
        model_bytes_per_client = len(serialize_ndarrays(init_weights))
        metadata_bytes_per_client = 512
        round_logs = []
        for r in range(1, num_rounds + 1):
            round_logs.append(
                RoundAuditLog(
                    server_round=r,
                    global_model_version=f"v{r - 1}",
                    strategy_name=strategy_name,
                    num_participating=num_clients,
                    num_accepted=num_clients,
                    num_rejected=0,
                    accepted_clients=authorized_cids,
                    model_bytes_sent=model_bytes_per_client * num_clients,
                    update_bytes_received=model_bytes_per_client * num_clients,
                    metadata_bytes_received=metadata_bytes_per_client * num_clients,
                )
            )

    total_model_bytes = sum(log_entry.model_bytes_sent for log_entry in round_logs)
    total_metadata_bytes = sum(log_entry.metadata_bytes_received for log_entry in round_logs)

    # Extract final validation metrics
    final_acc = 0.0
    final_loss = 0.0
    if hist.metrics_centralized and "val_acc" in hist.metrics_centralized:
        final_acc = float(hist.metrics_centralized["val_acc"][-1][1])
    if hist.losses_centralized:
        final_loss = float(hist.losses_centralized[-1][1])

    # Save final model checkpoint if path provided
    checkpoint_path_str = ""
    checkpoint_digest_str = ""
    if checkpoint_dir:
        ckpt_dir = Path(checkpoint_dir)
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        final_ckpt = ckpt_dir / f"{strategy_name}_final_seed{seed}.pt"
        final_model = IDS1DCNN(num_features=num_features, num_classes=num_classes)
        state_dict = dict(
            zip(
                final_model.state_dict().keys(),
                [torch.from_numpy(p) for p in last_evaluated_weights],
                strict=True,
            )
        )
        final_model.load_state_dict(state_dict)
        torch.save(final_model.state_dict(), final_ckpt)
        checkpoint_path_str = str(final_ckpt).replace("\\", "/")
        checkpoint_digest_str = compute_ndarrays_digest(last_evaluated_weights)

    return FLSimulationResult(
        strategy_name=strategy_name,
        dataset_name=dataset_name,
        num_clients=num_clients,
        num_rounds=num_rounds,
        local_epochs=local_epochs,
        seed=seed,
        round_logs=round_logs,
        total_model_bytes=total_model_bytes,
        total_metadata_bytes=total_metadata_bytes,
        final_global_val_accuracy=final_acc,
        final_global_val_loss=final_loss,
        final_checkpoint_path=checkpoint_path_str,
        final_checkpoint_digest=checkpoint_digest_str,
    )
