"""ProRAG-FL Experiment Matrix and Execution Framework."""

from prorag_fl.experiments.planner import (
    compute_resource_estimates,
    expand_matrix_plan,
    generate_planning_markdown,
)
from prorag_fl.experiments.runner import ExperimentRunner
from prorag_fl.experiments.schemas import (
    ArtifactEntry,
    ExperimentDescriptor,
    ExperimentType,
    MatrixPlanSummary,
    RunArtifactManifest,
    RunFailureRecord,
    RunStatus,
)
from prorag_fl.experiments.smoke import generate_smoke_descriptors, run_smoke_matrix

__all__ = [
    "ArtifactEntry",
    "ExperimentDescriptor",
    "ExperimentRunner",
    "ExperimentType",
    "MatrixPlanSummary",
    "RunArtifactManifest",
    "RunFailureRecord",
    "RunStatus",
    "compute_resource_estimates",
    "expand_matrix_plan",
    "generate_planning_markdown",
    "generate_smoke_descriptors",
    "run_smoke_matrix",
]
