# Nominal Versus Effective Bias

Table note: means are taken over decoder, distance, and seed slices. The table reports compiled component rates and effective bias under the selected normalization.

| code_family | schedule_family | eta | bar_p_x | bar_p_y | bar_p_z | eta_eff | chi_temp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clifford_deformed_surface | bias_preserving_reference | 1 | 0.0007 | 0.0007 | 0.0013 | 0.8649 | 0.9800 |
| clifford_deformed_surface | bias_preserving_reference | 5 | 0.0002 | 0.0002 | 0.0021 | 4.3428 | 0.9800 |
| clifford_deformed_surface | bias_preserving_reference | 20 | 0.0001 | 0.0001 | 0.0024 | 17.3000 | 0.9800 |
| clifford_deformed_surface | bias_preserving_reference | 50 | 0.0000 | 0.0000 | 0.0025 | 43.3119 | 0.9800 |
| clifford_deformed_surface | cnot_decomposition_variant | 1 | 0.0010 | 0.0010 | 0.0011 | 0.4086 | 0.7400 |
| clifford_deformed_surface | cnot_decomposition_variant | 5 | 0.0003 | 0.0003 | 0.0018 | 2.0520 | 0.7400 |
| clifford_deformed_surface | cnot_decomposition_variant | 20 | 0.0001 | 0.0001 | 0.0021 | 8.1728 | 0.7400 |
| clifford_deformed_surface | cnot_decomposition_variant | 50 | 0.0000 | 0.0000 | 0.0021 | 20.4579 | 0.7400 |
| clifford_deformed_surface | measurement_reset_asymmetric | 1 | 0.0009 | 0.0009 | 0.0011 | 0.4600 | 0.7800 |
| clifford_deformed_surface | measurement_reset_asymmetric | 5 | 0.0003 | 0.0003 | 0.0019 | 2.3091 | 0.7800 |
| clifford_deformed_surface | measurement_reset_asymmetric | 20 | 0.0001 | 0.0001 | 0.0021 | 9.2022 | 0.7800 |
| clifford_deformed_surface | measurement_reset_asymmetric | 50 | 0.0000 | 0.0000 | 0.0022 | 23.0235 | 0.7800 |
