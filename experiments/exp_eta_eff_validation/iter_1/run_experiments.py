from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

THIS_DIR = Path(__file__).resolve().parent
SRC_DIR = THIS_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from exp_eta_eff_validation.analysis import generate_all_tables  # noqa: E402
from exp_eta_eff_validation.core import ensure_directories, generate_all_datasets, load_config, write_json  # noqa: E402
from exp_eta_eff_validation.plotting import create_figures  # noqa: E402
from exp_eta_eff_validation.sympy_checks import run_sympy_validation  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    workspace_root = Path(__file__).resolve().parents[3]
    config = load_config(workspace_root / args.config)
    paths = ensure_directories(config, workspace_root)

    sympy_report = paths["output_dir"] / "sympy_validation_report.md"
    sympy_checks = run_sympy_validation(sympy_report)
    frames = generate_all_datasets(paths["data_dir"])
    table_names, metrics = generate_all_tables(frames, paths["tables_dir"])
    figure_names = create_figures(frames, paths["figures_dir"], paths["verification_dir"])

    manifest = {
        "config_path": args.config,
        "output_dir": str(paths["output_dir"].relative_to(workspace_root)),
        "sympy_report": str(sympy_report.relative_to(workspace_root)),
        "datasets": sorted(str(path.relative_to(workspace_root)) for path in paths["data_dir"].glob("*.csv")),
        "tables": sorted(str(path.relative_to(workspace_root)) for path in paths["tables_dir"].glob("*.md")),
        "figures": sorted(str(path.relative_to(workspace_root)) for path in paths["figures_dir"].glob("*.pdf")),
        "verification_rasters": sorted(str(path.relative_to(workspace_root)) for path in paths["verification_dir"].glob("*.png")),
        "table_names": table_names,
        "figure_names": figure_names,
        "metrics": metrics,
        "sympy_checks": sympy_checks,
    }
    results_summary = {
        "figures": manifest["figures"],
        "tables": manifest["tables"],
        "datasets": manifest["datasets"],
        "sympy_report": manifest["sympy_report"],
        "metrics": metrics,
        "notes": [
            "This run executed the full six-experiment surrogate matrix from experiment_design.",
            "Figure PDFs were rasterized with PyMuPDF to verify readability.",
        ],
    }

    write_json(paths["output_dir"] / "outputs_manifest.json", manifest)
    write_json(paths["output_dir"] / "results_summary.json", results_summary)
    print(json.dumps({"status": "ok", "manifest": manifest["output_dir"]}))


if __name__ == "__main__":
    main()
