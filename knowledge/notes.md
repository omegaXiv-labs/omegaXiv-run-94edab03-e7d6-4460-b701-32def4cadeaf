# Biased-Noise Surface-Code Thresholds: Synthesis

## Scope and corpus
This corpus targets threshold estimation for the surface code under dephasing-biased, gate-dependent noise with repeated syndrome extraction. It covers 35 sources: 27 primary papers and 8 software/documentation sources. The strongest directly aligned papers are [tuckett2020_fault_tolerant_thresholds], [bonilla2021_xzzx], [higgott2023_improved_decoding], [xiao2024_finite_size_corrections], and [martinez2025_two_level_circuit].

## 1. Threshold theory and why bias matters
The classical threshold picture for topological codes comes from [dennis2002_topological_memory], [wang2003_confinement_higgs], and [kitaev2003_anyons]. These papers establish the homological decoding framework and the statistical-mechanical mapping used later to interpret threshold crossings.

A consistent cross-paper theme is that dephasing bias should be treated as usable structure, not averaged away. [aliferis2008_biased_noise] makes this point in a non-topological FT setting, while [stephens2013_topological_biased] brings it directly into surface-code threshold estimation. The conceptual jump is: unbiased surface-code thresholds are not the relevant baseline once the hardware noise is strongly asymmetric.

Similarity:
- [aliferis2008_biased_noise], [stephens2013_topological_biased], and [tuckett2020_fault_tolerant_thresholds] all argue that the effective threshold depends on whether the circuit preserves the native asymmetry.

Difference:
- [dennis2002_topological_memory] and [wang2003_confinement_higgs] are mostly asymptotic and structural.
- [xiao2024_finite_size_corrections] is explicitly finite-size and explains why small-distance sweeps can disagree with asymptotic intuition.

## 2. Tailored surface-code families under biased noise
The main code-family progression is:
- early biased surface-code adaptation: [stephens2013_topological_biased]
- tailored surface codes: [tuckett2018_ultrahigh_threshold], [tuckett2019_tailoring_surface_codes], [tuckett2020_fault_tolerant_thresholds]
- code-family generalization: [li2019_compass_codes]
- XZZX and descendants: [bonilla2021_xzzx], [xu2023_tailored_xzzx], [dua2024_clifford_deformed]

The central formal definition in [bonilla2021_xzzx] is the XZZX stabilizer deformation, which changes the syndrome geometry so that dominant Z faults become easier to decode. That paper also reports the biased-noise scaling laws `O((p / sqrt(eta))^(d/2))` and, at infinite bias, `O(p^(d^2/2))`. These expressions matter because they explain why the logical-error slope can improve sharply with distance even when the raw threshold shift is modest.

[tuckett2019_tailoring_surface_codes] and [li2019_compass_codes] show that geometry and boundary choice are not implementation details. They are part of the error model. In practice, this means the simulation phase should treat code layout and boundary conditions as first-class experimental parameters, especially if the schedule changes hook-error orientation.

## 3. Circuit-level noise, schedules, and decoder dependence
The strongest direct lesson for the requested project is that code-capacity results are not enough. [tuckett2020_fault_tolerant_thresholds] and [higgott2023_improved_decoding] show that repeated syndrome extraction, boundary fragility, and circuit-specific decoder design can materially lower or raise the observed threshold.

[tsai2024_temporal_fragility] adds a closely related warning: schedule-induced temporal fragility can erase a nominal bias advantage. [martinez2025_two_level_circuit] is especially important because it studies realistic circuit-level biased noise with two-level qubits rather than relying on idealized bias-preserving hardware. That makes it the most relevant recent reference for the user’s requested gate-dependent and scheduling-aware simulations.

Similarity:
- [tuckett2020_fault_tolerant_thresholds], [higgott2023_improved_decoding], [tsai2024_temporal_fragility], and [martinez2025_two_level_circuit] all conclude that the realized threshold depends on the full syndrome-extraction pipeline, not just the code.

Difference:
- [tuckett2018_ultrahigh_threshold] and [bonilla2021_xzzx] are often cited for dramatic gains, but [higgott2023_improved_decoding] and [tsai2024_temporal_fragility] explain why those gains can shrink at circuit level if boundaries or time-direction effects are mishandled.

## 4. Finite-size behavior and analytical comparison points
The target distances `d in {3,5,7,9}` make finite-size theory unavoidable. [robertson2017_small_memories] already warns that small-memory behavior can differ from asymptotic preference ordering. [xiao2024_finite_size_corrections] gives the clearest recent formal treatment, including the biased-noise parameterization

`p_x = p_y = p_z / (2 eta)` and `p = p_x + p_y + p_z`.

It also highlights a special point `p = (1 + eta^(-1)) / (2 + eta^(-1))` and an exact finite-size logical-failure expression

`P_f = 3/4 - (1/4) exp(-2 d_Z arctanh(1/(2 eta)))`.

These formulas matter for interpreting non-monotonic crossing behavior and anti-threshold effects. If the simulation phase finds mismatches between theoretical threshold curves and Monte Carlo crossings, [xiao2024_finite_size_corrections] is the first place to check whether the disagreement is finite-size rather than a simulator bug.

## 5. Beyond standard surface-code families
The broader frontier includes [huang2023_3d_topological_codes], [liang2025_xyz_cyclic], and [setiawan2025_x3z3_floquet]. These papers matter less as direct baselines for the immediate implementation, but they establish that:
- threshold gains under strong bias can persist across multiple code families
- schedule design itself can be a tailoring knob
- the best asymptotic code family may not be the best realistic finite-distance surface-code implementation

This broader context is useful when writing limitations. If the final study only evaluates standard or XZZX surface codes, it should state that it is not exhausting the wider biased-noise design space.

## 6. Simulation and decoder tooling
The recommended software stack from this corpus is:
- circuit generation and fast stabilizer simulation: [gidney2021_stim_paper], [stim_repo]
- matching decoder baseline: [pymatching_repo]
- faster matching backend for scale: [higgott2025_sparse_blossom]
- flexible noisy-circuit modeling fallback: [qiskit_aer_docs]
- validation and alternate infrastructure: [qecsim_repo], [panqec_repo], [pecos_repo], [tesseract_repo]
- directly relevant reusable implementation: [qec_two_level_bias_repo]

Practical recommendation from the literature:
- Use Stim when the noisy syndrome-extraction circuit can be compiled into a detector error model.
- Use Qiskit Aer when the gate-dependent model requires more custom channel composition or when direct detector extraction is inconvenient.
- Keep a small-distance cross-check path with qecsim or a simplified Aer model.

## 7. Most important similarities and differences across the corpus
Strong agreement:
- Exploiting Z-dominant bias improves performance if the code, boundary conditions, decoder, and circuit all preserve that structure. Evidence: [aliferis2008_biased_noise], [stephens2013_topological_biased], [tuckett2020_fault_tolerant_thresholds], [bonilla2021_xzzx], [martinez2025_two_level_circuit].
- Decoder quality and circuit schedule are inseparable from threshold estimation. Evidence: [bravyi2014_mld_surface], [darmawan2018_tensor_network], [higgott2023_improved_decoding], [higgott2025_sparse_blossom].
- Finite-size logical rates can disagree with asymptotic threshold narratives. Evidence: [robertson2017_small_memories], [xiao2024_finite_size_corrections].

Main disagreements or tensions:
- Idealized or code-capacity gains are larger than realistic circuit-level gains. Compare [tuckett2018_ultrahigh_threshold] and [bonilla2021_xzzx] against [tuckett2020_fault_tolerant_thresholds], [tsai2024_temporal_fragility], and [martinez2025_two_level_circuit].
- Different families claim near-50% or very high thresholds in special bias limits, but those statements depend on decoder class, noise model, and boundary/schedule details. Compare [tuckett2019_tailoring_surface_codes], [huang2023_3d_topological_codes], [dua2024_clifford_deformed], and [liang2025_xyz_cyclic].

## 8. Actionable takeaways for the implementation phase
1. Use [martinez2025_two_level_circuit], [tuckett2020_fault_tolerant_thresholds], [bonilla2021_xzzx], and [higgott2023_improved_decoding] as the primary comparison set for realistic circuit-level claims.
2. Treat schedule design, hook-error orientation, and boundary choices as explicit experimental variables, not fixed background details.
3. Report both threshold crossings and logical error per round at each finite distance because [robertson2017_small_memories] and [xiao2024_finite_size_corrections] show that finite-size behavior can mislead.
4. Start implementation with Stim + PyMatching or sparse blossom, and use Qiskit Aer only when the biased gate-dependent model is too custom for a clean detector-error-model workflow.
5. When documenting limitations, state clearly whether the study models only Pauli bias or also gate-dependent correlated effects in the spirit of [chubb2021_correlated_noise] and [martinez2025_two_level_circuit].
