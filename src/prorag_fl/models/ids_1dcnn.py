"""Locked 1D-CNN IDS Architecture for ProRAG-FL conforming to 10_LOCAL_IDS_1DCNN.md."""

from __future__ import annotations

from typing import NamedTuple

import torch
import torch.nn as nn


class ModelOutput(NamedTuple):
    """Container for model outputs supporting both tuple unpacking and named access."""

    logits: torch.Tensor
    embedding: torch.Tensor


class IDS1DCNN(nn.Module):
    """1D-CNN Intrusion Detection System Network.

    Architecture (Locked Specification):
    - Block 1: Conv1d(1, 64, k=3, p=1) -> BatchNorm1d(64) -> ReLU
    - Block 2: Conv1d(64, 128, k=3, p=1) -> BatchNorm1d(128) -> ReLU -> MaxPool1d(2)
    - Block 3: Conv1d(128, 256, k=3, p=1) -> ReLU -> AdaptiveAvgPool1d(1)
    - Embedding: Flatten -> Linear(256, 128) -> ReLU
    - Head: Dropout(0.30) -> Linear(128, num_classes)

    Returns:
        ModelOutput(logits=[B, num_classes], embedding=[B, 128])
        No softmax is applied to logits before cross-entropy.
    """

    def __init__(self, num_features: int, num_classes: int, dropout_rate: float = 0.30) -> None:
        super().__init__()
        self.num_features = num_features
        self.num_classes = num_classes
        self.dropout_rate = dropout_rate

        # Block 1
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=64, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(64)
        self.relu1 = nn.ReLU()

        # Block 2
        self.conv2 = nn.Conv1d(in_channels=64, out_channels=128, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(128)
        self.relu2 = nn.ReLU()
        self.pool2 = nn.MaxPool1d(kernel_size=2)

        # Block 3
        self.conv3 = nn.Conv1d(in_channels=128, out_channels=256, kernel_size=3, padding=1)
        self.relu3 = nn.ReLU()
        self.global_pool = nn.AdaptiveAvgPool1d(1)

        # Dense embedding representation
        self.flatten = nn.Flatten()
        self.fc_embed = nn.Linear(in_features=256, out_features=128)
        self.relu_embed = nn.ReLU()

        # Classification head
        self.dropout = nn.Dropout(p=dropout_rate)
        self.classifier = nn.Linear(in_features=128, out_features=num_classes)

        # Weight initialization
        self._initialize_weights()

    def _initialize_weights(self) -> None:
        """Kaiming normal initialization for conv and linear layers."""
        for m in self.modules():
            if isinstance(m, nn.Conv1d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0.0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1.0)
                nn.init.constant_(m.bias, 0.0)
            elif isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0.0)

    def forward(self, x: torch.Tensor) -> ModelOutput:
        """Forward pass through the 1D-CNN.

        Args:
            x: Input tensor of shape [B, F] or [B, 1, F].

        Returns:
            ModelOutput with unnormalized logits [B, num_classes] and 128-D embedding [B, 128].
        """
        if x.dim() == 2:
            # Reshape [B, F] -> [B, 1, F]
            x = x.unsqueeze(1)
        elif x.dim() != 3 or x.size(1) != 1:
            raise ValueError(f"Expected input shape [B, F] or [B, 1, F], got {list(x.shape)}")

        # Block 1
        h = self.conv1(x)
        h = self.bn1(h)
        h = self.relu1(h)

        # Block 2
        h = self.conv2(h)
        h = self.bn2(h)
        h = self.relu2(h)
        h = self.pool2(h)

        # Block 3
        h = self.conv3(h)
        h = self.relu3(h)
        h = self.global_pool(h)

        # Embedding [B, 128]
        h_flat = self.flatten(h)
        embedding = self.relu_embed(self.fc_embed(h_flat))

        # Classification logits [B, num_classes] (No softmax)
        logits = self.classifier(self.dropout(embedding))

        return ModelOutput(logits=logits, embedding=embedding)

    def get_embedding(self, x: torch.Tensor) -> torch.Tensor:
        """Extract the 128-D feature embedding directly."""
        return self.forward(x).embedding
