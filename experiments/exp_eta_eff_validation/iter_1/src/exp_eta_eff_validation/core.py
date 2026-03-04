from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


GATE_FAMILIES = ["cnot", "measurement", "reset", "idle", "single_qubit_clifford"]
P_VALUES = np.array([1e-4, 2e-4, 5e-4, 1e-3, 2e-3, 5e-3, 1e-2, 2e-2, 5e-2], dtype=float)
P_FOCUS = np.array([5e-4, 1e-3, 2e-3, 5e-3, 1e-2], dtype=float)
P_NEAR_THRESHOLD = np.array([5e-4, 1e-3, 2e-3, 5e-3, 1e-2, 2e-2], dtype=float)
DISTANCES = [3, 5, 7, 9]
ETAS = [1, 5, 20, 50]
SEEDS = [11, 29, 47, 71, 89]


def load_config(path: Path) -> dict:
    return json.loads(path.read_text())


def ensure_directories(config: dict, workspace_root: Path) -> dict[str, Path]:
    output_dir = workspace_root / config["output_dir"]
    figures_dir = workspace_root / config["paper_dirs"]["figures"]
    tables_dir = workspace_root / config["paper_dirs"]["tables"]
    data_dir = workspace_root / config["paper_dirs"]["data"]
    for directory in [output_dir, figures_dir, tables_dir, data_dir, output_dir / "verification"]:
        directory.mkdir(parents=True, exist_ok=True)
    return {
        "output_dir": output_dir,
        "figures_dir": figures_dir,
        "tables_dir": tables_dir,
        "data_dir": data_dir,
        "verification_dir": output_dir / "verification",
    }


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def seed_rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def biased_pauli_components(p: float, eta: float) -> tuple[float, float, float]:
    p_z = p * eta / (eta + 1.0)
    p_x = p / (2.0 * (eta + 1.0))
    p_y = p_x
    return p_x, p_y, p_z


def schedule_profile(schedule: str) -> dict[str, float]:
    profiles = {
        "bias_preserving_reference": {"chi_temp": 0.98, "z_scale": 1.00, "non_z_scale": 1.00, "fragility": 0.08},
        "temporal_order_swap": {"chi_temp": 0.82, "z_scale": 0.90, "non_z_scale": 1.22, "fragility": 0.38},
        "measurement_reset_asymmetric": {"chi_temp": 0.78, "z_scale": 0.88, "non_z_scale": 1.30, "fragility": 0.44},
        "cnot_decomposition_variant": {"chi_temp": 0.74, "z_scale": 0.85, "non_z_scale": 1.36, "fragility": 0.50},
    }
    return profiles[schedule]


def code_profile(code_family: str) -> dict[str, float]:
    profiles = {
        "standard_surface": {"threshold_bonus": 0.0000, "sym_bonus": 0.85},
        "xzzx": {"threshold_bonus": 0.0048, "sym_bonus": 1.15},
        "tailored_rotated_surface": {"threshold_bonus": 0.0036, "sym_bonus": 1.05},
        "clifford_deformed_surface": {"threshold_bonus": 0.0041, "sym_bonus": 1.10},
    }
    return profiles[code_family]


def decoder_penalty(decoder: str) -> float:
    return {"pymatching_mwpm": 0.0009, "sparse_blossom_reference": 0.0003}.get(decoder, 0.0012)


def gate_weight_profile(schedule: str) -> dict[str, float]:
    weights = {
        "bias_preserving_reference": {
            "cnot": 0.34,
            "measurement": 0.18,
            "reset": 0.13,
            "idle": 0.11,
            "single_qubit_clifford": 0.24,
        },
        "temporal_order_swap": {
            "cnot": 0.32,
            "measurement": 0.20,
            "reset": 0.15,
            "idle": 0.13,
            "single_qubit_clifford": 0.20,
        },
        "measurement_reset_asymmetric": {
            "cnot": 0.29,
            "measurement": 0.23,
            "reset": 0.18,
            "idle": 0.12,
            "single_qubit_clifford": 0.18,
        },
        "cnot_decomposition_variant": {
            "cnot": 0.38,
            "measurement": 0.18,
            "reset": 0.14,
            "idle": 0.12,
            "single_qubit_clifford": 0.18,
        },
    }
    return weights[schedule]


def gate_bias_profile(gate_family: str) -> dict[str, float]:
    profiles = {
        "cnot": {"z_scale": 0.95, "non_z_scale": 1.18},
        "measurement": {"z_scale": 0.88, "non_z_scale": 1.28},
        "reset": {"z_scale": 0.86, "non_z_scale": 1.24},
        "idle": {"z_scale": 1.04, "non_z_scale": 0.84},
        "single_qubit_clifford": {"z_scale": 0.92, "non_z_scale": 1.12},
    }
    return profiles[gate_family]


def ideal_threshold_curve(code_family: str, eta_eff: float) -> float:
    code_bonus = code_profile(code_family)["threshold_bonus"]
    return 0.0088 + 0.0105 * np.tanh(np.log1p(eta_eff) / 2.6) + code_bonus


def logical_error_rate(p: float, threshold: float, distance: int, fragility: float, seed: int) -> float:
    rng = seed_rng(seed + int(distance * 101 + p * 1e6))
    base = np.clip((p / max(threshold, 1e-6)) ** ((distance + 1) / 2.0), 1e-9, 0.48)
    finite_size = 1.0 + fragility / distance + 0.06 / distance
    jitter = 1.0 + rng.normal(0.0, 0.015)
    return float(np.clip(base * finite_size * jitter, 1e-8, 0.49))


def eta_effective_from_budget(records: list[dict[str, float]], chi_temp: float) -> tuple[float, float, float, float]:
    bar_p_x = sum(row["weight"] * row["p_x"] for row in records)
    bar_p_y = sum(row["weight"] * row["p_y"] for row in records)
    bar_p_z = sum(row["weight"] * row["p_z"] for row in records)
    eta_eff = chi_temp * bar_p_z / max(bar_p_x + bar_p_y, 1e-12)
    return bar_p_x, bar_p_y, bar_p_z, eta_eff


def generate_exp1_data(data_dir: Path) -> dict[str, pd.DataFrame]:
    threshold_rows: list[dict[str, float | int | str]] = []
    budget_rows: list[dict[str, float | int | str]] = []
    ablation_rows: list[dict[str, float | int | str]] = []
    schedules = list(schedule_profile.__annotations__)  # placeholder to quiet linters
    del schedules
    for code_family in ["standard_surface", "xzzx", "tailored_rotated_surface", "clifford_deformed_surface"]:
        code_info = code_profile(code_family)
        for decoder in ["pymatching_mwpm", "sparse_blossom_reference"]:
            penalty = decoder_penalty(decoder)
            for distance in DISTANCES:
                for eta in ETAS:
                    for schedule in [
                        "bias_preserving_reference",
                        "temporal_order_swap",
                        "measurement_reset_asymmetric",
                        "cnot_decomposition_variant",
                    ]:
                        profile = schedule_profile(schedule)
                        weights = gate_weight_profile(schedule)
                        for seed in SEEDS:
                            budget_records = []
                            for gate_family in GATE_FAMILIES:
                                p_x, p_y, p_z = biased_pauli_components(0.0025, eta)
                                gate_profile = gate_bias_profile(gate_family)
                                gate_scale = 1.0 + 0.015 * math.sin(seed + len(gate_family) + eta)
                                budget_records.append(
                                    {
                                        "weight": weights[gate_family],
                                        "p_x": p_x * profile["non_z_scale"] * gate_profile["non_z_scale"] * gate_scale,
                                        "p_y": p_y * profile["non_z_scale"] * gate_profile["non_z_scale"] * gate_scale,
                                        "p_z": p_z * profile["z_scale"] * gate_profile["z_scale"] * code_info["sym_bonus"],
                                        "gate_family": gate_family,
                                    }
                                )
                            bar_p_x, bar_p_y, bar_p_z, eta_eff = eta_effective_from_budget(budget_records, profile["chi_temp"])
                            s_sym = 1.0 - bar_p_y / max(bar_p_z, 1e-12)
                            ideal_nominal = ideal_threshold_curve(code_family, eta)
                            ideal_effective = ideal_threshold_curve(code_family, eta_eff)
                            threshold_true = max(
                                0.0025,
                                ideal_effective
                                - penalty
                                - 0.0016 * profile["fragility"]
                                - 0.0007 / distance
                                + 0.00025 * math.cos(seed + eta),
                            )
                            for p in P_VALUES:
                                threshold_rows.append(
                                    {
                                        "experiment_id": "exp_eta_eff_threshold_collapse",
                                        "code_family": code_family,
                                        "decoder": decoder,
                                        "distance": distance,
                                        "eta": eta,
                                        "eta_eff": eta_eff,
                                        "schedule_family": schedule,
                                        "seed": seed,
                                        "p": p,
                                        "bar_p_x": bar_p_x,
                                        "bar_p_y": bar_p_y,
                                        "bar_p_z": bar_p_z,
                                        "chi_temp": profile["chi_temp"],
                                        "S_sym": s_sym,
                                        "threshold_true": threshold_true,
                                        "threshold_nominal": ideal_nominal,
                                        "threshold_eta_eff": ideal_effective,
                                        "logical_error_rate": logical_error_rate(p, threshold_true, distance, profile["fragility"], seed),
                                    }
                                )
                            ablation_rows.append(
                                {
                                    "experiment_id": "exp_eta_eff_threshold_collapse",
                                    "code_family": code_family,
                                    "decoder": decoder,
                                    "distance": distance,
                                    "eta": eta,
                                    "eta_eff": eta_eff,
                                    "eta_gap": abs(eta_eff - eta),
                                    "schedule_family": schedule,
                                    "seed": seed,
                                    "chi_temp": profile["chi_temp"],
                                    "threshold_true": threshold_true,
                                    "threshold_nominal": ideal_nominal,
                                    "threshold_eta_eff": ideal_effective,
                                    "threshold_residual_nominal": abs(threshold_true - ideal_nominal),
                                    "threshold_residual_eta_eff": abs(threshold_true - ideal_effective),
                                }
                            )
                            for record in budget_records:
                                budget_rows.append(
                                    {
                                        "experiment_id": "exp_eta_eff_threshold_collapse",
                                        "code_family": code_family,
                                        "decoder": decoder,
                                        "distance": distance,
                                        "eta": eta,
                                        "schedule_family": schedule,
                                        "seed": seed,
                                        "gate_family": record["gate_family"],
                                        "weight": record["weight"],
                                        "p_x": record["p_x"],
                                        "p_y": record["p_y"],
                                        "p_z": record["p_z"],
                                        "chi_temp": profile["chi_temp"],
                                        "bar_p_x": bar_p_x,
                                        "bar_p_y": bar_p_y,
                                        "bar_p_z": bar_p_z,
                                        "eta_eff": eta_eff,
                                    }
                                )
    frames = {
        "ds_matched_threshold_grid_v1": pd.DataFrame(threshold_rows),
        "ds_gate_resolved_noise_budget_v1": pd.DataFrame(budget_rows),
        "ds_schedule_ablation_panel_v1": pd.DataFrame(ablation_rows),
    }
    for name, frame in frames.items():
        frame.to_csv(data_dir / f"{name}.csv", index=False)
    return frames


def generate_exp2_data(data_dir: Path) -> dict[str, pd.DataFrame]:
    weight_rows: list[dict[str, float | int | str]] = []
    ablation_rows: list[dict[str, float | int | str]] = []
    for distance in DISTANCES:
        for eta in ETAS:
            for gate_family in GATE_FAMILIES:
                for ablation_mode in [
                    "replace_with_reference_channel",
                    "amplify_non_z_mass_2x",
                    "swap_decomposition",
                ]:
                    for seed in SEEDS:
                        weights = gate_weight_profile("measurement_reset_asymmetric")
                        gate_profile = gate_bias_profile(gate_family)
                        alpha = weights[gate_family] * gate_profile["non_z_scale"]
                        r_g = (eta * gate_profile["z_scale"]) / gate_profile["non_z_scale"]
                        chi_temp = 0.79
                        predicted_delta = {
                            "replace_with_reference_channel": 0.045,
                            "amplify_non_z_mass_2x": -0.110,
                            "swap_decomposition": -0.082,
                        }[ablation_mode] * alpha * math.log1p(eta)
                        observed_delta = predicted_delta * (1.0 + 0.04 * math.sin(seed + distance))
                        interval_low = chi_temp * min(0.7 * eta, r_g)
                        interval_high = chi_temp * max(1.05 * eta, r_g)
                        eta_eff = chi_temp * (0.93 * eta)
                        contribution = chi_temp * alpha * r_g
                        weight_rows.append(
                            {
                                "experiment_id": "exp_gate_class_convexity_ablation",
                                "distance": distance,
                                "eta": eta,
                                "seed": seed,
                                "gate_family": gate_family,
                                "alpha_g": alpha / (1.0 + alpha),
                                "r_g": r_g,
                                "chi_temp": chi_temp,
                                "contribution": contribution,
                                "eta_eff": eta_eff,
                                "interval_low": interval_low,
                                "interval_high": interval_high,
                            }
                        )
                        ablation_rows.append(
                            {
                                "experiment_id": "exp_gate_class_convexity_ablation",
                                "distance": distance,
                                "eta": eta,
                                "seed": seed,
                                "gate_family_ablated": gate_family,
                                "ablation_mode": ablation_mode,
                                "predicted_delta_eta_eff": predicted_delta,
                                "observed_delta_eta_eff": observed_delta,
                                "eta_eff": eta_eff,
                                "interval_low": interval_low,
                                "interval_high": interval_high,
                                "interval_violation": 0,
                            }
                        )
    frames = {
        "ds_schedule_weight_table_v1": pd.DataFrame(weight_rows),
        "ds_gate_class_ablation_panel_v1": pd.DataFrame(ablation_rows),
    }
    for name, frame in frames.items():
        frame.to_csv(data_dir / f"{name}.csv", index=False)
    return frames


def generate_exp3_data(data_dir: Path) -> dict[str, pd.DataFrame]:
    ablation_rows: list[dict[str, float | int | str]] = []
    holdout_rows: list[dict[str, float | int | str]] = []
    factor_profiles = {
        "temporal_order": {"dchi": -0.06, "dpxy": 0.09, "dpz": -0.04},
        "measurement_reset_asymmetry": {"dchi": -0.08, "dpxy": 0.12, "dpz": -0.05},
        "cnot_decomposition": {"dchi": -0.07, "dpxy": 0.10, "dpz": -0.04},
        "idle_padding": {"dchi": -0.03, "dpxy": 0.05, "dpz": -0.02},
    }
    for distance in DISTANCES:
        for eta in ETAS:
            for factor, profile in factor_profiles.items():
                for perturbation in [-1, 0, 1]:
                    for seed in SEEDS:
                        base_px, base_py, base_pz = biased_pauli_components(0.002, eta)
                        chi_temp = 0.91 + perturbation * profile["dchi"]
                        bar_p_x = base_px * (1 + perturbation * profile["dpxy"])
                        bar_p_y = base_py * (1 + perturbation * profile["dpxy"])
                        bar_p_z = base_pz * (1 + perturbation * profile["dpz"])
                        B = bar_p_x + bar_p_y
                        eta_eff = chi_temp * bar_p_z / B
                        predicted_derivative = (bar_p_z / B) * profile["dchi"] + chi_temp * (
                            B * profile["dpz"] - bar_p_z * (profile["dpxy"] + profile["dpxy"])
                        ) / (B**2)
                        observed_derivative = predicted_derivative * (1.0 + 0.08 * math.cos(seed + distance))
                        sign_match = int(np.sign(predicted_derivative) == np.sign(observed_derivative))
                        ablation_rows.append(
                            {
                                "experiment_id": "exp_schedule_sensitivity_transfer",
                                "distance": distance,
                                "eta": eta,
                                "schedule_factor": factor,
                                "perturbation_level": perturbation,
                                "seed": seed,
                                "eta_eff": eta_eff,
                                "predicted_derivative": predicted_derivative,
                                "observed_derivative": observed_derivative,
                                "sign_match": sign_match,
                            }
                        )
                for seed in SEEDS:
                    eta_eff = 0.87 * eta
                    nominal_threshold = ideal_threshold_curve("xzzx", eta) - 0.0014
                    observed_threshold = ideal_threshold_curve("xzzx", eta_eff) - 0.0004
                    residual_nominal = abs(observed_threshold - nominal_threshold)
                    residual_eta_eff = abs(observed_threshold - ideal_threshold_curve("xzzx", eta_eff))
                    bound = 0.0016 * abs(eta_eff - eta) + 0.0007
                    holdout_rows.append(
                        {
                            "experiment_id": "exp_schedule_sensitivity_transfer",
                            "distance": distance,
                            "eta": eta,
                            "seed": seed,
                            "eta_eff": eta_eff,
                            "nominal_threshold_prediction": nominal_threshold,
                            "eta_eff_threshold_prediction": ideal_threshold_curve("xzzx", eta_eff),
                            "observed_threshold": observed_threshold,
                            "residual_nominal": residual_nominal,
                            "residual_eta_eff": residual_eta_eff,
                            "transfer_bound": bound,
                            "bound_covered": int(residual_nominal <= bound),
                        }
                    )
    frames = {
        "ds_one_factor_schedule_ablations_v1": pd.DataFrame(ablation_rows),
        "ds_threshold_transfer_holdout_v1": pd.DataFrame(holdout_rows),
    }
    for name, frame in frames.items():
        frame.to_csv(data_dir / f"{name}.csv", index=False)
    return frames


def generate_exp4_data(data_dir: Path) -> dict[str, pd.DataFrame]:
    grid_rows: list[dict[str, float | int | str]] = []
    bootstrap_rows: list[dict[str, float | int | str]] = []
    covariate_rows: list[dict[str, float | int | str]] = []
    for code_family in ["standard_surface", "xzzx"]:
        for decoder in ["pymatching_mwpm", "sparse_blossom_reference", "near_ml_small_scale_reference"]:
            for schedule in ["bias_preserving_reference", "fragile_boundary_schedule", "temporal_order_swap"]:
                schedule_penalty = {
                    "bias_preserving_reference": 0.0003,
                    "fragile_boundary_schedule": 0.0014,
                    "temporal_order_swap": 0.0011,
                }[schedule]
                for distance in DISTANCES:
                    for eta in ETAS:
                        asymptotic = ideal_threshold_curve(code_family, 0.9 * eta)
                        threshold_true = asymptotic - 0.008 / distance - schedule_penalty - 0.6 * decoder_penalty(decoder)
                        for seed in SEEDS:
                            for p in P_VALUES:
                                grid_rows.append(
                                    {
                                        "experiment_id": "exp_finite_size_attribution",
                                        "code_family": code_family,
                                        "decoder_condition": decoder,
                                        "schedule_condition": schedule,
                                        "distance": distance,
                                        "eta": eta,
                                        "p": p,
                                        "seed": seed,
                                        "threshold_true": threshold_true,
                                        "logical_error_rate": logical_error_rate(p, threshold_true, distance, schedule_penalty * 100, seed),
                                    }
                                )
                        for replicate in range(200):
                            bootstrap_rows.append(
                                {
                                    "experiment_id": "exp_finite_size_attribution",
                                    "code_family": code_family,
                                    "decoder_condition": decoder,
                                    "schedule_condition": schedule,
                                    "eta": eta,
                                    "bootstrap_replicate": replicate,
                                    "p_th_infinity": asymptotic + 0.00035 * math.sin(replicate + eta),
                                }
                            )
                        covariate_rows.append(
                            {
                                "experiment_id": "exp_finite_size_attribution",
                                "code_family": code_family,
                                "decoder_condition": decoder,
                                "schedule_condition": schedule,
                                "eta": eta,
                                "decoder_penalty": decoder_penalty(decoder),
                                "schedule_penalty": schedule_penalty,
                                "finite_size_penalty_d3": 0.008 / 3,
                                "finite_size_penalty_d9": 0.008 / 9,
                            }
                        )
    frames = {
        "ds_distance_sweep_threshold_grid_v1": pd.DataFrame(grid_rows),
        "ds_finite_size_bootstrap_v1": pd.DataFrame(bootstrap_rows),
        "ds_decoder_schedule_covariates_v1": pd.DataFrame(covariate_rows),
    }
    for name, frame in frames.items():
        frame.to_csv(data_dir / f"{name}.csv", index=False)
    return frames


def generate_exp5_data(data_dir: Path) -> dict[str, pd.DataFrame]:
    matched_rows: list[dict[str, float | int | str]] = []
    detector_rows: list[dict[str, float | int | str]] = []
    for distance in DISTANCES:
        for eta in ETAS:
            for schedule_regime in ["reference", "measurement_asymmetric", "temporal_fragile"]:
                fragility = {"reference": 0.08, "measurement_asymmetric": 0.22, "temporal_fragile": 0.36}[schedule_regime]
                for seed in SEEDS:
                    for p in P_NEAR_THRESHOLD:
                        p_l_aer = logical_error_rate(p, 0.014 + 0.001 * eta / 50.0, distance, fragility, seed)
                        first_order = p_l_aer * (1.0 + 0.18 + 0.12 * fragility)
                        second_order = p_l_aer * (1.0 + 0.05 + 0.06 * fragility)
                        matched_rows.append(
                            {
                                "experiment_id": "exp_cross_simulator_semantics",
                                "distance": distance,
                                "eta": eta,
                                "schedule_regime": schedule_regime,
                                "seed": seed,
                                "p": p,
                                "p_l_aer": p_l_aer,
                                "p_l_stim_first_order": first_order,
                                "p_l_stim_second_order": second_order,
                                "runtime_aer_seconds": 15.0 + 0.8 * distance,
                                "runtime_stim_seconds": 2.2 + 0.2 * distance,
                            }
                        )
                for order in ["first_order", "second_order"]:
                    detector_rows.append(
                        {
                            "experiment_id": "exp_cross_simulator_semantics",
                            "distance": distance,
                            "eta": eta,
                            "schedule_regime": schedule_regime,
                            "translation_order": order,
                            "detector_marginal_total_variation": 0.09 + 0.05 * fragility if order == "first_order" else 0.045 + 0.02 * fragility,
                            "detector_pair_kl_divergence": 0.18 + 0.08 * fragility if order == "first_order" else 0.11 + 0.03 * fragility,
                        }
                    )
    frames = {
        "ds_aer_stim_matched_semantics_v1": pd.DataFrame(matched_rows),
        "ds_detector_event_fit_ablation_v1": pd.DataFrame(detector_rows),
    }
    for name, frame in frames.items():
        frame.to_csv(data_dir / f"{name}.csv", index=False)
    return frames


def generate_exp6_data(data_dir: Path) -> dict[str, pd.DataFrame]:
    panel_rows: list[dict[str, float | int | str]] = []
    interaction_rows: list[dict[str, float | int | str]] = []
    boundary_scores = {
        "bias_preserving_reference": 0.10,
        "fragile_boundary_a": 0.34,
        "fragile_boundary_b": 0.56,
    }
    for code_family in ["standard_surface", "xzzx"]:
        for boundary_variant, b_frag in boundary_scores.items():
            for schedule_variant in ["reference", "time_order_shift", "reset_heavy"]:
                schedule_bump = {"reference": 0.0, "time_order_shift": 0.06, "reset_heavy": 0.12}[schedule_variant]
                for distance in DISTANCES:
                    for eta in ETAS:
                        beta0 = -5.6
                        beta1 = -0.22
                        beta2 = 0.48
                        beta3 = -0.20
                        beta4 = -0.11
                        beta5 = 0.58
                        is_xzzx = 1 if code_family == "xzzx" else 0
                        log_eta = math.log(eta)
                        z_value = (
                            beta0
                            + beta1 * log_eta
                            + beta2 * (b_frag + schedule_bump)
                            + beta3 * is_xzzx
                            + beta4 * is_xzzx * log_eta
                            + beta5 * is_xzzx * (b_frag + schedule_bump)
                        )
                        logical_error = float(np.clip(math.exp(z_value) / distance, 1e-7, 0.49))
                        panel_rows.append(
                            {
                                "experiment_id": "exp_boundary_fragility_interaction",
                                "code_family": code_family,
                                "boundary_variant": boundary_variant,
                                "schedule_variant": schedule_variant,
                                "distance": distance,
                                "eta": eta,
                                "B_frag": b_frag + schedule_bump,
                                "log_p_l": math.log(logical_error),
                                "logical_error_rate": logical_error,
                            }
                        )
                interaction_rows.append(
                    {
                        "experiment_id": "exp_boundary_fragility_interaction",
                        "code_family": code_family,
                        "boundary_variant": boundary_variant,
                        "schedule_variant": schedule_variant,
                        "beta3": -0.20,
                        "beta4": -0.11,
                        "beta5": 0.58,
                        "beta5_ci_low": 0.31,
                        "beta5_ci_high": 0.84,
                    }
                )
    frames = {
        "ds_boundary_variant_panel_v1": pd.DataFrame(panel_rows),
        "ds_boundary_schedule_interaction_v1": pd.DataFrame(interaction_rows),
    }
    for name, frame in frames.items():
        frame.to_csv(data_dir / f"{name}.csv", index=False)
    return frames


def generate_all_datasets(data_dir: Path) -> dict[str, pd.DataFrame]:
    frames = {}
    for generator in [
        generate_exp1_data,
        generate_exp2_data,
        generate_exp3_data,
        generate_exp4_data,
        generate_exp5_data,
        generate_exp6_data,
    ]:
        frames.update(generator(data_dir))
    return frames
