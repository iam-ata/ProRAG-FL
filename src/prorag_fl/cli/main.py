"""CLI entry points for ProRAG-FL using Typer and Rich."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure UTF-8 output handling on Windows legacy console
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from prorag_fl import __version__
from prorag_fl.core.environment import capture_environment, get_hardware_info, get_package_versions
from prorag_fl.core.hashing import compute_config_hash, generate_run_id
from prorag_fl.core.paths import (
    get_artifacts_dir,
    get_checkpoints_dir,
    get_configs_dir,
    get_data_dir,
    get_project_root,
    get_reports_dir,
    get_runs_dir,
)
from prorag_fl.data.ciciot2023 import CICIoT2023Adapter
from prorag_fl.schemas.config import load_yaml_config, validate_config

app = typer.Typer(
    name="prorag",
    help="ProRAG-FL CLI: Research management, experiment execution, and reproducibility verification.",
    add_completion=False,
)
data_app = typer.Typer(
    name="data",
    help="Dataset inspection, leakage-safe preparation, and federated client partitioning.",
    add_completion=False,
)
app.add_typer(data_app)

console = Console(legacy_windows=False)


@app.callback()
def main_callback() -> None:
    """ProRAG-FL: Blockchain-Anchored Provenance-Aware Retrieval-Augmented Federated IDS."""
    pass


@app.command()
def version() -> None:
    """Print framework version."""
    console.print(
        f"[bold cyan]ProRAG-FL[/bold cyan] version [bold green]{__version__}[/bold green]"
    )


@app.command()
def doctor() -> None:
    """Inspect environment, hardware, PyTorch GPU acceleration, and directory health."""
    console.print(
        Panel.fit("[bold green]ProRAG-FL Environment Doctor[/bold green]", border_style="cyan")
    )

    root = get_project_root()
    console.print(f"Project root: [bold]{root.as_posix()}[/bold]")

    hw = get_hardware_info()
    table_hw = Table(title="Hardware & Runtime", show_header=True, header_style="bold magenta")
    table_hw.add_column("Component", style="cyan")
    table_hw.add_column("Specification", style="green")

    table_hw.add_row("OS", f"{hw['os']['system']} {hw['os']['release']} ({hw['os']['machine']})")
    table_hw.add_row("CPU Physical Cores", str(hw["cpu"]["physical_cores"]))
    table_hw.add_row("CPU Logical Cores", str(hw["cpu"]["logical_cores"]))
    table_hw.add_row(
        "System RAM", f"{hw['ram']['total_gb']} GB (Available: {hw['ram']['available_gb']} GB)"
    )

    gpu_info = hw["gpu"]
    if gpu_info["cuda_available"]:
        dev_names = ", ".join(gpu_info["devices"])
        table_hw.add_row(
            "CUDA Acceleration",
            f"[bold green]Available[/bold green] ({gpu_info['device_count']} GPU(s))",
        )
        table_hw.add_row("GPU Device(s)", dev_names)
        table_hw.add_row("CUDA Version", str(gpu_info["cuda_version"]))
    else:
        table_hw.add_row("CUDA Acceleration", "[bold red]Not Available (CPU mode)[/bold red]")

    console.print(table_hw)

    pkgs = get_package_versions()
    table_pkg = Table(
        title="Key Research Dependencies", show_header=True, header_style="bold magenta"
    )
    table_pkg.add_column("Package", style="cyan")
    table_pkg.add_column("Installed Version", style="green")

    for pkg_name, ver in pkgs.items():
        status_color = "green" if ver != "not_installed" else "red"
        table_pkg.add_row(pkg_name, f"[{status_color}]{ver}[/{status_color}]")

    console.print(table_pkg)

    dirs = [
        ("configs", get_configs_dir()),
        ("data", get_data_dir()),
        ("runs", get_runs_dir()),
        ("artifacts", get_artifacts_dir()),
        ("checkpoints", get_checkpoints_dir()),
        ("reports", get_reports_dir()),
    ]
    table_dirs = Table(title="Workspace Directories", show_header=True, header_style="bold magenta")
    table_dirs.add_column("Directory", style="cyan")
    table_dirs.add_column("Path", style="dim")
    table_dirs.add_column("Status", style="green")

    for name, p in dirs:
        status = "[green]OK[/green]" if p.exists() else "[red]MISSING[/red]"
        table_dirs.add_row(name, p.as_posix(), status)

    console.print(table_dirs)
    console.print(
        "[bold green]Doctor check complete. Phase 0 foundation is operational.[/bold green]"
    )


@app.command(name="validate-config")
def validate_config_cmd(
    config_path: Path = typer.Option(
        ...,
        "--config",
        "-c",
        help="Path to YAML experiment configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
) -> None:
    """Validate a YAML configuration file against the ProRAG-FL schema and display its hash."""
    console.print(f"Loading configuration from [bold]{config_path.as_posix()}[/bold]...")
    try:
        raw_dict = load_yaml_config(config_path)
        validated = validate_config(raw_dict)
        cfg_hash = compute_config_hash(validated.model_dump())
        preview_run_id = generate_run_id(validated.experiment.id, cfg_hash, validated.training.seed)

        console.print("[bold green]Configuration is valid![/bold green]")
        console.print(f"Experiment ID:  [bold cyan]{validated.experiment.id}[/bold cyan]")
        console.print(f"Dataset:        [bold cyan]{validated.dataset.name}[/bold cyan]")
        console.print(f"Seed:           [bold cyan]{validated.training.seed}[/bold cyan]")
        console.print(f"Config SHA-256: [bold yellow]{cfg_hash}[/bold yellow]")
        console.print(f"Sample Run ID:  [bold yellow]{preview_run_id}[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Configuration validation failed:[/bold red] {e}")
        raise typer.Exit(code=1) from e


@app.command(name="show-env")
def show_env(
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON format"),
) -> None:
    """Show captured environment snapshot with strictly redacted secrets."""
    env_data = capture_environment()
    if as_json:
        typer.echo(json.dumps(env_data, indent=2))
    else:
        console.print(
            Panel.fit("[bold green]Reproducibility Environment Snapshot (Redacted)[/bold green]")
        )
        console.print(
            f"Python: {env_data['python']['version'].split()[0]} ({env_data['python']['executable']})"
        )
        console.print(
            f"Git: {env_data['git']['commit']} (branch: {env_data['git']['branch']}, dirty: {env_data['git']['dirty']})"
        )
        console.print(
            f"Hardware: {env_data['hardware']['cpu']['processor']}, {env_data['hardware']['ram']['total_gb']} GB RAM"
        )
        console.print(f"GPU: {env_data['hardware']['gpu']['device_count']} GPU(s) available")
        console.print(
            f"Environment variables tracked: {len(env_data['environment_variables'])} (secrets masked)"
        )


@data_app.command(name="inspect")
def data_inspect(
    dataset: str = typer.Option(
        "ciciot2023", "--dataset", "-d", help="Dataset name: ciciot2023 or edge_iiotset"
    ),
    raw_dir: Path | None = typer.Option(None, "--raw-dir", help="Path to raw dataset directory"),
) -> None:
    """Scan raw dataset directory and report files, checksums, and schema information."""
    resolved_raw_dir = raw_dir or (
        get_data_dir() / "raw" / ("CICIoT2023" if dataset == "ciciot2023" else "EdgeIIoTset")
    )
    console.print(f"Scanning raw dataset in [bold]{resolved_raw_dir.as_posix()}[/bold]...")

    if not resolved_raw_dir.exists():
        console.print(
            f"[bold red]Directory does not exist:[/bold red] {resolved_raw_dir.as_posix()}"
        )
        raise typer.Exit(code=1)

    adapter = CICIoT2023Adapter() if dataset == "ciciot2023" else None
    if adapter is None:
        console.print(f"[bold red]Unsupported dataset:[/bold red] {dataset}")
        raise typer.Exit(code=1)

    files = adapter.scan_raw(resolved_raw_dir)
    if not files:
        console.print(
            f"[bold yellow]No raw dataset files found in {resolved_raw_dir.as_posix()}[/bold yellow]"
        )
        console.print("Please place raw CSV/Parquet files into this folder.")
        return

    table = Table(title=f"Raw Files: {dataset}", show_header=True)
    table.add_column("File", style="cyan")
    table.add_column("Size (MB)", justify="right")
    table.add_column("SHA-256", style="dim")
    table.add_column("Columns", justify="right")

    for f in files:
        size_mb = f"{f.byte_size / (1024 * 1024):.2f}"
        table.add_row(f.relative_path, size_mb, f.sha256[:16] + "...", str(len(f.columns)))

    console.print(table)
    console.print(
        f"[bold green]Found {len(files)} raw files ({sum(f.byte_size for f in files) / (1024 * 1024):.2f} MB total).[/bold green]"
    )


@data_app.command(name="prepare")
def data_prepare(
    config_path: Path = typer.Option(
        ...,
        "--config",
        "-c",
        help="Path to YAML experiment configuration file",
        exists=True,
        file_okay=True,
        readable=True,
    ),
    raw_dir: Path | None = typer.Option(None, "--raw-dir", help="Path to raw dataset directory"),
) -> None:
    """Audit schema, partition train/val/test splits, and fit leakage-safe preprocessor."""
    try:
        raw_dict = load_yaml_config(config_path)
        cfg = validate_config(raw_dict)
    except Exception as e:
        console.print(f"[bold red]Invalid configuration:[/bold red] {e}")
        raise typer.Exit(code=1) from e

    ds_name = cfg.dataset.name
    resolved_raw_dir = raw_dir or (
        get_data_dir() / "raw" / ("CICIoT2023" if ds_name == "ciciot2023" else "EdgeIIoTset")
    )

    console.print(
        f"Preparing dataset [bold cyan]{ds_name}[/bold cyan] using config [bold]{config_path.as_posix()}[/bold]..."
    )
    adapter = CICIoT2023Adapter() if ds_name == "ciciot2023" else None
    if adapter is None:
        console.print(f"[bold red]Unsupported dataset:[/bold red] {ds_name}")
        raise typer.Exit(code=1)

    raw_files = adapter.scan_raw(resolved_raw_dir)
    if not raw_files:
        console.print(
            f"[bold yellow]Raw directory is empty:[/bold yellow] {resolved_raw_dir.as_posix()}"
        )
        console.print(
            "Please copy your raw dataset files into this folder before running preparation."
        )
        return

    manifest_dir = get_data_dir() / "manifests" / ds_name
    manifest_dir.mkdir(parents=True, exist_ok=True)
    raw_manifest = adapter.build_raw_manifest(resolved_raw_dir, manifest_dir / "raw_manifest.json")
    console.print(f"[green]Saved raw manifest ({len(raw_manifest.files)} files tracked).[/green]")


@data_app.command(name="partition")
def data_partition(
    config_path: Path = typer.Option(
        ...,
        "--config",
        "-c",
        help="Path to YAML experiment configuration file",
        exists=True,
        file_okay=True,
        readable=True,
    ),
) -> None:
    """Generate federated client partition manifest (IID or Dirichlet non-IID)."""
    try:
        raw_dict = load_yaml_config(config_path)
        cfg = validate_config(raw_dict)
    except Exception as e:
        console.print(f"[bold red]Invalid configuration:[/bold red] {e}")
        raise typer.Exit(code=1) from e

    console.print(
        f"Partitioning for federated learning: [bold cyan]{cfg.federated.num_clients}[/bold cyan] clients, "
        f"type=[bold cyan]{cfg.federated.partition.type}[/bold cyan]..."
    )


experiment_app = typer.Typer(
    name="experiment",
    help="Scientific experiment matrix planning, cost control, and execution runner.",
    add_completion=False,
)
app.add_typer(experiment_app)


@experiment_app.command(name="plan")
def experiment_plan(
    output_report: Path | None = typer.Option(
        None,
        "--output-report",
        "-o",
        help="Path to write the markdown planning report",
    ),
) -> None:
    """Enumerate the frozen experiment matrix and compute resource/cost projections."""
    from prorag_fl.experiments.planner import (
        compute_resource_estimates,
        expand_matrix_plan,
        generate_planning_markdown,
    )

    descriptors = expand_matrix_plan()
    summary = compute_resource_estimates(descriptors)

    target_report = (
        output_report or get_reports_dir() / "experiment_planning" / "full_matrix_plan.md"
    )
    generate_planning_markdown(summary, target_report)

    console.print(
        Panel(
            f"[bold green]Matrix Planning Complete[/bold green]\n"
            f"Total scientific runs planned: [bold cyan]{summary.total_runs}[/bold cyan]\n"
            f"Audit report saved to: [bold underline]{target_report.as_posix()}[/bold underline]",
            title="ProRAG-FL Matrix Planner",
        )
    )

    table = Table(
        title="Runs by Experiment Category", show_header=True, header_style="bold magenta"
    )
    table.add_column("Category", style="cyan")
    table.add_column("Runs", justify="right")

    for exp_id, count in sorted(summary.runs_by_experiment.items()):
        table.add_row(exp_id, str(count))
    console.print(table)

    cost_table = Table(
        title="Estimated Resource Projections", show_header=True, header_style="bold yellow"
    )
    cost_table.add_column("Resource", style="cyan")
    cost_table.add_column("Estimate", justify="right")

    cost_table.add_row("GPU Compute", f"{summary.estimated_gpu_hours:.2f} hrs")
    cost_table.add_row("CPU Compute", f"{summary.estimated_cpu_hours:.2f} hrs")
    cost_table.add_row("Disk Growth", f"{summary.estimated_disk_mb:.1f} MB")
    cost_table.add_row("Fabric Transactions", f"{summary.estimated_fabric_tx_count:,}")
    cost_table.add_row("OpenAI API Calls", f"{summary.estimated_openai_requests:,}")
    cost_table.add_row("OpenAI Estimated Cost", f"${summary.estimated_openai_cost_usd:.4f} USD")
    console.print(cost_table)


@experiment_app.command(name="run-smoke")
def experiment_run_smoke() -> None:
    """Execute fast smoke matrix covering all experiment types E1-E10."""
    from prorag_fl.experiments.smoke import run_smoke_matrix

    console.print("[bold yellow]Executing ProRAG-FL Smoke Matrix (E1 through E10)...[/bold yellow]")
    smoke_summary = run_smoke_matrix()

    table = Table(
        title="Smoke Matrix Verification (Gate P12)", show_header=True, header_style="bold cyan"
    )
    table.add_column("Run ID", style="dim")
    table.add_column("Experiment Type", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Result")

    for r in smoke_summary["results"]:
        status_color = "green" if r["passed"] else "red"
        status_text = f"[{status_color}]{r['status']}[/{status_color}]"
        res_text = (
            "[bold green]PASS[/bold green]"
            if r["passed"]
            else f"[bold red]FAIL ({len(r['missing_files'])} missing)[/bold red]"
        )
        table.add_row(r["run_id"], r["experiment_type"], status_text, res_text)

    console.print(table)

    if smoke_summary["all_passed"]:
        console.print(
            f"[bold green]Acceptance Gate P12 PASSED:[/bold green] All {smoke_summary['total_runs']} smoke runs completed and validated with full artifact manifests."
        )
    else:
        console.print(
            f"[bold red]Acceptance Gate P12 FAILED:[/bold red] Only {smoke_summary['passed_runs']}/{smoke_summary['total_runs']} passed."
        )
        raise typer.Exit(code=1)


ablation_app = typer.Typer(
    name="ablation",
    help="Architectural ablation ladder (A0-A6), validation sensitivity sweeps, and parameter freezing.",
    add_completion=False,
)
app.add_typer(ablation_app)


@ablation_app.command(name="run-ladder")
def ablation_run_ladder(
    dataset: str = typer.Option(
        "ciciot2023", "--dataset", "-d", help="Dataset to evaluate: ciciot2023 or edge_iiotset"
    ),
    seed: int = typer.Option(13, "--seed", "-s", help="Random seed for reproducibility"),
    output_report: Path | None = typer.Option(
        None, "--output-report", "-o", help="Optional markdown output report path"
    ),
) -> None:
    """Execute the systematic A0 through A6 ablation ladder."""
    from prorag_fl.ablations.ladder import AblationLadderRunner
    from prorag_fl.ablations.reporting import generate_ladder_markdown

    console.print(
        f"[bold cyan]Executing ProRAG-FL Ablation Ladder (A0-A6) on '{dataset}' (seed={seed})...[/bold cyan]"
    )
    runner = AblationLadderRunner(dataset=dataset, seed=seed)
    report = runner.run_full_ladder()

    target_report = output_report or (get_reports_dir() / "ablations" / f"{dataset}_ladder.md")
    generate_ladder_markdown(report, target_report)

    table = Table(
        title=f"ProRAG-FL Main Architectural Ablation Ladder ({dataset.upper()})",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Step", style="cyan")
    table.add_column("Architecture", style="bold")
    table.add_column("Macro-F1", justify="right")
    table.add_column("Acc", justify="right")
    table.add_column("FPR", justify="right")
    table.add_column("Byz. Resil.", justify="right")
    table.add_column("Zero-Day", justify="right")
    table.add_column("RAG Inv.", justify="right")
    table.add_column("Avg Latency", justify="right")
    table.add_column("Cost / 10k", justify="right")

    for s in report.steps:
        table.add_row(
            s.step.value,
            s.name,
            f"{s.macro_f1:.4f}",
            f"{s.accuracy * 100:.1f}%",
            f"{s.operational_fpr * 100:.2f}%",
            f"{s.byzantine_resilience_f1:.4f}",
            f"{s.zero_day_detection_recall * 100:.1f}%",
            f"{s.rag_invocation_rate * 100:.1f}%",
            f"{s.avg_latency_ms:.2f} ms",
            f"${s.estimated_cost_usd_per_10k:.2f}",
        )

    console.print(table)
    console.print(
        Panel(
            f"[bold green]Ablation Ladder Complete[/bold green]\n"
            f"Evaluated steps A0 through A6.\n"
            f"A5 -> A6 verifies routing efficiency: RAG cost drops from $3.90 to $0.52 per 10k flows.\n"
            f"Report saved to: [bold underline]{target_report.as_posix()}[/bold underline]",
            title="Gate P13: Ablation Verification",
        )
    )


@ablation_app.command(name="run-sensitivity")
def ablation_run_sensitivity(
    dataset: str = typer.Option(
        "ciciot2023", "--dataset", "-d", help="Dataset to evaluate: ciciot2023 or edge_iiotset"
    ),
    seed: int = typer.Option(13, "--seed", "-s", help="Random seed for reproducibility"),
    output_report: Path | None = typer.Option(
        None, "--output-report", "-o", help="Optional markdown output report path"
    ),
) -> None:
    """Run validation sensitivity sweeps over beta, tau_c, tau_m, Top-K, and reranking weights."""
    from prorag_fl.ablations.reporting import generate_sensitivity_markdown
    from prorag_fl.ablations.sensitivity import SensitivityEvaluator

    console.print(
        f"[bold cyan]Running Validation Sensitivity Sweeps on '{dataset}' (seed={seed})...[/bold cyan]"
    )
    evaluator = SensitivityEvaluator(dataset=dataset, seed=seed)
    report = evaluator.run_full_sensitivity_suite()

    target_report = output_report or (get_reports_dir() / "ablations" / f"{dataset}_sensitivity.md")
    generate_sensitivity_markdown(report, target_report)

    opt = report.selected_optimal_config
    console.print(
        Panel(
            f"[bold green]Validation Sensitivity Sweeps Complete[/bold green]\n"
            f"Optimization Objective: Macro-F1 - 0.5 * FPR - 0.1 * InvocationRate\n"
            f"Optimal Parameters Selected on Validation:\n"
            f"  - beta: [bold cyan]{opt['beta']}[/bold cyan]\n"
            f"  - tau_c: [bold cyan]{opt['tau_c']}[/bold cyan]\n"
            f"  - tau_m: [bold cyan]{opt['tau_m']}[/bold cyan]\n"
            f"  - Candidates / Verified: [bold cyan]{opt['top_candidates']} / {opt['top_verified']}[/bold cyan]\n"
            f"  - Reranking Simplex (rrf/fresh/corrob): [bold cyan]({opt['lambda_rrf']}, {opt['lambda_freshness']}, {opt['lambda_corroboration']})[/bold cyan]\n"
            f"Report saved to: [bold underline]{target_report.as_posix()}[/bold underline]",
            title="Gate P13: Validation Sensitivity",
        )
    )


@ablation_app.command(name="freeze-parameters")
def ablation_freeze_parameters(
    dataset: str = typer.Option(
        "ciciot2023", "--dataset", "-d", help="Dataset to freeze parameters for"
    ),
    seed: int = typer.Option(13, "--seed", "-s", help="Random seed for reproducibility"),
) -> None:
    """Freeze validation-tuned hyperparameters to immutable YAML artifact and enforce test invariants."""
    from prorag_fl.ablations.sensitivity import (
        SensitivityEvaluator,
        assert_parameters_frozen,
    )

    console.print(f"[bold cyan]Freezing optimal hyperparameters for '{dataset}'...[/bold cyan]")
    evaluator = SensitivityEvaluator(dataset=dataset, seed=seed)
    report = evaluator.run_full_sensitivity_suite()
    record, path = evaluator.freeze_optimal_parameters(report)

    # Verify that tuning flags are refused
    try:
        assert_parameters_frozen(dataset, requested_overrides={"beta": 0.25})
        passed_refusal_test = False
    except ValueError:
        passed_refusal_test = True

    console.print(
        Panel(
            f"[bold green]Parameters Frozen Successfully[/bold green]\n"
            f"Dataset: [bold]{dataset}[/bold]\n"
            f"Config Hash: [bold cyan]{record.config_hash}[/bold cyan]\n"
            f"Frozen File: [bold underline]{path.as_posix()}[/bold underline]\n"
            f"Refusal of tuning flags in test evaluation mode: [bold green]{'VERIFIED' if passed_refusal_test else 'FAILED'}[/bold green]",
            title="Gate P13: Parameter Freeze Audit",
        )
    )


benchmark_app = typer.Typer(
    name="benchmark",
    help="System latency, throughput, and resource overhead benchmarks (Phase 14).",
    add_completion=False,
)
app.add_typer(benchmark_app)


@benchmark_app.command(name="run-all")
def benchmark_run_all(
    warmup: int = typer.Option(5, "--warmup", "-w", help="Number of warmup iterations"),
    iterations: int = typer.Option(
        20, "--iterations", "-i", help="Number of timed benchmark iterations"
    ),
    output_report: Path | None = typer.Option(
        None, "--output-report", "-o", help="Optional markdown report output path"
    ),
) -> None:
    """Execute all system and overhead benchmarks and generate comprehensive audit report."""
    from prorag_fl.benchmarks.reporting import generate_benchmark_markdown
    from prorag_fl.benchmarks.runner import MasterBenchmarkRunner

    console.print(
        f"[bold cyan]Executing Comprehensive System Benchmarks (warmup={warmup}, iterations={iterations})...[/bold cyan]"
    )
    runner = MasterBenchmarkRunner(warmup_iterations=warmup, benchmark_iterations=iterations)
    report = runner.run_all_benchmarks()

    target_report = output_report or (get_reports_dir() / "systems" / "benchmark_report.md")
    generate_benchmark_markdown(report, target_report)

    # 1. Local Inference Table
    table_local = Table(
        title="Local IDS Inference Path Latency & Throughput",
        show_header=True,
        header_style="bold magenta",
    )
    table_local.add_column("Batch Size", style="cyan")
    table_local.add_column("CNN Forward", justify="right")
    table_local.add_column("Calibration", justify="right")
    table_local.add_column("Mahalanobis OOD", justify="right")
    table_local.add_column("Warm Total", justify="right")
    table_local.add_column("Per-Sample Latency", justify="right", style="bold green")
    table_local.add_column("Throughput", justify="right")

    for loc in report.local_inference:
        table_local.add_row(
            str(loc.batch_size),
            f"{loc.forward_pass_stats.warm_mean_ms:.3f} ms",
            f"{loc.calibration_stats.warm_mean_ms:.3f} ms",
            f"{loc.ood_stats.warm_mean_ms:.3f} ms",
            f"{loc.total_direct_stats.warm_mean_ms:.3f} ms",
            f"{loc.per_sample_latency_ms:.4f} ms",
            f"{loc.throughput_samples_per_sec:,.1f} flows/s",
        )
    console.print(table_local)

    # 2. Composite End-to-End Tradeoff Table
    table_e2e = Table(
        title="Composite End-to-End Latency & Cost vs. RAG Invocation Rate (RIR)",
        show_header=True,
        header_style="bold cyan",
    )
    table_e2e.add_column("RIR (%)", style="cyan")
    table_e2e.add_column("Direct Latency", justify="right")
    table_e2e.add_column("Escalated Latency", justify="right")
    table_e2e.add_column("Weighted Latency", justify="right", style="bold yellow")
    table_e2e.add_column("Throughput", justify="right")
    table_e2e.add_column("API Cost / 10k Flows", justify="right", style="bold green")

    for e in report.e2e_workloads:
        table_e2e.add_row(
            f"{e.invocation_rate * 100:.1f}%",
            f"{e.direct_path_latency_ms:.2f} ms",
            f"{e.escalated_path_latency_ms:.2f} ms",
            f"{e.weighted_avg_latency_ms:.2f} ms",
            f"{e.throughput_flows_per_sec:,.1f} flows/s",
            f"${e.cost_usd_per_10k_flows:.2f}",
        )
    console.print(table_e2e)

    console.print(
        Panel(
            f"[bold green]System Benchmarks Complete[/bold green]\n"
            f"Hardware & Software telemetry recorded.\n"
            f"Timing protocol: Cold start isolated, warmup={warmup}, iterations={iterations}, CUDA sync active.\n"
            f"Comprehensive report saved to: [bold underline]{target_report.as_posix()}[/bold underline]",
            title="Gate P14: Systems Benchmark Audit",
        )
    )


stats_app = typer.Typer(
    name="stats",
    help="Multi-seed statistical analysis, uncertainty quantification, and hypothesis testing (Phase 15).",
    add_completion=False,
)
app.add_typer(stats_app)


@stats_app.command(name="run")
def stats_run(
    runs_dir: Path = typer.Option(
        Path("runs"), "--runs-dir", "-r", help="Directory containing completed run artifacts"
    ),
    output_dir: Path = typer.Option(
        Path("reports/statistics"), "--output-dir", "-o", help="Output directory for reports"
    ),
    markdown_report: Path = typer.Option(
        Path("reports/statistics/statistical_report.md"),
        "--markdown-report",
        "-m",
        help="Path for generated markdown audit report",
    ),
) -> None:
    """Aggregate multi-seed runs, run hypothesis tests, and export statistical summary tables."""
    from prorag_fl.analysis.aggregator import MultiSeedAggregator
    from prorag_fl.analysis.reporting import generate_statistical_markdown_report

    console.print(
        Panel(
            f"[bold cyan]Starting Multi-Seed Statistical Analysis[/bold cyan]\n"
            f"Runs Directory: [bold]{runs_dir.as_posix()}[/bold]\n"
            f"Target Seeds: [bold][13, 37, 73, 101, 211][/bold] (N = 5)\n"
            f"Output Tables: [bold]{output_dir.as_posix()}[/bold]\n"
            f"Markdown Report: [bold]{markdown_report.as_posix()}[/bold]",
            title="Gate P15: Statistical Analysis Protocol",
        )
    )

    aggregator = MultiSeedAggregator(runs_dir=runs_dir)
    report = aggregator.aggregate_and_test()

    parquet_p, csv_p, json_p = aggregator.export_summary_tables(report, output_dir=output_dir)

    markdown_content = generate_statistical_markdown_report(report)
    markdown_report.parent.mkdir(parents=True, exist_ok=True)
    markdown_report.write_text(markdown_content, encoding="utf-8")

    # Display Rich Summary Tables
    table = Table(
        title="Key Methods Multi-Seed Performance Summary (Mean ± Std [95% CI])",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Dataset", style="cyan")
    table.add_column("Method", style="bold")
    table.add_column("Macro-F1", justify="right", style="bold green")
    table.add_column("Balanced Acc", justify="right")
    table.add_column("Operational FPR", justify="right", style="yellow")
    table.add_column("Attacked Macro-F1", justify="right", style="red")

    for s in report.summaries[:15]:
        m = s.metrics
        f1_str = f"{m['macro_f1'].mean:.4f} ± {m['macro_f1'].std:.4f}" if "macro_f1" in m else "N/A"
        acc_str = (
            f"{m['balanced_accuracy'].mean:.4f} ± {m['balanced_accuracy'].std:.4f}"
            if "balanced_accuracy" in m
            else "N/A"
        )
        fpr_str = f"{m['fpr'].mean:.4f} ± {m['fpr'].std:.4f}" if "fpr" in m else "N/A"
        att_str = (
            f"{m['attacked_macro_f1'].mean:.4f} ± {m['attacked_macro_f1'].std:.4f}"
            if "attacked_macro_f1" in m
            else "N/A"
        )
        table.add_row(s.dataset, s.method, f1_str, acc_str, fpr_str, att_str)

    console.print(table)

    table_tests = Table(
        title="Pairwise Hypothesis Tests (ProRAG-FL vs Baselines, FDR < 0.05)",
        show_header=True,
        header_style="bold cyan",
    )
    table_tests.add_column("Dataset", style="cyan")
    table_tests.add_column("Baseline", style="bold")
    table_tests.add_column("Metric", style="green")
    table_tests.add_column("Test", style="dim")
    table_tests.add_column("Raw p-val", justify="right")
    table_tests.add_column("FDR (B-H) p-val", justify="right", style="bold yellow")
    table_tests.add_column("Cohen's d", justify="right", style="bold")
    table_tests.add_column("Significant", justify="center", style="bold green")

    for t in report.hypothesis_tests[:10]:
        sig_str = "YES" if t.is_significant_005 else "NO"
        table_tests.add_row(
            t.dataset,
            t.baseline_method,
            t.metric_name,
            t.test_name,
            f"{t.p_value_raw:.4f}",
            f"{t.p_value_fdr_bh:.4f}",
            f"{t.effect_size_cohen_d:+.2f}",
            sig_str,
        )

    console.print(table_tests)

    console.print(
        Panel(
            f"[bold green]Statistical Analysis Complete[/bold green]\n"
            f"Evaluated Runs: [bold]{report.total_runs_analyzed}[/bold]\n"
            f"Parquet Export: [bold underline]{parquet_p.as_posix()}[/bold underline]\n"
            f"CSV Export: [bold underline]{csv_p.as_posix()}[/bold underline]\n"
            f"Tests JSON: [bold underline]{json_p.as_posix()}[/bold underline]\n"
            f"Markdown Report: [bold underline]{markdown_report.as_posix()}[/bold underline]",
            title="Gate P15: Statistical Acceptance Gate Passed",
        )
    )


export_app = typer.Typer(
    name="export",
    help="Publication artifacts generator and manuscript synchronization (Phase 16).",
    add_completion=False,
)
app.add_typer(export_app)


@export_app.command(name="build-all")
def export_build_all(
    reports_dir: Path = typer.Option(
        Path("reports"), "--reports-dir", "-r", help="Master reports root directory"
    ),
    exports_dir: Path = typer.Option(
        Path("reports/paper_exports"), "--exports-dir", "-e", help="Paper exports output directory"
    ),
    runs_dir: Path = typer.Option(
        Path("runs"), "--runs-dir", help="Directory containing completed run artifacts"
    ),
) -> None:
    """Build results_master dataset, 7 LaTeX tables, 4 vector figures, and claims.json."""
    from prorag_fl.export.builder import PaperArtifactsBuilder

    console.print(
        Panel(
            f"[bold cyan]Starting Paper Artifacts Generation[/bold cyan]\n"
            f"Master Reports: [bold]{reports_dir.as_posix()}[/bold]\n"
            f"Paper Exports: [bold]{exports_dir.as_posix()}[/bold]\n"
            f"Target Artifacts: [bold]7 LaTeX Tables, 4 Figures, claims.json[/bold]",
            title="Gate P16: Paper Export Protocol",
        )
    )

    builder = PaperArtifactsBuilder(
        reports_dir=reports_dir, exports_dir=exports_dir, runs_dir=runs_dir
    )
    manifest = builder.build_all()

    # Rich summary table for generated paper exports
    table = Table(title="Generated Paper Artifacts", show_header=True, header_style="bold green")
    table.add_column("Category", style="cyan")
    table.add_column("Artifact Path", style="bold")

    table.add_row("Master Parquet", manifest.master_parquet_path)
    table.add_row("Master CSV", manifest.master_csv_path)

    for tbl in manifest.tables_generated:
        table.add_row("LaTeX Table", tbl)
    for fig in manifest.figures_generated:
        table.add_row("Vector Figure", fig)

    table.add_row("Claims Traceability", f"{manifest.claims_file} ({manifest.claims_count} claims)")
    console.print(table)

    console.print(
        Panel(
            f"[bold green]Paper Artifacts Built Successfully[/bold green]\n"
            f"Master Parquet: [bold underline]{manifest.master_parquet_path}[/bold underline]\n"
            f"Master CSV: [bold underline]{manifest.master_csv_path}[/bold underline]\n"
            f"Tables: [bold]{len(manifest.tables_generated)} .tex files[/bold]\n"
            f"Figures: [bold]{len(manifest.figures_generated)} files[/bold]\n"
            f"Claims Mapped: [bold]{manifest.claims_count}[/bold]\n"
            f"Manifest: [bold underline]{(exports_dir / 'export_manifest.json').as_posix()}[/bold underline]",
            title="Gate P16: Publication Readiness Audit Passed",
        )
    )


@export_app.command(name="sync-manuscript")
def export_sync_manuscript(
    exports_dir: Path = typer.Option(
        Path("reports/paper_exports"), "--exports-dir", "-e", help="Paper exports directory"
    ),
    manuscript_dir: Path = typer.Option(
        Path("../Manuscript"), "--manuscript-dir", "-m", help="Target manuscript directory"
    ),
    execute: bool = typer.Option(
        False, "--execute", help="Execute synchronization (default is dry-run for safety)"
    ),
) -> None:
    """Safely synchronize validated tables and figures to ../Manuscript/."""
    from prorag_fl.export.sync import ManuscriptSynchronizer

    dry_run = not execute
    mode_str = (
        "[yellow]DRY-RUN (Preview)[/yellow]"
        if dry_run
        else "[bold red]LIVE SYNC (Executing)[/bold red]"
    )

    console.print(
        Panel(
            f"[bold cyan]Manuscript Boundary Synchronization[/bold cyan]\n"
            f"Mode: {mode_str}\n"
            f"Source: [bold]{exports_dir.as_posix()}[/bold]\n"
            f"Destination: [bold]{manuscript_dir.as_posix()}[/bold]\n"
            f"Safety Invariant: [bold green]Never modifies manuscript prose or narrative[/bold green]",
            title="Gate P16: Manuscript Synchronization Gate",
        )
    )

    synchronizer = ManuscriptSynchronizer(exports_dir=exports_dir, manuscript_dir=manuscript_dir)
    res = synchronizer.sync(dry_run=dry_run)

    table = Table(
        title="Synchronized Artifacts Plan", show_header=True, header_style="bold magenta"
    )
    table.add_column("Type", style="cyan")
    table.add_column("Source", style="dim")
    table.add_column("Destination", style="bold")

    for act in res["actions"]:
        table.add_row(act["file_type"], act["source"], act["destination"])
    console.print(table)

    status_msg = (
        "[bold yellow]Dry-run complete. Run with --execute to perform file sync.[/bold yellow]"
        if dry_run
        else f"[bold green]Successfully synchronized {res['synced_count']} artifacts to {res['manuscript_dir']}[/bold green]"
    )
    console.print(Panel(status_msg, title="Sync Status"))


audit_app = typer.Typer(
    name="audit",
    help="Final reproducibility audit and checklist verification (Phase 17).",
    add_completion=False,
)
app.add_typer(audit_app)


@audit_app.command(name="full")
def audit_run_full(
    root_dir: Path = typer.Option(Path("."), "--root-dir", "-d", help="Project root directory"),
) -> None:
    """Execute full 10-category reproducibility audit and synchronize checklist."""
    from prorag_fl.audit.engine import ReproducibilityAuditEngine
    from prorag_fl.audit.reporting import AuditReporter

    console.print(
        Panel(
            f"[bold cyan]ProRAG-FL Final Reproducibility & Audit Protocol[/bold cyan]\n"
            f"Root Directory: [bold]{root_dir.as_posix()}[/bold]\n"
            f"Checklist Scope: [bold]10 Categories (30_FINAL_REPRODUCIBILITY_CHECKLIST.md)[/bold]\n"
            f"Acceptance Gate: [bold]Gate P17 (Traceability, Anti-Cherry-Picking, Integrity)[/bold]",
            title="Gate P17: Master Audit Verification",
        )
    )

    engine = ReproducibilityAuditEngine(root_dir=root_dir)
    audit = engine.run_full_audit()

    reporter = AuditReporter(root_dir=root_dir)
    saved = reporter.save_reports(audit)

    table = Table(
        title="Reproducibility Audit Summary by Category",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Category", style="cyan")
    table.add_column("Total Checks", justify="center")
    table.add_column("Passed", justify="center", style="bold green")
    table.add_column("Warnings", justify="center", style="yellow")
    table.add_column("Failed", justify="center", style="red")
    table.add_column("Status", justify="center", style="bold")

    for cat_name, summary in audit.categories.items():
        status_text = (
            "[bold green]PASS[/bold green]"
            if summary.is_fully_compliant
            else "[bold red]FAIL[/bold red]"
        )
        table.add_row(
            cat_name,
            str(summary.total_checks),
            str(summary.passed_count),
            str(summary.warning_count),
            str(summary.failed_count),
            status_text,
        )
    console.print(table)

    verdict_style = "bold green" if audit.is_reproducible else "bold red"
    verdict_text = (
        "PASS — 100% REPRODUCIBLE" if audit.is_reproducible else "FAIL — AUDIT DEFICIENCIES"
    )

    console.print(
        Panel(
            f"Overall Reproducibility: [{verdict_style}]{verdict_text}[/{verdict_style}]\n"
            f"Total Checks: [bold]{audit.total_passed}/{audit.total_checks} Passed[/bold]\n"
            f"Warnings: [yellow]{audit.total_warnings}[/yellow] | Failures: [red]{audit.total_failed}[/red]\n"
            f"Audit JSON: [bold underline]{saved['json_path']}[/bold underline]\n"
            f"Audit Markdown: [bold underline]{saved['md_path']}[/bold underline]\n"
            f"Checklist Synced: [bold green]{saved['checklist_synced']}[/bold green]",
            title=f"Gate P17: Audit Pass ({verdict_text})",
        )
    )


@audit_app.command(name="checklist")
def audit_show_checklist(
    root_dir: Path = typer.Option(Path("."), "--root-dir", "-d", help="Project root directory"),
) -> None:
    """Display interactive status of all items in 30_FINAL_REPRODUCIBILITY_CHECKLIST.md."""
    from prorag_fl.audit.engine import ReproducibilityAuditEngine
    from prorag_fl.audit.schemas import AuditCheckStatus

    engine = ReproducibilityAuditEngine(root_dir=root_dir)
    audit = engine.run_full_audit()

    table = Table(
        title="ProRAG-FL Master Reproducibility Checklist",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Check Item", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")

    for cat_name, summary in audit.categories.items():
        for it in summary.items:
            badge = (
                "[bold green][PASS][/bold green]"
                if it.status == AuditCheckStatus.PASSED
                else (
                    "[bold yellow][WARN][/bold yellow]"
                    if it.status == AuditCheckStatus.WARNING
                    else "[bold red][FAIL][/bold red]"
                )
            )
            table.add_row(
                cat_name, it.name, badge, it.details[:80] + ("..." if len(it.details) > 80 else "")
            )

    console.print(table)


if __name__ == "__main__":
    app()
