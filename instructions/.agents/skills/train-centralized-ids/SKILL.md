---
name: train-centralized-ids
description: Implements the frozen PyTorch 1D-CNN, local/centralized controls, temperature calibration, 128-D embeddings, and Mahalanobis OOD.
---
# Train IDS
Use architecture from AGENTS.md. Implement train/validation/checkpoint/evaluator/per-class metrics. Fit temperature only on validation. Fit Mahalanobis means/covariance using known training representation; choose OOD threshold on validation. Tests: shapes, gradient, tiny-batch overfit, checkpoint round-trip, deterministic inference, no test-label access. Produce Local and Centralized 1D-CNN baselines and model card.
