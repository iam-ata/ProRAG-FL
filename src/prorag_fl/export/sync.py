"""Manuscript synchronization orchestrator for Phase 16.

Safely synchronizes generated LaTeX tables and figures from reports/paper_exports/
to ../Manuscript/tables/ and ../Manuscript/figures/ under strict boundary guardrails.

Strictly adheres to:
- instructions/26_RESULTS_PIPELINE_AND_PAPER_SYNC.md:
  "Manuscript boundary: Manuscript is ../Manuscript/. Generate artifacts under Code first.
   Only an explicit synchronization command, after researcher approval, copies tables/figures
   to the manuscript. Do not auto-rewrite scientific narrative without review."
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ManuscriptSynchronizer:
    """Manages explicit synchronization of generated paper artifacts to ../Manuscript/."""

    def __init__(
        self,
        exports_dir: str | Path = "reports/paper_exports",
        manuscript_dir: str | Path = "../Manuscript",
    ) -> None:
        self.exports_dir = Path(exports_dir)
        self.manuscript_dir = Path(manuscript_dir)

    def validate_exports(self) -> list[Path]:
        """Check that required paper export files are built and present."""
        if not self.exports_dir.is_dir():
            raise FileNotFoundError(
                f"Exports directory {self.exports_dir} does not exist. Run 'prorag export build-all' first."
            )

        expected_tables = [
            "table_setup.tex",
            "table_main_ids.tex",
            "table_fl_poisoning.tex",
            "table_unseen_attack.tex",
            "table_rag_poisoning.tex",
            "table_ablation.tex",
            "table_overhead.tex",
        ]

        missing: list[str] = []
        found: list[Path] = []
        for tbl in expected_tables:
            p = self.exports_dir / tbl
            if p.is_file():
                found.append(p)
            else:
                missing.append(tbl)

        if missing:
            raise FileNotFoundError(
                f"Missing expected LaTeX tables in {self.exports_dir}: {missing}. Run 'prorag export build-all' first."
            )

        figures_dir = self.exports_dir / "figures"
        if not figures_dir.is_dir():
            raise FileNotFoundError(f"Missing figures directory in {self.exports_dir}.")

        found.extend(list(figures_dir.glob("*.pdf")))
        found.extend(list(figures_dir.glob("*.png")))
        return found

    def sync(self, dry_run: bool = True) -> dict[str, Any]:
        """Synchronize validated paper artifacts to manuscript directory under strict boundary controls."""
        artifacts = self.validate_exports()

        target_tables = self.manuscript_dir / "tables"
        target_figures = self.manuscript_dir / "figures"

        actions: list[dict[str, str]] = []

        for src in artifacts:
            if src.suffix == ".tex":
                dst = target_tables / src.name
            else:
                dst = target_figures / src.name

            actions.append(
                {
                    "source": src.as_posix(),
                    "destination": dst.as_posix(),
                    "file_type": "table" if src.suffix == ".tex" else "figure",
                }
            )

        if not dry_run:
            target_tables.mkdir(parents=True, exist_ok=True)
            target_figures.mkdir(parents=True, exist_ok=True)

            for act in actions:
                shutil.copy2(act["source"], act["destination"])
                logger.info("Copied %s -> %s", act["source"], act["destination"])

        return {
            "dry_run": dry_run,
            "manuscript_dir": self.manuscript_dir.as_posix(),
            "synced_count": len(actions),
            "actions": actions,
        }
