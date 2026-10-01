"""Unit tests for Phase 16: Results Pipeline & Manuscript Synchronization.

Verifies:
- Master dataset compilation (results_master.parquet and results_master.csv).
- Seven publication LaTeX tables syntax and completeness.
- Vector and bitmap figure generation (PDF and PNG).
- Scientific claims traceability mapping (claims.json).
- Manuscript boundary safety invariant and dry-run synchronization.

Strictly adheres to:
- instructions/26_RESULTS_PIPELINE_AND_PAPER_SYNC.md
- instructions/36_PHASE_ACCEPTANCE_GATES.md (Gate P16)
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from prorag_fl.export.builder import PaperArtifactsBuilder
from prorag_fl.export.sync import ManuscriptSynchronizer


def test_build_all_paper_artifacts(tmp_path: Path) -> None:
    """Verify end-to-end building of master datasets, LaTeX tables, figures, and claims mapping."""
    reports_dir = tmp_path / "reports"
    exports_dir = reports_dir / "paper_exports"
    runs_dir = tmp_path / "runs"

    builder = PaperArtifactsBuilder(
        reports_dir=reports_dir,
        exports_dir=exports_dir,
        runs_dir=runs_dir,
    )
    manifest = builder.build_all()

    # 1. Master Datasets
    p_path = Path(manifest.master_parquet_path)
    c_path = Path(manifest.master_csv_path)
    assert p_path.is_file()
    assert c_path.is_file()

    df_p = pd.read_parquet(p_path)
    df_c = pd.read_csv(c_path)
    assert len(df_p) == len(df_c)
    assert len(df_p) > 0
    assert "run_id" in df_p.columns
    assert "dataset" in df_p.columns
    assert "seed" in df_p.columns
    assert "macro_f1" in df_p.columns
    assert "operational_fpr" in df_p.columns
    assert "attacked_macro_f1" in df_p.columns

    # 2. LaTeX Tables
    expected_tables = [
        "table_setup.tex",
        "table_main_ids.tex",
        "table_fl_poisoning.tex",
        "table_unseen_attack.tex",
        "table_rag_poisoning.tex",
        "table_ablation.tex",
        "table_overhead.tex",
    ]
    assert len(manifest.tables_generated) == 7
    for tbl_name in expected_tables:
        tbl_path = exports_dir / tbl_name
        assert tbl_path.is_file()
        content = tbl_path.read_text(encoding="utf-8")
        assert r"\begin{table" in content
        assert r"\begin{tabular}" in content
        assert r"\toprule" in content
        assert r"\bottomrule" in content
        assert r"\end{tabular}" in content
        assert r"\end{table" in content

    # 3. Figures (PDF and PNG)
    expected_fig_stems = [
        "fig_latency_vs_rir",
        "fig_ablation_ladder",
        "fig_byzantine_resilience",
        "fig_roc_ood",
        "fig_baseline_macro_f1",
        "fig_baseline_pareto",
    ]
    assert len(manifest.figures_generated) >= 12
    for stem in expected_fig_stems:
        pdf_f = exports_dir / "figures" / f"{stem}.pdf"
        png_f = exports_dir / "figures" / f"{stem}.png"
        assert pdf_f.is_file() and pdf_f.stat().st_size > 0
        assert png_f.is_file() and png_f.stat().st_size > 0
    assert (exports_dir / "figures" / "prorag_architecture_clean.png").is_file()

    # 4. Claims Traceability
    claims_file = Path(manifest.claims_file)
    assert claims_file.is_file()
    with open(claims_file, encoding="utf-8") as f:
        claims = json.load(f)
    assert len(claims) >= 5
    for c in claims:
        assert "claim_id" in c
        assert "research_question" in c
        assert "claim_text" in c
        assert "metric" in c
        assert "source_runs" in c
        assert len(c["source_runs"]) > 0
        assert "p_value" in c
        assert c["p_value"] <= 0.05


def test_manuscript_synchronizer_safety(tmp_path: Path) -> None:
    """Verify dry-run safety and safe explicit copy boundary controls."""
    reports_dir = tmp_path / "reports"
    exports_dir = reports_dir / "paper_exports"
    manuscript_dir = tmp_path / "Manuscript"

    builder = PaperArtifactsBuilder(
        reports_dir=reports_dir,
        exports_dir=exports_dir,
        runs_dir=tmp_path / "runs",
    )
    builder.build_all()

    sync = ManuscriptSynchronizer(exports_dir=exports_dir, manuscript_dir=manuscript_dir)

    # A. Dry-run mode: should NOT create files in manuscript_dir
    res_dry = sync.sync(dry_run=True)
    assert res_dry["dry_run"] is True
    assert res_dry["synced_count"] > 0
    assert not (manuscript_dir / "tables").exists()
    assert not (manuscript_dir / "figures").exists()

    # B. Live execution mode: should copy tables and figures to designated subdirectories
    res_live = sync.sync(dry_run=False)
    assert res_live["dry_run"] is False
    assert (manuscript_dir / "tables" / "table_main_ids.tex").is_file()
    assert (manuscript_dir / "figures" / "fig_latency_vs_rir.pdf").is_file()
    assert (manuscript_dir / "figures" / "fig_latency_vs_rir.png").is_file()
