"""CICIoT2023 dataset adapter with schema validation, leakage audit, and label canonicalization."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from prorag_fl.data.adapter import DatasetAdapter
from prorag_fl.schemas.dataset import ColumnAudit, FeatureSchema, LabelClassInfo, LabelMapping

# Authoritative CICIoT2023 family taxonomy
CICIOT2023_FAMILY_MAP: dict[str, str] = {
    # Benign
    "benigntraffic": "Benign",
    "benign": "Benign",
    # Mirai (Held-out Unseen-to-Model Family)
    "mirai-greeth_flood": "Mirai",
    "mirai-udpplain": "Mirai",
    "mirai-greip_flood": "Mirai",
    "mirai": "Mirai",
    # DDoS
    "ddos-icmp_flood": "DDoS",
    "ddos-udp_flood": "DDoS",
    "ddos-tcp_flood": "DDoS",
    "ddos-pshack_flood": "DDoS",
    "ddos-synonymousip_flood": "DDoS",
    "ddos-rstfinflood": "DDoS",
    "ddos-http_flood": "DDoS",
    "ddos-udp_fragmentation": "DDoS",
    "ddos-icmp_fragmentation": "DDoS",
    "ddos-ack_fragmentation": "DDoS",
    "ddos-slowloris": "DDoS",
    "ddos": "DDoS",
    # DoS
    "dos-udp_flood": "DoS",
    "dos-tcp_flood": "DoS",
    "dos-syn_flood": "DoS",
    "dos-http_flood": "DoS",
    "dos": "DoS",
    # Recon
    "recon-hostdiscovery": "Recon",
    "recon-osscan": "Recon",
    "recon-portscan": "Recon",
    "recon-pingsweep": "Recon",
    "recon": "Recon",
    # Web attacks
    "vulnerabilityscan": "Web",
    "sqlinjection": "Web",
    "commandinjection": "Web",
    "backdoor_malware": "Web",
    "browserhijacking": "Web",
    "xss": "Web",
    "uploading_attack": "Web",
    "web": "Web",
    # Spoofing
    "dns_spoofing": "Spoofing",
    "mitm-arpspoofing": "Spoofing",
    "spoofing": "Spoofing",
    # Brute Force
    "dictionarybruteforce": "BruteForce",
    "bruteforce": "BruteForce",
}

# Standard ordered families for integer multiclass target IDs
ORDERED_FAMILIES: list[str] = [
    "Benign",
    "DDoS",
    "DoS",
    "Recon",
    "Web",
    "Spoofing",
    "BruteForce",
    "Mirai",  # Held-out family at index 7
]

# Patterns for columns that trivially leak attack identity or represent non-generalizable metadata
LEAKAGE_COLUMN_PATTERNS = [
    r"^id$",
    r"^flow_id$",
    r"^timestamp$",
    r"^time$",
    r".*date.*",
    r"^src_ip$",
    r"^dst_ip$",
    r"^source_ip$",
    r"^destination_ip$",
    r"^src_port$",
    r"^dst_port$",
    r"^source_port$",
    r"^destination_port$",
    r"^scenario.*",
    r"^capture.*",
    r"^filename$",
    r"^unnamed.*",
]


class CICIoT2023Adapter(DatasetAdapter):
    """Adapter for the CICIoT2023 benchmark dataset."""

    def __init__(self) -> None:
        super().__init__(dataset_name="ciciot2023")

    def find_target_column(self, columns: list[str]) -> str:
        """Locate target label column dynamically."""
        for c in columns:
            if c.lower() in ("label", "attack_type", "attack"):
                return c
        raise ValueError(f"Could not find target label column among: {columns}")

    def audit_schema_and_leakage(
        self, df: pd.DataFrame
    ) -> tuple[FeatureSchema, dict[str, ColumnAudit]]:
        """Audit dataset schema and identify leakage/constant/identifier columns to exclude."""
        target_col = self.find_target_column(list(df.columns))
        label_metadata_cols = {
            "label",
            "canonical_label",
            "family",
            "target_id",
            "is_attack",
            "attack_type",
            "attack",
        }

        column_audits: dict[str, ColumnAudit] = {}
        dropped_cols: dict[str, str] = {}
        numeric_cols: list[str] = []
        categorical_cols: list[str] = []
        identifier_cols: list[str] = []
        timestamp_cols: list[str] = []

        for col in df.columns:
            if col == target_col or col.lower() in label_metadata_cols:
                dropped_cols[col] = "Target / label metadata (firewalled to evaluation only)"
                continue

            col_lower = col.strip().lower()
            series = df[col]
            n_null = int(series.isna().sum())
            n_unique = int(series.nunique(dropna=False))
            is_constant = n_unique <= 1
            is_all_null = n_null == len(df)

            # Check infinite for numeric types
            n_inf = 0
            if pd.api.types.is_numeric_dtype(series):
                n_inf = int(np.isinf(pd.to_numeric(series, errors="coerce")).sum())

            audit = ColumnAudit(
                dtype=str(series.dtype),
                num_missing=n_null,
                num_infinite=n_inf,
                num_unique=n_unique,
                is_constant=is_constant,
                is_all_null=is_all_null,
            )
            column_audits[col] = audit

            # Check if matches leakage patterns
            is_leakage = any(re.match(pat, col_lower) for pat in LEAKAGE_COLUMN_PATTERNS)

            if is_all_null:
                dropped_cols[col] = "All null values"
            elif is_constant:
                dropped_cols[col] = "Zero variance (constant feature)"
            elif is_leakage:
                dropped_cols[col] = "Direct leakage / non-generalizable identifier or timestamp"
                if "time" in col_lower or "date" in col_lower:
                    timestamp_cols.append(col)
                else:
                    identifier_cols.append(col)
            elif pd.api.types.is_numeric_dtype(series):
                numeric_cols.append(col)
            else:
                categorical_cols.append(col)

        final_order = sorted(numeric_cols + categorical_cols)

        schema = FeatureSchema(
            dataset_name=self.dataset_name,
            numeric_features=numeric_cols,
            categorical_features=categorical_cols,
            target_column=target_col,
            identifier_columns=identifier_cols,
            timestamp_columns=timestamp_cols,
            dropped_columns=dropped_cols,
            final_feature_order=final_order,
        )

        return schema, column_audits

    def canonicalize_labels(self, df: pd.DataFrame) -> tuple[pd.DataFrame, LabelMapping]:
        """Map raw labels into canonical classes, attack families, and target IDs."""
        target_col = self.find_target_column(list(df.columns))
        df_out = df.copy()

        raw_labels = df_out[target_col].astype(str).tolist()
        canonical_classes: list[str] = []
        families: list[str] = []
        target_ids: list[int] = []
        binary_targets: list[int] = []

        family_to_id = {fam: idx for idx, fam in enumerate(ORDERED_FAMILIES)}
        id_to_family = dict(enumerate(ORDERED_FAMILIES))

        raw_to_canonical: dict[str, str] = {}
        class_details: dict[str, LabelClassInfo] = {}

        for raw in raw_labels:
            raw_clean = raw.strip()
            lookup_key = raw_clean.lower()
            family = CICIOT2023_FAMILY_MAP.get(lookup_key, "UnknownAttack")

            canonical = raw_clean
            raw_to_canonical[raw_clean] = canonical

            fam_id = family_to_id.get(family, len(ORDERED_FAMILIES) - 1)
            is_attack = family != "Benign"

            canonical_classes.append(canonical)
            families.append(family)
            target_ids.append(fam_id)
            binary_targets.append(1 if is_attack else 0)

            if family not in class_details:
                class_details[family] = LabelClassInfo(
                    class_id=fam_id,
                    canonical_name=family,
                    family=family,
                    is_attack=is_attack,
                    is_held_out=(family == "Mirai"),
                )

        df_out["canonical_label"] = canonical_classes
        df_out["family"] = families
        df_out["target_id"] = target_ids
        df_out["is_attack"] = binary_targets

        mapping = LabelMapping(
            dataset_name=self.dataset_name,
            raw_to_canonical=raw_to_canonical,
            canonical_to_id=family_to_id,
            id_to_canonical=id_to_family,
            family_mapping=CICIOT2023_FAMILY_MAP,
            class_details=class_details,
            num_classes=len(ORDERED_FAMILIES),
        )

        return df_out, mapping
