# Kernel provenance

Status: VERIFIED for the new K1-train selection. Authorization: pending orchestrator.
The design record cites a five-rule selection on 88 official VSI-Bench ScanNet items; it does not prove a clean origin for each constant.
S1k uses only the 110 K1 TRAINING room captures and stored dense-64 DA3 predictions, sampled at their 32 anchors through adapter.convert.
The preregistered Cartesian grid is margin {0.05, 0.10} m × cell {0.05, 0.10} m × votes {1, 2} × closing {0.10, 0.20} m.
The objective is mean per-item K1-train MRA; refusals score zero. Ties choose the first listed tuple.
Winner: {'height_margin_m': 0.05, 'cell_m': 0.1, 'min_votes': 2, 'closing_m': 0.2}; K1-train MRA 77.636364.
Legacy tuple: {'height_margin_m': 0.1, 'cell_m': 0.05, 'min_votes': 2, 'closing_m': 0.2}. Winner equals legacy: False.
K1 labels inherit the legacy kernel; this selection does not establish benchmark-independent labels or a new rule family.
Measured: 188.02 CPU-seconds, 188.96 elapsed seconds; eight-thread limit; no new inference.
Command: bash scripts/cpu.sh scripts/s1k.py > out/S1K.log 2>&1
Receipt command: bash scripts/cpu.sh scripts/kernel_provenance.py
Evidence: out/S1K_REGISTRATION.json, out/S1K_RESULTS.json, configs/KERNEL_FROZEN.json; every input has a SHA256.
evidence/s1k_execution_code preserves the exact source hashes used during selection; execution_code_snapshots maps the recorded paths.
The frozen kernel serves selection.py and price.py. reproduce.py checks the legacy kernel against its stored reference.
The benchmark-origin disclosure is retained because the task explicitly requires it. No benchmark item or score was read for S1k.
