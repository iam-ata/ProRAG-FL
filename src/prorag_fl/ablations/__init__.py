"""Phase 13: Ablation and Sensitivity Analysis.

Provides:
- A0 to A6 architectural ladder configs and runner
- Validation-only sensitivity sweeps
- Multi-objective scoring and parameter freezing
- Markdown reporting for comparative analysis and paper sync
"""

from __future__ import annotations

from prorag_fl.ablations.ladder import (
    AblationLadderRunner,
    get_ladder_config,
)
from prorag_fl.ablations.reporting import (
    generate_ladder_markdown,
    generate_sensitivity_markdown,
)
from prorag_fl.ablations.schemas import (
    AblationLadderReport,
    AblationStepConfig,
    AblationStepResult,
    FrozenParametersRecord,
    LadderStep,
    SensitivityGridPoint,
    SensitivityReport,
)
from prorag_fl.ablations.sensitivity import (
    SensitivityEvaluator,
    assert_parameters_frozen,
    load_frozen_parameters,
)

__all__ = [
    "AblationLadderReport",
    "AblationLadderRunner",
    "AblationStepConfig",
    "AblationStepResult",
    "FrozenParametersRecord",
    "LadderStep",
    "SensitivityEvaluator",
    "SensitivityGridPoint",
    "SensitivityReport",
    "assert_parameters_frozen",
    "generate_ladder_markdown",
    "generate_sensitivity_markdown",
    "get_ladder_config",
    "load_frozen_parameters",
]
