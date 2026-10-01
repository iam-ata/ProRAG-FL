"""Out-of-Distribution detection and escalation gate module for ProRAG-FL."""

from prorag_fl.ood.dual_gate import DualGate
from prorag_fl.ood.mahalanobis import MahalanobisOODDetector

__all__ = [
    "MahalanobisOODDetector",
    "DualGate",
]
