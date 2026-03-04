# Effective-Bias Validation Experiments

This package implements the validation and experimentation phase for the selected
`path_effective_bias_renormalization` track while preserving the six-experiment
matrix from `phase_outputs/experiment_design.json`.

## Goal

Produce a reproducible, iteration-safe surrogate benchmark suite that:

- executes all six planned experiments,
- materializes the declared datasets, figures, and tables,
- runs SymPy checks linked to `phase_outputs/SYMPY.md`,
- writes artifacts into `paper/figures/iter_1`, `paper/tables/iter_1`, and
  `paper/data/iter_1`, and
- records a machine-readable manifest for downstream phase reporting.

The current workspace does not include Stim, Qiskit Aer, or a reusable external
biased-noise repository checkout. To keep the phase executable, the package uses a
literature-grounded surrogate generator whose equations are tied to the selected
hypothesis formalism:

- biased-Pauli closure from `derive_math_methodology`,
- convex-mixture decomposition of `eta_eff`,
- schedule sensitivity and transfer-bound checks,
- finite-size correction and penalty decomposition,
- cross-simulator parity with first- and second-order translations,
- boundary-fragility interaction modeling.

## Layout

- `configs/validation_config.json`: experiment definitions and output paths
- `src/exp_eta_eff_validation/core.py`: synthetic data generation and I/O helpers
- `src/exp_eta_eff_validation/analysis.py`: metric computation and table writing
- `src/exp_eta_eff_validation/plotting.py`: PDF figure generation and readability checks
- `src/exp_eta_eff_validation/sympy_checks.py`: symbolic validations and report writing
- `run_experiments.py`: thin CLI entrypoint
- `tests/test_surrogate_experiment.py`: formula and smoke tests

## Reproducibility

- Seeds are fixed to `11, 29, 47, 71, 89` across all experiments.
- The generated datasets are deterministic for the same config and seed set.
- The run manifest captures artifact paths and summary metrics.

## Commands

Create or reuse the workspace venv:

```bash
uv venv experiments/.venv
uv pip install --python experiments/.venv/bin/python numpy pandas matplotlib seaborn sympy scipy pytest ruff pymupdf
```

Run the experiments:

```bash
experiments/.venv/bin/python experiments/exp_eta_eff_validation/iter_1/run_experiments.py --config experiments/exp_eta_eff_validation/iter_1/configs/validation_config.json
```

Run lint:

```bash
experiments/.venv/bin/ruff check experiments/exp_eta_eff_validation/iter_1/src experiments/exp_eta_eff_validation/iter_1/tests experiments/exp_eta_eff_validation/iter_1/run_experiments.py
```

Run tests:

```bash
experiments/.venv/bin/pytest experiments/exp_eta_eff_validation/iter_1/tests -q
```

## Outputs

- `experiments/exp_eta_eff_validation/iter_1/outputs_manifest.json`
- `experiments/exp_eta_eff_validation/iter_1/results_summary.json`
- `experiments/exp_eta_eff_validation/iter_1/sympy_validation_report.md`
- datasets under `paper/data/iter_1`
- tables under `paper/tables/iter_1`
- figures under `paper/figures/iter_1`

## Limitations

This iteration uses a surrogate benchmark rather than direct Stim or Qiskit Aer
execution because those simulator stacks are not present in the workspace. The
generated artifacts are therefore validation scaffolding tied to the formal
hypotheses, not final physics claims.

## Revision Fixes Applied

The latest refinement guidance is now encoded in both the manuscript and this
experiment package:

- The primary `eta_eff` claim is treated as a conditional first-order result,
  valid when boundary fragility and backend semantic mismatch remain bounded.
- Threshold reporting is paired with a backend-semantic confidence band derived
  from matched backend disagreement (`threshold_absolute_gap` and
  `agreement_rate_within_tolerance`) rather than reported as a single
  unconditional scalar.
- Direct-backend reruns must preserve the iter_1 artifact schema (dataset,
  figure, and table paths plus summary metrics) so surrogate-to-direct deltas
  are attributable to backend semantics instead of report drift.
