Finish `build_spatial_v2_stage2`:
1. Run `pytest /scratch/jjyeung/orch_home_distill/spatial_v2/tests/test_stage2.py` and confirm 100% PASS (fix any remaining assertion cleanly).
2. Run the 1-GPU BF16 3-step forward+backward VRAM smoke test on `trinity-0-18` GPU `4` wrapped in `/data3/shared/scripts/vnice/vnice.sh` (`0 GB` disk footprint on `0-18` using exact Qwen3.5-9B config synthetic weights; verify exact peak VRAM, finite loss, non-zero grads, and zero `GatedDeltaNet` grad-checkpointing / `A_log` dtype issues — note: keep `linear_attn.A_log` and `linear_attn.norm.weight` in `float32`!).
3. Write the concise verified report to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/build_spatial_v2_stage2.md`.
