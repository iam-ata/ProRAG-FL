# Phase 2 — Local and Centralized 1D-CNN IDS

## Input
Processed row `[F]` becomes batch tensor `[B,1,F]`.

## Architecture
```text
Conv1d(1,64,k=3,padding=1)
BatchNorm1d(64)
ReLU
Conv1d(64,128,k=3,padding=1)
BatchNorm1d(128)
ReLU
MaxPool1d(2)
Conv1d(128,256,k=3,padding=1)
ReLU
AdaptiveAvgPool1d(1)
Flatten
Linear(256,128)
ReLU
Dropout(0.30)
Linear(128,num_classes)
```
Return both logits and 128-D embedding. Do not apply softmax before cross-entropy.

## Training defaults
- AdamW;
- lr 0.001;
- weight decay 0.0001;
- batch 256;
- class-weighted CE;
- deterministic seed controls;
- centralized early stopping based only on validation.

## Centralized control
Train on union of all training-client data using the same preprocessor/validation/test. It is an oracle centralized reference, not privacy-preserving deployment.

## Local control
Each client trains independently from the same initialization. Evaluate per-client and on common test where scientifically appropriate.

## Class weights
Compute from training labels only and save the exact vector.

## Required debug tests
1. output/embedding shapes;
2. finite gradients to every trainable block;
3. tiny-batch overfit;
4. checkpoint save/load produces identical logits;
5. same seed -> deterministic first-batch/evaluation within documented tolerance;
6. no test loader is reachable by the trainer.

## Model card
Save architecture, parameters, feature count, classes, optimizer/loss, hardware, preprocessor hash, checkpoint digest, and train/validation history.
