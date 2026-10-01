"""Cryptographic Merkle tree implementation with audit path proofs and tamper verification."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from prorag_fl.schemas.knowledge import MerkleProofStep


def hash_leaf(data: bytes | str) -> str:
    """Compute SHA-256 leaf hash from raw or string chunk data."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def hash_internal(left_hex: str, right_hex: str) -> str:
    """Compute parent hash by concatenating binary representations of left and right child hashes."""
    left_bytes = bytes.fromhex(left_hex)
    right_bytes = bytes.fromhex(right_hex)
    return hashlib.sha256(left_bytes + right_bytes).hexdigest()


class MerkleTree:
    """Cryptographic Merkle Tree adhering strictly to Phase 6 specifications.

    - Leaf k = SHA-256(canonical_chunk_bytes)
    - Parent = SHA-256(left_bytes || right_bytes)
    - Odd leaf handling: Duplicates the last node at that tree level.
    """

    def __init__(self, leaves: Sequence[str | bytes]) -> None:
        if not leaves:
            raise ValueError("Cannot construct a MerkleTree with empty leaves.")

        # Convert all leaves to hex strings
        self.leaf_hashes: list[str] = [
            leaf if isinstance(leaf, str) and len(leaf) == 64 else hash_leaf(leaf)
            for leaf in leaves
        ]

        # Build full level-by-level tree: levels[0] is leaves, levels[-1][0] is root
        self.levels: list[list[str]] = [list(self.leaf_hashes)]
        self._build_tree()

    def _build_tree(self) -> None:
        """Construct parent levels up to root."""
        current_level = self.levels[0]

        while len(current_level) > 1:
            next_level: list[str] = []
            n = len(current_level)

            for i in range(0, n, 2):
                left = current_level[i]
                # Odd-leaf handling: duplicate last leaf if odd count
                right = current_level[i + 1] if i + 1 < n else left
                parent = hash_internal(left, right)
                next_level.append(parent)

            self.levels.append(next_level)
            current_level = next_level

    @property
    def root(self) -> str:
        """Return the hex-encoded SHA-256 Merkle root hash."""
        return self.levels[-1][0]

    def get_proof(self, leaf_index: int) -> list[MerkleProofStep]:
        """Generate audit path (Merkle proof) for a specific leaf index."""
        if leaf_index < 0 or leaf_index >= len(self.leaf_hashes):
            raise IndexError(
                f"Leaf index {leaf_index} out of bounds for tree with {len(self.leaf_hashes)} leaves."
            )

        proof: list[MerkleProofStep] = []
        idx = leaf_index

        for level in self.levels[:-1]:
            n = len(level)
            if idx % 2 == 0:
                # Sibling is on the right
                sibling_idx = idx + 1 if idx + 1 < n else idx
                sibling_hash = level[sibling_idx]
                proof.append(MerkleProofStep(position="right", sibling_hash=sibling_hash))
            else:
                # Sibling is on the left
                sibling_idx = idx - 1
                sibling_hash = level[sibling_idx]
                proof.append(MerkleProofStep(position="left", sibling_hash=sibling_hash))

            idx = idx // 2

        return proof


def verify_merkle_proof(
    leaf_hash: str,
    proof: Sequence[MerkleProofStep],
    expected_root: str,
) -> bool:
    """Verify an audit path from leaf to root.

    Returns True if and only if reconstructing the parent chain from the leaf_hash
    and proof steps matches expected_root exactly.
    """
    if len(leaf_hash) != 64 or len(expected_root) != 64:
        return False

    current = leaf_hash

    for step in proof:
        if step.position == "right":
            current = hash_internal(current, step.sibling_hash)
        elif step.position == "left":
            current = hash_internal(step.sibling_hash, current)
        else:
            return False

    return current.lower() == expected_root.lower()
