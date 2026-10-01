"""Unit tests for Phase 2 1D-CNN IDS Architecture, Trainer, and ModelCard."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch
import torch.nn as nn

from prorag_fl.core.seeding import set_seed
from prorag_fl.models.ids_1dcnn import IDS1DCNN, ModelOutput
from prorag_fl.models.model_card import generate_model_card
from prorag_fl.models.trainer import IDSTrainer
from prorag_fl.models.utils import compute_class_weights, create_ids_data_loader


@pytest.fixture
def mock_dimensions() -> tuple[int, int, int]:
    """Batch size, num_features, num_classes."""
    return 16, 46, 8


@pytest.mark.unit
def test_1dcnn_output_and_embedding_shapes(mock_dimensions: tuple[int, int, int]) -> None:
    """Requirement 1: Verify output logits and 128-D embedding shapes for 2D and 3D inputs."""
    batch_size, num_features, num_classes = mock_dimensions
    model = IDS1DCNN(num_features=num_features, num_classes=num_classes)
    model.eval()

    # Test with 2D input [B, F]
    x_2d = torch.randn(batch_size, num_features)
    out_2d = model(x_2d)
    assert isinstance(out_2d, ModelOutput)
    assert out_2d.logits.shape == (batch_size, num_classes)
    assert out_2d.embedding.shape == (batch_size, 128)

    # Test tuple unpacking
    logits, emb = model(x_2d)
    assert logits.shape == (batch_size, num_classes)
    assert emb.shape == (batch_size, 128)

    # Test with 3D input [B, 1, F]
    x_3d = torch.randn(batch_size, 1, num_features)
    out_3d = model(x_3d)
    assert out_3d.logits.shape == (batch_size, num_classes)
    assert out_3d.embedding.shape == (batch_size, 128)


@pytest.mark.unit
def test_1dcnn_finite_gradients_to_every_block(mock_dimensions: tuple[int, int, int]) -> None:
    """Requirement 2: Verify finite non-zero gradients flow to every trainable layer."""
    batch_size, num_features, num_classes = mock_dimensions
    model = IDS1DCNN(num_features=num_features, num_classes=num_classes)
    model.train()

    x = torch.randn(batch_size, num_features)
    y = torch.randint(0, num_classes, (batch_size,))
    criterion = nn.CrossEntropyLoss()

    output = model(x)
    loss = criterion(output.logits, y)
    loss.backward()

    for name, param in model.named_parameters():
        if param.requires_grad:
            assert param.grad is not None, f"Parameter {name} has no gradient!"
            assert torch.isfinite(param.grad).all(), f"Parameter {name} has non-finite gradients!"
            assert param.grad.abs().sum().item() > 0.0, f"Parameter {name} has dead zero gradients!"


@pytest.mark.unit
def test_1dcnn_tiny_batch_overfit() -> None:
    """Requirement 3: Verify model can overfit a tiny batch (loss -> 0, accuracy -> 100%)."""
    set_seed(13)
    num_features = 32
    num_classes = 4
    batch_size = 16

    model = IDS1DCNN(num_features=num_features, num_classes=num_classes, dropout_rate=0.0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.01, weight_decay=0.0)
    criterion = nn.CrossEntropyLoss()

    x = torch.randn(batch_size, num_features)
    y = torch.randint(0, num_classes, (batch_size,))

    model.train()
    for _ in range(60):
        optimizer.zero_grad()
        output = model(x)
        loss = criterion(output.logits, y)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        final_out = model(x)
        final_loss = criterion(final_out.logits, y).item()
        preds = torch.argmax(final_out.logits, dim=1)
        acc = (preds == y).float().mean().item()

    assert final_loss < 0.10, f"Overfit loss {final_loss:.4f} not sufficiently small"
    assert acc == 1.0, f"Overfit accuracy {acc * 100:.1f}% is not 100%"


@pytest.mark.unit
def test_1dcnn_checkpoint_save_load_identical_logits(mock_dimensions: tuple[int, int, int]) -> None:
    """Requirement 4: Verify checkpoint save/load produces byte-identical logits."""
    batch_size, num_features, num_classes = mock_dimensions
    set_seed(42)

    model1 = IDS1DCNN(num_features=num_features, num_classes=num_classes)
    trainer1 = IDSTrainer(model=model1, lr=0.001)

    with tempfile.TemporaryDirectory() as tmp_dir:
        ckpt_path = Path(tmp_dir) / "test_model.pt"
        saved_path, digest = trainer1.save_checkpoint(ckpt_path)

        assert saved_path.exists()
        assert len(digest) == 64  # Valid SHA-256 hex string

        # Initialize fresh model and load
        model2 = IDS1DCNN(num_features=num_features, num_classes=num_classes)
        trainer2 = IDSTrainer(model=model2, lr=0.001)
        trainer2.load_checkpoint(saved_path)

        # Compare outputs on deterministic evaluation input
        x = torch.randn(batch_size, num_features).to(trainer1.device)
        model1.eval()
        model2.eval()
        with torch.no_grad():
            out1 = model1(x)
            out2 = model2(x)

        assert torch.allclose(out1.logits, out2.logits, atol=1e-6)
        assert torch.allclose(out1.embedding, out2.embedding, atol=1e-6)


@pytest.mark.unit
def test_1dcnn_seed_determinism(mock_dimensions: tuple[int, int, int]) -> None:
    """Requirement 5: Same seed produces deterministic initial weights and first batch output."""
    batch_size, num_features, num_classes = mock_dimensions

    # Run 1
    set_seed(73)
    model_a = IDS1DCNN(num_features=num_features, num_classes=num_classes)
    x_a = torch.randn(batch_size, num_features)
    model_a.eval()
    with torch.no_grad():
        out_a = model_a(x_a)

    # Run 2 with identical seed
    set_seed(73)
    model_b = IDS1DCNN(num_features=num_features, num_classes=num_classes)
    x_b = torch.randn(batch_size, num_features)
    model_b.eval()
    with torch.no_grad():
        out_b = model_b(x_b)

    assert torch.allclose(x_a, x_b, atol=1e-7), "Input tensors under same seed differed!"
    assert torch.allclose(out_a.logits, out_b.logits, atol=1e-6), "Logits under same seed differed!"
    assert torch.allclose(out_a.embedding, out_b.embedding, atol=1e-6), "Embeddings differed!"


@pytest.mark.unit
def test_1dcnn_trainer_defense_blocks_test_loader(mock_dimensions: tuple[int, int, int]) -> None:
    """Requirement 6: IDSTrainer strictly rejects any test loader to prevent leakage."""
    _, num_features, num_classes = mock_dimensions
    model = IDS1DCNN(num_features=num_features, num_classes=num_classes)
    trainer = IDSTrainer(model=model)

    train_loader = create_ids_data_loader(np.zeros((10, num_features)), np.zeros(10), batch_size=5)
    val_loader = create_ids_data_loader(np.zeros((5, num_features)), np.zeros(5), batch_size=5)
    test_loader_forbidden = create_ids_data_loader(
        np.zeros((5, num_features)), np.zeros(5), batch_size=5
    )

    with pytest.raises(ValueError, match="TEST FIREWALL BREACH"):
        trainer.fit(
            train_loader=train_loader,
            val_loader=val_loader,
            max_epochs=1,
            test_loader=test_loader_forbidden,
        )


@pytest.mark.unit
def test_class_weights_computation() -> None:
    """Verify class weights formula from training labels only."""
    # 100 benign (class 0), 10 attack A (class 1), 0 held-out (class 2)
    labels = np.array([0] * 100 + [1] * 10)
    weights = compute_class_weights(labels, num_classes=3, norm=True)

    assert weights.shape == (3,)
    assert weights[0] < weights[1], "Frequent class should have lower weight than minority class"
    assert weights[2] == 0.0, "Absent / held-out class must have 0 weight"


@pytest.mark.unit
def test_model_card_generation(mock_dimensions: tuple[int, int, int]) -> None:
    """Verify ModelCard metadata, architecture summary, and serialization."""
    _, num_features, num_classes = mock_dimensions
    model = IDS1DCNN(num_features=num_features, num_classes=num_classes)

    with tempfile.TemporaryDirectory() as tmp_dir:
        card_path = Path(tmp_dir) / "model_card.json"
        card = generate_model_card(
            model=model,
            dataset_name="ciciot2023",
            run_id="test_run_001",
            classes=["Benign", "DDoS", "DoS", "Recon", "Web", "Spoofing", "BruteForce", "Mirai"],
            preprocessor_hash="abc123hash",
            checkpoint_path="checkpoints/model.pt",
            checkpoint_digest="deadbeef1234",
            seed=13,
            training_history={"epochs": [1, 2], "val_loss": [0.5, 0.4]},
            best_epoch=2,
            best_val_loss=0.4,
            output_path=card_path,
        )

        assert card_path.exists()
        assert card.num_features == num_features
        assert card.num_classes == num_classes
        assert card.total_parameters > 0
        assert "Conv1d" in card.architecture_summary
        assert card.environment_snapshot is not None
