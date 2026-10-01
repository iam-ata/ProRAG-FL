"""Federated aggregation strategies for ProRAG-FL: FedAvg, MultiKrum, FedTrimmedAvg, and ProvenanceGatedFedTrimmedAvg."""

from __future__ import annotations

import time
from collections.abc import Callable

from flwr.common import (
    FitRes,
    Parameters,
    Scalar,
    parameters_to_ndarrays,
)
from flwr.server.client_proxy import ClientProxy
from flwr.server.strategy import FedAvg, FedTrimmedAvg, Krum

from prorag_fl.federated.provenance_envelope import (
    ProvenanceVerifier,
    compute_ndarrays_digest,
    serialize_ndarrays,
)
from prorag_fl.schemas.federated import ModelProvenanceEnvelope, RoundAuditLog


def create_fedavg_strategy(
    fraction_fit: float = 1.0,
    min_fit_clients: int = 2,
    min_available_clients: int = 2,
    evaluate_fn: Callable | None = None,
    on_fit_config_fn: Callable | None = None,
    initial_parameters: Parameters | None = None,
) -> FedAvg:
    """Create standard FedAvg baseline strategy."""
    return FedAvg(
        fraction_fit=fraction_fit,
        min_fit_clients=min_fit_clients,
        min_available_clients=min_available_clients,
        evaluate_fn=evaluate_fn,
        on_fit_config_fn=on_fit_config_fn,
        initial_parameters=initial_parameters,
    )


def create_multikrum_strategy(
    num_malicious_clients: int = 1,
    num_clients_to_keep: int = 2,
    fraction_fit: float = 1.0,
    min_fit_clients: int = 3,
    min_available_clients: int = 3,
    evaluate_fn: Callable | None = None,
    on_fit_config_fn: Callable | None = None,
    initial_parameters: Parameters | None = None,
) -> Krum:
    """Create MultiKrum baseline strategy selecting and averaging top-m updates."""
    return Krum(
        num_malicious_clients=num_malicious_clients,
        num_clients_to_keep=num_clients_to_keep,
        fraction_fit=fraction_fit,
        min_fit_clients=min_fit_clients,
        min_available_clients=min_available_clients,
        evaluate_fn=evaluate_fn,
        on_fit_config_fn=on_fit_config_fn,
        initial_parameters=initial_parameters,
    )


def create_fedtrimmedavg_strategy(
    beta: float = 0.20,
    fraction_fit: float = 1.0,
    min_fit_clients: int = 2,
    min_available_clients: int = 2,
    evaluate_fn: Callable | None = None,
    on_fit_config_fn: Callable | None = None,
    initial_parameters: Parameters | None = None,
) -> FedTrimmedAvg:
    """Create canonical coordinate-wise FedTrimmedAvg strategy with locked beta=0.20."""
    return FedTrimmedAvg(
        beta=beta,
        fraction_fit=fraction_fit,
        min_fit_clients=min_fit_clients,
        min_available_clients=min_available_clients,
        evaluate_fn=evaluate_fn,
        on_fit_config_fn=on_fit_config_fn,
        initial_parameters=initial_parameters,
    )


class ProvenanceGatedFedTrimmedAvg(FedTrimmedAvg):
    """Locked proposed update rule conforming to 02_LOCKED_PROPOSED_METHOD.md and 12_FEDERATED_LEARNING.md:

        theta_(t+1) = FedTrimmedAvg({Delta theta_i^t | V_i^M = 1}, beta=0.20)

    Steps:
        1. Verify each candidate's identity, signature, round, model version, update digest, and nonce.
        2. Log accept/reject and rejection reason.
        3. Pass only accepted updates (V_i^M = 1) to FedTrimmedAvg with beta=0.20.
        4. If insufficient eligible updates remain (< min_accepted_clients), NEVER fall back to FedAvg;
           emit INSUFFICIENT_ELIGIBLE_CLIENTS.
    """

    def __init__(
        self,
        verifier: ProvenanceVerifier,
        beta: float = 0.20,
        min_accepted_clients: int = 2,
        fraction_fit: float = 1.0,
        min_fit_clients: int = 2,
        min_available_clients: int = 2,
        evaluate_fn: Callable | None = None,
        on_fit_config_fn: Callable | None = None,
        initial_parameters: Parameters | None = None,
    ) -> None:
        super().__init__(
            beta=beta,
            fraction_fit=fraction_fit,
            min_fit_clients=min_fit_clients,
            min_available_clients=min_available_clients,
            evaluate_fn=evaluate_fn,
            on_fit_config_fn=on_fit_config_fn,
            initial_parameters=initial_parameters,
        )
        self.verifier = verifier
        self.min_accepted_clients = min_accepted_clients
        self.round_audit_logs: list[RoundAuditLog] = []

    def aggregate_fit(
        self,
        server_round: int,
        results: list[tuple[ClientProxy, FitRes]],
        failures: list[tuple[ClientProxy, FitRes] | BaseException],
    ) -> tuple[Parameters | None, dict[str, Scalar]]:
        """Aggregate candidate updates filtered by hard cryptographic provenance validation."""
        start_time = time.perf_counter()

        if not results:
            return None, {}

        accepted_results: list[tuple[ClientProxy, FitRes]] = []
        accepted_client_ids: list[str] = []
        rejections: dict[str, str] = {}
        local_metrics: dict[str, dict[str, float]] = {}

        total_update_bytes = 0
        total_metadata_bytes = 0

        # Extract current expected global model version from config or convention
        expected_version = f"v{server_round - 1}" if server_round > 1 else "v0"

        # Step 1: Evaluate candidate provenance envelopes
        for client_proxy, fit_res in results:
            metrics = fit_res.metrics
            client_id = str(metrics.get("client_id", client_proxy.cid))

            update_bytes = int(metrics.get("update_bytes", 0))
            metadata_bytes = int(metrics.get("metadata_bytes", 0))
            total_update_bytes += update_bytes
            total_metadata_bytes += metadata_bytes

            local_metrics[client_id] = {
                "train_loss": float(metrics.get("train_loss", 0.0)),
                "train_acc": float(metrics.get("train_acc", 0.0)),
            }

            envelope_json = metrics.get("provenance_envelope_json")
            if not envelope_json:
                rejections[client_id] = "missing_provenance_envelope"
                continue

            try:
                envelope = ModelProvenanceEnvelope.model_validate_json(str(envelope_json))
            except Exception as e:
                rejections[client_id] = f"malformed_envelope:{e}"
                continue

            # Check update ndarrays digest
            ndarrays = parameters_to_ndarrays(fit_res.parameters)
            is_valid, reason = self.verifier.verify(
                envelope=envelope,
                expected_round=server_round,
                expected_model_version=expected_version,
                update_ndarrays=ndarrays,
            )

            if is_valid:
                accepted_results.append((client_proxy, fit_res))
                accepted_client_ids.append(client_id)
            else:
                rejections[client_id] = reason

        # Step 2: Enforcement check
        insufficient_clients = len(accepted_results) < self.min_accepted_clients
        checkpoint_digest = ""

        if insufficient_clients:
            # Strictly DO NOT fall back to FedAvg
            aggregated_params = None
            aggregation_metrics: dict[str, Scalar] = {
                "status": "INSUFFICIENT_ELIGIBLE_CLIENTS",
                "num_accepted": len(accepted_results),
                "num_rejected": len(rejections),
            }
        else:
            # Step 3: Pass exclusively accepted candidates to FedTrimmedAvg
            aggregated_params, aggregation_metrics = super().aggregate_fit(
                server_round=server_round,
                results=accepted_results,
                failures=failures,
            )
            if aggregated_params is not None:
                agg_ndarrays = parameters_to_ndarrays(aggregated_params)
                checkpoint_digest = compute_ndarrays_digest(agg_ndarrays)

        elapsed_time = time.perf_counter() - start_time

        # Model bytes sent downstream to participating clients
        model_bytes_sent = len(
            serialize_ndarrays(parameters_to_ndarrays(results[0][1].parameters))
        ) * len(results)

        # Step 4: Record per-round audit log
        audit_log = RoundAuditLog(
            server_round=server_round,
            global_model_version=expected_version,
            strategy_name="ProvenanceGatedFedTrimmedAvg",
            num_participating=len(results),
            num_accepted=len(accepted_results),
            num_rejected=len(rejections),
            accepted_clients=accepted_client_ids,
            rejections=rejections,
            local_metrics=local_metrics,
            aggregation_time_seconds=float(elapsed_time),
            model_bytes_sent=model_bytes_sent,
            update_bytes_received=total_update_bytes,
            metadata_bytes_received=total_metadata_bytes,
            checkpoint_hash=checkpoint_digest,
            insufficient_clients=insufficient_clients,
        )
        self.round_audit_logs.append(audit_log)

        aggregation_metrics["num_accepted"] = len(accepted_results)
        aggregation_metrics["num_rejected"] = len(rejections)
        aggregation_metrics["checkpoint_digest"] = checkpoint_digest

        return aggregated_params, aggregation_metrics
