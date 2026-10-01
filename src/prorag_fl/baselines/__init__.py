"""Baselines module for ProRAG-FL comparative benchmarking.

Provides implementations and adapters for B0 through B11 adhering to
instructions/20_BASELINES_MASTER.md, 21_BASELINE_IMPLEMENTATION_DETAILS.md,
and 22_BASELINE_FIDELITY_PROTOCOL.md.
"""

from __future__ import annotations

from prorag_fl.baselines.bc2fl import Bc2FLBaseline
from prorag_fl.baselines.centralized_ids import Centralized1DCNNBaseline
from prorag_fl.baselines.common import (
    BaseBaseline,
    BaselineEvaluationResult,
    compute_standard_metrics,
)
from prorag_fl.baselines.fedmse import FedMSEBaseline
from prorag_fl.baselines.fl_controls import StandardFLBaseline
from prorag_fl.baselines.flow import FlowBaseline
from prorag_fl.baselines.local_ids import Local1DCNNBaseline
from prorag_fl.baselines.lqb_ids import LQBIDSBaseline
from prorag_fl.baselines.pfl_ids import PFLIDSBaseline
from prorag_fl.baselines.rlfe_ids import RLFEIDSBaseline
from prorag_fl.baselines.sflnid import SFLNIDBaseline

__all__ = [
    "BaseBaseline",
    "BaselineEvaluationResult",
    "compute_standard_metrics",
    "Local1DCNNBaseline",
    "Centralized1DCNNBaseline",
    "StandardFLBaseline",
    "SFLNIDBaseline",
    "FlowBaseline",
    "Bc2FLBaseline",
    "RLFEIDSBaseline",
    "LQBIDSBaseline",
    "FedMSEBaseline",
    "PFLIDSBaseline",
]
