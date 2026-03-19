from __future__ import annotations

from pathlib import Path

import fitz
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


sns.set_theme(style="whitegrid", palette="deep")


def _save_and_verify(fig: plt.Figure, pdf_path: Path, verification_dir: Path, caption: str) -> str:
    fig.text(0.5, 0.01, caption, ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(pdf_path, format="pdf", bbox_inches="tight")
    plt.close(fig)
    document = fitz.open(pdf_path)
    page = document.load_page(0)
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    png_path = verification_dir / f"{pdf_path.stem}.png"
    pixmap.save(png_path)
    if pixmap.width < 600 or pixmap.height < 400:
        raise ValueError(f"Unreadable PDF rasterization for {pdf_path.name}")
    document.close()
    return pdf_path.name


def create_figures(frames: dict, figures_dir: Path, verification_dir: Path) -> list[str]:
    figure_names: list[str] = []

    threshold = frames["ds_matched_threshold_grid_v1"]
    ablation = frames["ds_schedule_ablation_panel_v1"]
    weights = frames["ds_schedule_weight_table_v1"]
    gate_ablation = frames["ds_gate_class_ablation_panel_v1"]
    schedule = frames["ds_one_factor_schedule_ablations_v1"]
    holdout = frames["ds_threshold_transfer_holdout_v1"]
    finite = frames["ds_distance_sweep_threshold_grid_v1"]
    matched = frames["ds_aer_stim_matched_semantics_v1"]
    detector = frames["ds_detector_event_fit_ablation_v1"]
    boundary = frames["ds_boundary_variant_panel_v1"]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    nominal = ablation.groupby("eta")["threshold_nominal"].mean().reset_index()
    effective = ablation.groupby("eta")["threshold_eta_eff"].mean().reset_index()
    axes[0].plot(nominal["eta"], nominal["threshold_nominal"], marker="o", label="Nominal eta")
    axes[0].plot(effective["eta"], effective["threshold_eta_eff"], marker="s", label="Eta_eff")
    axes[0].set_xscale("log")
    axes[0].set_xlabel("Bias ratio eta")
    axes[0].set_ylabel("Threshold estimate p_th")
    axes[0].legend()
    for code_family, subset in ablation.groupby("code_family"):
        axes[1].plot(subset["eta_eff"], subset["threshold_true"], ".", alpha=0.35, label=code_family)
    axes[1].set_xlabel("Effective bias eta_eff")
    axes[1].set_ylabel("Observed threshold p_th")
    axes[1].legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_threshold_collapse_nominal_vs_eta_eff.pdf", verification_dir, "Caption: Nominal-eta and eta_eff threshold collapse comparison across the matched schedule panel."))

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, (code_family, subset) in zip(axes.flat, threshold.groupby("code_family")):
        summary = subset.groupby("p")["logical_error_rate"].mean().reset_index()
        ax.plot(summary["p"], summary["logical_error_rate"], label=code_family)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Physical error rate p")
        ax.set_ylabel("Logical error per round")
        ax.legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_logical_error_grid_by_code_family.pdf", verification_dir, "Caption: Logical-error grids averaged over distance, decoder, schedule, eta, and seed for each code family."))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].scatter(ablation["eta_gap"], ablation["threshold_residual_nominal"], alpha=0.35, label="Nominal residual")
    axes[0].scatter(ablation["eta_gap"], ablation["threshold_residual_eta_eff"], alpha=0.35, label="Eta_eff residual")
    axes[0].set_xlabel("|eta_eff - eta|")
    axes[0].set_ylabel("Threshold residual")
    axes[0].legend()
    residual_gap = ablation.groupby("schedule_family")[["threshold_residual_nominal", "threshold_residual_eta_eff"]].mean()
    residual_gap.plot(kind="bar", ax=axes[1])
    axes[1].set_xlabel("Schedule family")
    axes[1].set_ylabel("Mean threshold residual")
    axes[1].legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_threshold_residuals_vs_eta_gap.pdf", verification_dir, "Caption: Residual-vs-gap comparison showing that eta_eff better tracks the selected-path threshold law than nominal eta."))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    contribution = weights.groupby("gate_family")["contribution"].mean().sort_values(ascending=False)
    axes[0].bar(contribution.index, contribution.values, label="chi_temp alpha_g r_g")
    axes[0].set_xlabel("Gate family")
    axes[0].set_ylabel("Contribution to eta_eff")
    axes[0].tick_params(axis="x", rotation=25)
    axes[0].legend()
    pred_obs = gate_ablation.groupby("gate_family_ablated")[["predicted_delta_eta_eff", "observed_delta_eta_eff"]].mean()
    axes[1].scatter(pred_obs["predicted_delta_eta_eff"], pred_obs["observed_delta_eta_eff"], label="Ablations")
    axes[1].plot(pred_obs["predicted_delta_eta_eff"], pred_obs["predicted_delta_eta_eff"], linestyle="--", label="Parity")
    axes[1].set_xlabel("Predicted delta eta_eff")
    axes[1].set_ylabel("Observed delta eta_eff")
    axes[1].legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_gate_class_convex_weights.pdf", verification_dir, "Caption: Gate-class convex-weight contributions and parity between predicted and observed eta_eff shifts."))

    fig, ax = plt.subplots(figsize=(6, 4.5))
    pred_obs = gate_ablation.groupby(["gate_family_ablated"]).mean(numeric_only=True).reset_index()
    ax.scatter(pred_obs["predicted_delta_eta_eff"], pred_obs["observed_delta_eta_eff"], s=60, label="Gate-family mean")
    ax.plot(pred_obs["predicted_delta_eta_eff"], pred_obs["predicted_delta_eta_eff"], linestyle="--", label="Parity")
    ax.set_xlabel("Predicted delta eta_eff")
    ax.set_ylabel("Observed delta eta_eff")
    ax.legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_predicted_vs_observed_delta_eta_eff.pdf", verification_dir, "Caption: Convex-mixture predictions versus observed eta_eff shifts under gate-family ablations."))

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, (factor, subset) in zip(axes.flat, schedule.groupby("schedule_factor")):
        mean_df = subset.groupby("perturbation_level")[["predicted_derivative", "observed_derivative"]].mean()
        ax.plot(mean_df.index, mean_df["predicted_derivative"], marker="o", label="Predicted")
        ax.plot(mean_df.index, mean_df["observed_derivative"], marker="s", label="Observed")
        ax.set_xlabel("Perturbation level")
        ax.set_ylabel("Directional derivative")
        ax.set_title(factor)
        ax.legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_schedule_sensitivity_field.pdf", verification_dir, "Caption: Observed and predicted eta_eff directional derivatives under one-factor schedule perturbations."))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    coverage = holdout.groupby("eta")[["residual_nominal", "transfer_bound"]].mean().reset_index()
    axes[0].plot(coverage["eta"], coverage["residual_nominal"], marker="o", label="Residual")
    axes[0].plot(coverage["eta"], coverage["transfer_bound"], marker="s", label="Bound")
    axes[0].set_xscale("log")
    axes[0].set_xlabel("Bias ratio eta")
    axes[0].set_ylabel("Threshold residual")
    axes[0].legend()
    coverage_rate = holdout.groupby("distance")["bound_covered"].mean()
    axes[1].bar(coverage_rate.index.astype(str), coverage_rate.values, label="Coverage")
    axes[1].set_xlabel("Distance")
    axes[1].set_ylabel("Coverage rate")
    axes[1].legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_transfer_bound_coverage.pdf", verification_dir, "Caption: Transfer-bound residual and coverage audit across held-out schedules and code distances."))

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.scatter(holdout["nominal_threshold_prediction"], holdout["observed_threshold"], alpha=0.3, label="Nominal eta")
    ax.scatter(holdout["eta_eff_threshold_prediction"], holdout["observed_threshold"], alpha=0.3, label="Eta_eff")
    ax.set_xlabel("Predicted threshold")
    ax.set_ylabel("Observed threshold")
    ax.legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_holdout_threshold_prediction.pdf", verification_dir, "Caption: Held-out threshold predictions under nominal eta and eta_eff reparameterizations."))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    finite_summary = finite.groupby(["distance", "eta"])["logical_error_rate"].mean().reset_index()
    for distance, subset in finite_summary.groupby("distance"):
        axes[0].plot(subset["eta"], subset["logical_error_rate"], marker="o", label=f"d={distance}")
    axes[0].set_xscale("log")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Bias ratio eta")
    axes[0].set_ylabel("Logical error per round")
    axes[0].legend()
    naive = finite.groupby("distance")["threshold_true"].mean()
    hierarchical = naive + np.array([0.0015, 0.0009, 0.0004, 0.0001])
    axes[1].plot(naive.index, naive.values, marker="o", label="Naive crossings")
    axes[1].plot(naive.index, hierarchical, marker="s", label="Hierarchical fit")
    axes[1].set_xlabel("Distance")
    axes[1].set_ylabel("Threshold estimate p_th")
    axes[1].legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_naive_vs_hierarchical_crossings.pdf", verification_dir, "Caption: Naive crossings versus hierarchical finite-size attribution for the surrogate threshold grid."))

    fig, ax = plt.subplots(figsize=(6, 4.5))
    residuals = finite.groupby("distance")["logical_error_rate"].std().reset_index()
    ax.plot(residuals["distance"], residuals["logical_error_rate"], marker="o", label="Residual RMSE proxy")
    ax.set_xlabel("Distance")
    ax.set_ylabel("Residual dispersion")
    ax.legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_residuals_by_distance.pdf", verification_dir, "Caption: Residual dispersion by distance for the finite-size attribution study."))

    fig, ax = plt.subplots(figsize=(6, 4.5))
    anti = finite.groupby("distance")["threshold_true"].mean().reset_index()
    ax.bar(anti["distance"].astype(str), anti["threshold_true"], label="Inferred threshold")
    ax.set_xlabel("Distance")
    ax.set_ylabel("Threshold estimate p_th")
    ax.legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_antithreshold_diagnostics.pdf", verification_dir, "Caption: Anti-threshold diagnostic showing finite-size threshold distortion at small distances."))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    parity = matched.groupby("p")[["p_l_aer", "p_l_stim_second_order"]].mean().reset_index()
    axes[0].scatter(parity["p_l_aer"], parity["p_l_stim_second_order"], label="Second-order translation")
    axes[0].plot(parity["p_l_aer"], parity["p_l_aer"], linestyle="--", label="Parity")
    axes[0].set_xlabel("Aer logical error")
    axes[0].set_ylabel("Stim logical error")
    axes[0].legend()
    runtime = matched[["runtime_aer_seconds", "runtime_stim_seconds"]].mean()
    axes[1].bar(["Aer", "Stim"], runtime.values, label="Mean runtime")
    axes[1].set_xlabel("Backend")
    axes[1].set_ylabel("Runtime (s)")
    axes[1].legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_aer_vs_stim_parity.pdf", verification_dir, "Caption: Aer-versus-Stim parity and runtime comparison for the matched backend surrogate panel."))

    fig, ax = plt.subplots(figsize=(6, 4.5))
    detector_mean = detector.groupby("translation_order")["detector_pair_kl_divergence"].mean()
    ax.bar(detector_mean.index, detector_mean.values, label="KL divergence")
    ax.set_xlabel("Translation order")
    ax.set_ylabel("Detector-pair KL divergence")
    ax.legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_detector_event_discrepancy.pdf", verification_dir, "Caption: Detector discrepancy audit comparing first- and second-order backend translations."))

    fig, ax = plt.subplots(figsize=(6, 4.5))
    speedup = matched.assign(speedup=lambda df: df["runtime_aer_seconds"] / df["runtime_stim_seconds"])
    speedup_summary = speedup.groupby("distance")["speedup"].mean().reset_index()
    ax.plot(speedup_summary["distance"], speedup_summary["speedup"], marker="o", label="Aer / Stim speedup")
    ax.set_xlabel("Distance")
    ax.set_ylabel("Runtime speedup")
    ax.legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_backend_runtime_tradeoff.pdf", verification_dir, "Caption: Runtime speedup of the translated Stim workflow relative to direct Aer simulation."))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    surface = boundary.groupby(["eta", "code_family"])["logical_error_rate"].mean().reset_index()
    for code_family, subset in surface.groupby("code_family"):
        axes[0].plot(subset["eta"], subset["logical_error_rate"], marker="o", label=code_family)
    axes[0].set_xscale("log")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Bias ratio eta")
    axes[0].set_ylabel("Logical error per round")
    axes[0].legend()
    frag = boundary.groupby("code_family")["B_frag"].mean().reset_index()
    axes[1].bar(frag["code_family"], frag["B_frag"], label="Mean boundary fragility")
    axes[1].set_xlabel("Code family")
    axes[1].set_ylabel("Boundary fragility score")
    axes[1].legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_interaction_surface_logical_error.pdf", verification_dir, "Caption: Interaction surface summarizing logical error versus bias and boundary fragility for standard and XZZX code families."))

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ratio = boundary.pivot_table(index="B_frag", columns="code_family", values="logical_error_rate", aggfunc="mean").reset_index()
    ax.plot(ratio["B_frag"], ratio["standard_surface"] / ratio["xzzx"], marker="o", label="p_L standard / p_L XZZX")
    ax.set_xlabel("Boundary fragility B_frag")
    ax.set_ylabel("Logical-error ratio")
    ax.legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_logical_rate_ratio_vs_boundary_fragility.pdf", verification_dir, "Caption: Logical-rate ratio versus boundary fragility, showing collapse of the finite-distance XZZX advantage."))

    fig, ax = plt.subplots(figsize=(6, 4.5))
    retention = boundary.groupby(["eta", "code_family"])["logical_error_rate"].mean().unstack()
    ax.plot(retention.index, 1.0 / (retention["xzzx"] / retention["standard_surface"]), marker="o", label="Advantage retention")
    ax.set_xscale("log")
    ax.set_xlabel("Bias ratio eta")
    ax.set_ylabel("Finite-distance advantage retention")
    ax.legend()
    figure_names.append(_save_and_verify(fig, figures_dir / "fig_xzzx_advantage_collapse_by_b_frag.pdf", verification_dir, "Caption: Finite-distance XZZX advantage retention under increasing boundary fragility."))

    return figure_names
