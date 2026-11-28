`build_where_cache_d5_s0.py` is already updated and **`trinity-2-28` GPU `7` is FREE (`0%, 2 MiB`)**!
1. Run `build_where_cache_d5_s0.py` on `trinity-2-28` GPU `7` wrapped in `/data3/shared/scripts/vnice/vnice.sh` (`CUDA_VISIBLE_DEVICES=7`) to complete `where_cache_d5_s0/` (and check `P-1..P-4` + `step-544` vs `DA3` LIBERO depth diagnostic outputs in `work_vla_where_cache/out/`).
2. Verify `100%` `d5_s0` key coverage, exact `vla_libero` `U1` schema/dtypes, `0` NaN/Inf, deterministic reload.
3. Write the concise verified report to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_vla_where_cache_prep.md` with exact cache paths, sizes, `step-544` vs `DA3` LIBERO depth numbers, and exact Orchard `U1` launch flags.
