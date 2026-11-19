Implemented the guards and fixture fixes.

- Tests: **26/26 part 1; 20/20 part 2**.
- CPU steps 1–4 and fresh fixtures pass. STEP5 requires CUDA; no GPU inference ran.
- GPU launch safeguards remain incomplete; the report lists each blocker.
- Estimates: **0.876 GPU-h default**, **1.140 GPU-h with `--all-aliases`**.

[Report](out/PH2GATE_REPORT.md) · [Staging inventory](out/STAGING_PART2.tsv) · [Archive](out/sb_ph2gate.tar)

Verified archive SHA256:
```text
92c3c1d9569daaf2c6ba99a0ac4e8a02f8e0ba7e66fd0f72ec885b2453830842
```