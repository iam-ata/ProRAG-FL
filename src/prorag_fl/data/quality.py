"""Data quality report generator for ProRAG-FL datasets."""

from __future__ import annotations

import datetime
from pathlib import Path

from prorag_fl.schemas.dataset import ColumnAudit, FeatureSchema, SplitManifest


def generate_data_quality_report(
    dataset_name: str,
    feature_schema: FeatureSchema,
    column_audits: dict[str, ColumnAudit],
    split_manifest: SplitManifest,
    output_path: Path | str,
    extra_notes: str | None = None,
) -> Path:
    """Generate Markdown data quality and leakage audit report conforming to 08_DATASETS_AND_PREPROCESSING.md."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        f"# Data Quality & Leakage Audit Report: {dataset_name.upper()}",
        "",
        f"- **Generated At:** {datetime.datetime.now(datetime.UTC).isoformat()} UTC",
        f"- **Dataset:** `{dataset_name}`",
        f"- **Split Seed:** `{split_manifest.split_seed}`",
        f"- **Split Hash:** `{split_manifest.split_hash}`",
        f"- **Held-Out Attack Family:** `{split_manifest.held_out_family or 'None'}`",
        "",
        "## 1. Split Distribution & Firewall Audit",
        "",
        "| Partition | Sample Count | Percentage | Class Breakdown (Top Families) |",
        "|---|---|---|---|",
        f"| **Train** | {split_manifest.train_count:,} | {split_manifest.train_count / split_manifest.total_count * 100:.1f}% | {format_class_counts(split_manifest.train_class_counts)} |",
        f"| **Validation** | {split_manifest.val_count:,} | {split_manifest.val_count / split_manifest.total_count * 100:.1f}% | {format_class_counts(split_manifest.val_class_counts)} |",
        f"| **Test** | {split_manifest.test_count:,} | {split_manifest.test_count / split_manifest.total_count * 100:.1f}% | {format_class_counts(split_manifest.test_class_counts)} |",
        f"| **Total** | {split_manifest.total_count:,} | 100.0% | |",
        "",
    ]

    # Held-out verification section
    if split_manifest.held_out_family:
        held = split_manifest.held_out_family
        train_held = split_manifest.train_class_counts.get(held, 0)
        val_held = split_manifest.val_class_counts.get(held, 0)
        test_held = split_manifest.test_class_counts.get(held, 0)

        lines.extend(
            [
                "### Held-Out Attack Family Verification",
                "",
                f"- **Target Held-Out Family:** `{held}`",
                f"- **Count in Train:** `{train_held}` (Required: 0) -> **{'PASS' if train_held == 0 else 'FAIL - LEAKAGE!'}**",
                f"- **Count in Validation:** `{val_held}` (Required: 0) -> **{'PASS' if val_held == 0 else 'FAIL - LEAKAGE!'}**",
                f"- **Count in Test:** `{test_held}` (Required: > 0 for unseen-to-model test) -> **{'PASS' if test_held > 0 else 'WARNING: 0 in test'}**",
                "",
            ]
        )

    lines.extend(
        [
            "## 2. Feature Schema & Column Audit",
            "",
            f"- **Active Model Features:** `{len(feature_schema.final_feature_order)}` ({len(feature_schema.numeric_features)} numeric, {len(feature_schema.categorical_features)} categorical)",
            f"- **Excluded / Dropped Columns:** `{len(feature_schema.dropped_columns)}`",
            "",
            "### Dropped & Leakage Columns",
            "",
            "| Column Name | Rationale |",
            "|---|---|",
        ]
    )

    for col, reason in sorted(feature_schema.dropped_columns.items()):
        lines.append(f"| `{col}` | {reason} |")

    lines.extend(
        [
            "",
            "### Audited Active Columns",
            "",
            "| Column | Type | Missing Values | Infinite Values | Unique Count |",
            "|---|---|---|---|---|",
        ]
    )

    for col in feature_schema.final_feature_order:
        audit = column_audits.get(col)
        if audit:
            lines.append(
                f"| `{col}` | `{audit.dtype}` | {audit.num_missing} | {audit.num_infinite} | {audit.num_unique} |"
            )

    if extra_notes:
        lines.extend(["", "## 3. Notes & Observations", "", extra_notes])

    content = "\n".join(lines) + "\n"
    path.write_text(content, encoding="utf-8")
    return path


def format_class_counts(counts: dict[str, int], top_n: int = 4) -> str:
    """Format dictionary of class counts into a concise summary string."""
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    summary = [f"{k}: {v:,}" for k, v in sorted_items[:top_n]]
    if len(sorted_items) > top_n:
        summary.append(f"... (+{len(sorted_items) - top_n} more)")
    return ", ".join(summary)
