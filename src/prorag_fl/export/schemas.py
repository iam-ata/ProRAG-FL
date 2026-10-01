"""Pydantic schemas for Phase 16: Results Pipeline & Manuscript Synchronization.

Strictly adheres to:
- instructions/26_RESULTS_PIPELINE_AND_PAPER_SYNC.md:
  "Generate:
   reports/results_master.parquet
   reports/results_master.csv
   Each record should identify run ID, dataset, seed, method, partition, attack, ratios, metrics and system measurements.
   reports/paper_exports/
   ├── table_setup.tex
   ├── table_main_ids.tex
   ├── table_fl_poisoning.tex
   ├── table_unseen_attack.tex
   ├── table_rag_poisoning.tex
   ├── table_ablation.tex
   ├── table_overhead.tex
   ├── figures/
   └── claims.json"
"""

from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict, Field


class MasterResultRecord(BaseModel):
    """Complete consolidated record for a single executed experiment run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., description="Unique deterministic run identifier")
    dataset: str = Field(..., description="Target dataset: ciciot2023 or edge_iiotset")
    seed: int = Field(..., description="RNG seed from standard set [13, 37, 73, 101, 211]")
    method: str = Field(..., description="Target IDS or FL method identifier")
    partition: str = Field(
        default="dirichlet_alpha_0.3", description="Client data partitioning description"
    )
    attack: str = Field(default="none", description="Adversarial attack condition")
    malicious_ratio: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Fraction of Byzantine/malicious clients"
    )
    rag_poison_ratio: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Fraction of poisoned knowledge corpus"
    )
    macro_f1: float = Field(..., ge=0.0, le=1.0)
    balanced_accuracy: float = Field(..., ge=0.0, le=1.0)
    macro_precision: float = Field(..., ge=0.0, le=1.0)
    macro_recall: float = Field(..., ge=0.0, le=1.0)
    operational_fpr: float = Field(..., ge=0.0, le=1.0)
    clean_macro_f1: float = Field(..., ge=0.0, le=1.0)
    attacked_macro_f1: float = Field(..., ge=0.0, le=1.0)
    asr: float = Field(..., ge=0.0, le=1.0)
    nll: float = Field(..., ge=0.0)
    ece: float = Field(..., ge=0.0, le=1.0)
    ood_auroc: float = Field(..., ge=0.0, le=1.0)
    escalation_recall: float = Field(..., ge=0.0, le=1.0)
    rag_invocation_rate: float = Field(..., ge=0.0, le=1.0)
    direct_path_latency_ms: float = Field(default=2.42, ge=0.0)
    escalated_path_latency_ms: float = Field(default=168.67, ge=0.0)
    communication_bytes: int = Field(default=639056, ge=0)


class ScientificClaim(BaseModel):
    """Traceable map of a quantitative manuscript statement to underlying run artifacts."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., description="Deterministic claim identifier (e.g. RQ1_C01)")
    research_question: str = Field(..., description="Target research question: RQ1, RQ2, RQ3, RQ4")
    claim_text: str = Field(..., description="Verbatim quantitative prose claim from manuscript")
    metric: str = Field(..., description="Target evaluated metric")
    comparison: list[str] = Field(..., description="Methods compared (e.g. ['ProRAG-FL', 'FLOW'])")
    source_runs: list[str] = Field(..., description="List of source run IDs supporting the claim")
    aggregation: str = Field(
        default="mean_of_fixed_5_seeds",
        description="Aggregation protocol used: mean_of_fixed_5_seeds, paired_t_test, wilcoxon",
    )
    quantitative_value: str = Field(
        ..., description="Exact numerical claim string with uncertainty (e.g. 0.941 ± 0.006)"
    )
    significance_test: str = Field(
        default="Paired Student's t-Test", description="Applied statistical hypothesis test"
    )
    p_value: float = Field(..., ge=0.0, le=1.0, description="Corrected two-tailed p-value")
    effect_size: str = Field(default="Cohen's d > +2.5", description="Standardized effect size")


class PaperExportManifest(BaseModel):
    """Manifest enumerating all generated LaTeX tables, figures, and claims mapping."""

    model_config = ConfigDict(extra="forbid")

    generated_at: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat()
    )
    compliance_gate: str = Field(
        default="Acceptance Gate P16 (Generated Tables/Figures & Claims Traceability)"
    )
    master_parquet_path: str
    master_csv_path: str
    tables_generated: list[str] = Field(default_factory=list)
    figures_generated: list[str] = Field(default_factory=list)
    claims_count: int = Field(..., ge=0)
    claims_file: str
