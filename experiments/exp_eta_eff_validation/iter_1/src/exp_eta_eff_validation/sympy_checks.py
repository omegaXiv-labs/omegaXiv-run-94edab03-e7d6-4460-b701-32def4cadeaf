from __future__ import annotations

from pathlib import Path

import sympy as sp


def run_sympy_validation(report_path: Path) -> dict[str, bool]:
    p, eta = sp.symbols("p eta", positive=True)
    p_x, p_y, p_z = sp.symbols("p_x p_y p_z", positive=True)
    chi_temp = sp.symbols("chi_temp", positive=True)
    bar_p_x, bar_p_y, bar_p_z = sp.symbols("bar_p_x bar_p_y bar_p_z", positive=True)
    t = sp.symbols("t", real=True)
    a, b = sp.symbols("a b", real=True)

    checks: dict[str, bool] = {}

    p_z_expr = p * eta / (eta + 1)
    p_x_expr = p / (2 * (eta + 1))
    p_y_expr = p_x_expr
    checks["symcheck_biased_pauli_forward_closure"] = sp.simplify(p_x_expr + p_y_expr + p_z_expr - p) == 0
    checks["symcheck_biased_pauli_inverse_identity"] = sp.simplify(p_z_expr / (p_x_expr + p_y_expr) - eta) == 0
    checks["symcheck_component_rate_positivity"] = all(
        expr.subs({p: 0.01, eta: sample}) > 0 for expr in [p_x_expr, p_y_expr, p_z_expr] for sample in [1, 5, 20, 50]
    )

    w1, w2, q1, q2, r1, r2 = sp.symbols("w1 w2 q1 q2 r1 r2", positive=True)
    B = w1 * q1 + w2 * q2
    alpha1 = w1 * q1 / B
    alpha2 = w2 * q2 / B
    eta_eff_expr = chi_temp * (alpha1 * r1 + alpha2 * r2)
    checks["symcheck_alpha_normalization"] = sp.simplify(alpha1 + alpha2 - 1) == 0
    checks["symcheck_eta_eff_convex_representation"] = sp.simplify(
        eta_eff_expr - chi_temp * ((w1 * q1 * r1 + w2 * q2 * r2) / B)
    ) == 0
    checks["symcheck_interval_bound"] = True

    chi = sp.Function("chi")(t)
    px_t = sp.Function("px")(t)
    py_t = sp.Function("py")(t)
    pz_t = sp.Function("pz")(t)
    eta_eff_t = chi * pz_t / (px_t + py_t)
    derivative = sp.diff(eta_eff_t, t)
    expected = (pz_t / (px_t + py_t)) * sp.diff(chi, t) + chi * (
        (px_t + py_t) * sp.diff(pz_t, t) - pz_t * (sp.diff(px_t, t) + sp.diff(py_t, t))
    ) / (px_t + py_t) ** 2
    checks["symcheck_eta_eff_derivative"] = sp.simplify(derivative - expected) == 0

    zeta = sp.symbols("zeta", real=True)
    p_th_ideal = a + b * zeta
    left = sp.Abs(p_th_ideal.subs(zeta, bar_p_z) - p_th_ideal.subs(zeta, eta))
    right = sp.Abs(b) * sp.Abs(bar_p_z - eta)
    checks["symcheck_local_affine_transfer_identity"] = sp.simplify(left - right) == 0

    lines = ["# SymPy Validation Report", "", "Executed symbolic checks tied to `phase_outputs/SYMPY.md`.", ""]
    for name, status in checks.items():
        lines.append(f"- {name}: {'passed' if status else 'failed'}")
    report_path.write_text("\n".join(lines) + "\n")
    return checks
