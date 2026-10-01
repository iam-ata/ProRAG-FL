"""Hyperledger Fabric Gateway REST/gRPC client for model update provenance."""

from __future__ import annotations

import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from prorag_fl.blockchain.backend import ProvenanceBackend
from prorag_fl.schemas.blockchain import (
    ClientIdentityRecord,
    LedgerStats,
    ModelUpdateRecord,
    ProvenanceTransactionReceipt,
)

logger = logging.getLogger(__name__)


class FabricGatewayClient(ProvenanceBackend):
    """Client for external Hyperledger Fabric network via typed REST/gRPC gateway service."""

    def __init__(
        self,
        gateway_endpoint: str = "http://127.0.0.1:7050",
        channel_name: str = "prorag-channel",
        chaincode_name: str = "model-registry",
        timeout_seconds: float = 10.0,
    ) -> None:
        self.gateway_endpoint = gateway_endpoint.rstrip("/")
        self.channel_name = channel_name
        self.chaincode_name = chaincode_name
        self.timeout_seconds = timeout_seconds

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Send HTTP POST request to Fabric Gateway service."""
        import json

        url = f"{self.gateway_endpoint}/{path.lstrip('/')}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                res_body = resp.read().decode("utf-8")
                return json.loads(res_body)
        except urllib.error.URLError as e:
            logger.warning(
                "Fabric Gateway connection failed at %s: %s",
                url,
                e,
            )
            raise ConnectionError(f"Hyperledger Fabric Gateway unreachable at {url}: {e}") from e

    def _get(self, path: str) -> dict[str, Any]:
        """Send HTTP GET request to Fabric Gateway service."""
        import json

        url = f"{self.gateway_endpoint}/{path.lstrip('/')}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                res_body = resp.read().decode("utf-8")
                return json.loads(res_body)
        except urllib.error.URLError as e:
            logger.warning(
                "Fabric Gateway connection failed at %s: %s",
                url,
                e,
            )
            raise ConnectionError(f"Hyperledger Fabric Gateway unreachable at {url}: {e}") from e

    def register_client(
        self,
        client_id: str,
        msp_id: str = "Org1MSP",
        is_authorized: bool = True,
    ) -> ClientIdentityRecord:
        """Register client identity on Fabric ledger via gateway."""
        payload = {
            "channel": self.channel_name,
            "chaincode": self.chaincode_name,
            "fcn": "RegisterClient",
            "args": [client_id, msp_id, str(is_authorized).lower()],
        }
        resp = self._post("api/v1/invoke", payload)
        return ClientIdentityRecord.model_validate(resp.get("data", {}))

    def revoke_client(
        self,
        client_id: str,
        reason: str = "revoked_by_admin",
    ) -> ClientIdentityRecord:
        """Revoke client identity on Fabric ledger via gateway."""
        payload = {
            "channel": self.channel_name,
            "chaincode": self.chaincode_name,
            "fcn": "RevokeClient",
            "args": [client_id, reason],
        }
        resp = self._post("api/v1/invoke", payload)
        return ClientIdentityRecord.model_validate(resp.get("data", {}))

    def verify_update(
        self,
        client_id: str,
        server_round: int,
        global_model_version: str,
        update_sha256: str,
        nonce: str,
        expected_round: int | None = None,
    ) -> tuple[bool, str]:
        """Query verification logic on Fabric chaincode."""
        args = [client_id, str(server_round), global_model_version, update_sha256, nonce]
        if expected_round is not None:
            args.append(str(expected_round))
        payload = {
            "channel": self.channel_name,
            "chaincode": self.chaincode_name,
            "fcn": "VerifyUpdate",
            "args": args,
        }
        try:
            resp = self._post("api/v1/query", payload)
            data = resp.get("data", {})
            return bool(data.get("is_valid", False)), str(data.get("reason", "unknown"))
        except ConnectionError as e:
            return False, f"fabric_gateway_unreachable:{e}"

    def submit_update(
        self,
        record: ModelUpdateRecord,
    ) -> ProvenanceTransactionReceipt:
        """Invoke SubmitUpdate on Fabric chaincode."""
        payload = {
            "channel": self.channel_name,
            "chaincode": self.chaincode_name,
            "fcn": "SubmitUpdate",
            "args": [record.model_dump_json()],
        }
        resp = self._post("api/v1/invoke", payload)
        return ProvenanceTransactionReceipt.model_validate(resp.get("receipt", {}))

    def query_update(self, update_id: str) -> ModelUpdateRecord | None:
        """Query model update record by update ID."""
        payload = {
            "channel": self.channel_name,
            "chaincode": self.chaincode_name,
            "fcn": "QueryUpdate",
            "args": [update_id],
        }
        try:
            resp = self._post("api/v1/query", payload)
            data = resp.get("data")
            if not data:
                return None
            return ModelUpdateRecord.model_validate(data)
        except Exception:
            return None

    def query_updates_by_round(self, server_round: int) -> list[ModelUpdateRecord]:
        """Query all model updates for a round."""
        payload = {
            "channel": self.channel_name,
            "chaincode": self.chaincode_name,
            "fcn": "QueryUpdatesByRound",
            "args": [str(server_round)],
        }
        try:
            resp = self._post("api/v1/query", payload)
            items = resp.get("data", [])
            return [ModelUpdateRecord.model_validate(item) for item in items]
        except Exception:
            return []

    def get_ledger_stats(self) -> LedgerStats:
        """Query performance metrics from Fabric gateway."""
        try:
            resp = self._get("api/v1/stats")
            return LedgerStats.model_validate(resp)
        except Exception:
            return LedgerStats()

    def reset(self) -> None:
        """Reset chaincode state if supported by dev gateway."""
        try:
            self._post(
                "api/v1/invoke",
                {
                    "channel": self.channel_name,
                    "chaincode": self.chaincode_name,
                    "fcn": "ResetState",
                    "args": [],
                },
            )
        except Exception:
            pass
