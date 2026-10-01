"""Adversarial attacks and threat models suite for ProRAG-FL.

Adheres strictly to instructions/18_ATTACKS_AND_THREAT_MODEL.md.
"""

from __future__ import annotations

from prorag_fl.attacks.backdoor import TabularBackdoorAttacker
from prorag_fl.attacks.dos_amplification import RAGAmplificationAttacker
from prorag_fl.attacks.fl_poisoning import (
    LabelFlippingAttacker,
    ModelReplacementAttacker,
    SignFlippingAttacker,
)
from prorag_fl.attacks.knowledge_attacks import KnowledgeAttacker
from prorag_fl.attacks.provenance_attacks import ProvenanceAttacker
from prorag_fl.attacks.schemas import AttackEvaluationReport, AttackManifest

__all__ = [
    "AttackManifest",
    "AttackEvaluationReport",
    "LabelFlippingAttacker",
    "SignFlippingAttacker",
    "ModelReplacementAttacker",
    "TabularBackdoorAttacker",
    "ProvenanceAttacker",
    "KnowledgeAttacker",
    "RAGAmplificationAttacker",
]
