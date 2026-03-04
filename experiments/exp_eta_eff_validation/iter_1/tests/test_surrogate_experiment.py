from __future__ import annotations

from pathlib import Path
import sys

THIS_DIR = Path(__file__).resolve().parent
SRC_DIR = THIS_DIR.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from exp_eta_eff_validation.core import biased_pauli_components, eta_effective_from_budget  # noqa: E402
from exp_eta_eff_validation.sympy_checks import run_sympy_validation  # noqa: E402


def test_biased_pauli_closure() -> None:
    p_x, p_y, p_z = biased_pauli_components(0.01, 5)
    assert abs((p_x + p_y + p_z) - 0.01) < 1e-12
    assert abs(p_z / (p_x + p_y) - 5.0) < 1e-12


def test_eta_effective_positive() -> None:
    records = [
        {"weight": 0.4, "p_x": 0.001, "p_y": 0.001, "p_z": 0.008},
        {"weight": 0.6, "p_x": 0.0008, "p_y": 0.0008, "p_z": 0.006},
    ]
    _, _, _, eta_eff = eta_effective_from_budget(records, 0.9)
    assert eta_eff > 0


def test_sympy_validation_report(tmp_path: Path) -> None:
    report_path = tmp_path / "report.md"
    checks = run_sympy_validation(report_path)
    assert report_path.exists()
    assert all(checks.values())
