"""Automated downloader helper for CICIoT2023 and Edge-IIoTset datasets."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def get_target_dirs(base_code_dir: Path) -> tuple[Path, Path]:
    ciciot_dir = base_code_dir / "data" / "raw" / "CICIoT2023"
    edge_dir = base_code_dir / "data" / "raw" / "EdgeIIoTset"
    ciciot_dir.mkdir(parents=True, exist_ok=True)
    edge_dir.mkdir(parents=True, exist_ok=True)
    return ciciot_dir, edge_dir


def download_via_kaggle(dataset_name: str, target_dir: Path) -> bool:
    """Download and unzip a dataset from Kaggle via kaggle CLI."""
    slugs = {
        "ciciot2023": "dhoogla/ciciot2023",
        "edge_iiotset": "mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot",
    }
    slug = slugs.get(dataset_name)
    if not slug:
        print(f"Unknown dataset: {dataset_name}")
        return False

    cmd = [
        "kaggle",
        "datasets",
        "download",
        "-d",
        slug,
        "-p",
        str(target_dir),
        "--unzip",
    ]
    print(f"Running: {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, check=True)
        return res.returncode == 0
    except Exception as e:
        print(f"Kaggle download failed: {e}")
        print("Ensure 'kaggle' is installed and ~/.kaggle/kaggle.json credentials exist.")
        return False


def download_via_huggingface(repo_id: str, target_dir: Path) -> bool:
    """Download dataset repository from Hugging Face."""
    print(f"Downloading {repo_id} from Hugging Face into {target_dir}...")
    try:
        from huggingface_hub import snapshot_download

        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            local_dir=str(target_dir),
            local_dir_use_symlinks=False,
        )
        print("Hugging Face download complete!")
        return True
    except Exception as e:
        print(f"Hugging Face download failed: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Download ProRAG-FL datasets.")
    parser.add_argument(
        "--dataset",
        choices=["ciciot2023", "edge_iiotset", "both"],
        default="both",
        help="Dataset to download",
    )
    parser.add_argument(
        "--source",
        choices=["kaggle", "huggingface"],
        default="kaggle",
        help="Download source (kaggle CLI or huggingface hub)",
    )
    args = parser.parse_args()

    code_dir = Path(__file__).resolve().parent.parent
    ciciot_dir, edge_dir = get_target_dirs(code_dir)

    if args.dataset in ("ciciot2023", "both"):
        print(f"\nTarget path for CICIoT2023: {ciciot_dir.as_posix()}")
        if args.source == "kaggle":
            download_via_kaggle("ciciot2023", ciciot_dir)
        else:
            download_via_huggingface("bencorn/CIC-IoT-2023", ciciot_dir)

    if args.dataset in ("edge_iiotset", "both"):
        print(f"\nTarget path for Edge-IIoTset: {edge_dir.as_posix()}")
        if args.source == "kaggle":
            download_via_kaggle("edge_iiotset", edge_dir)
        else:
            print("Edge-IIoTset is primarily hosted on Kaggle and IEEE Dataport.")
            download_via_kaggle("edge_iiotset", edge_dir)


if __name__ == "__main__":
    main()
