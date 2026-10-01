"""Data loading, preprocessing, and partitioning module for ProRAG-FL."""

from prorag_fl.data.adapter import DatasetAdapter
from prorag_fl.data.ciciot2023 import CICIOT2023_FAMILY_MAP, ORDERED_FAMILIES, CICIoT2023Adapter
from prorag_fl.data.edge_iiotset import (
    EDGE_IIOTSET_FAMILY_MAP,
    ORDERED_EDGE_FAMILIES,
    EdgeIIoTsetAdapter,
)
from prorag_fl.data.partitioning import partition_dirichlet, partition_iid
from prorag_fl.data.preprocessor import FittedPreprocessor
from prorag_fl.data.quality import generate_data_quality_report

__all__ = [
    "DatasetAdapter",
    "CICIoT2023Adapter",
    "CICIOT2023_FAMILY_MAP",
    "ORDERED_FAMILIES",
    "EdgeIIoTsetAdapter",
    "EDGE_IIOTSET_FAMILY_MAP",
    "ORDERED_EDGE_FAMILIES",
    "FittedPreprocessor",
    "partition_iid",
    "partition_dirichlet",
    "generate_data_quality_report",
]
