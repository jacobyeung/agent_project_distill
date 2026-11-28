# Hard Technical Debug (`Codex Astra 6.2`, high): Orchard `4× H100` `vla_libero` `B0` & `B1` Step 3–5 `non-finite loss`

## Problem
Three consecutive Orchard `4× H100` (`orchard-community-*`, H100 80GB HBM3) runs of `vla_libero` (`kit=e6bccd3deea4d7ab`, `Qwen3.5-9B` + `QwenOFT` / `vl_train.py`) failed early:
1. **`Job 176652`**: crashed on `Qwen3_5DecoderLayer` / gradient checkpointing.
2. **`Job 176658` (`B1` `step-544`, `gc=true`, VLM train-mode)**: `step 1` (`loss=0.7447`), then **`step 3: non-finite loss`**.
3. **`Job 176668` (`B0` base `Qwen3.5-9B`, `bs=16`, `gc=false`)**: `step 1` (`loss=0.6983`), then exited `train rc=1` (likely OOM or NaN).
4. **`Job 176670` (`B0` base `Qwen3.5-9B`, `gc=true`)**: **`step 5: non-finite loss`** — PROVING the bug happens EVEN ON BASE `Qwen3.5-9B` (`B0`) where all `48` `linear_attn.{A_log, norm.weight}` tensors start in `float32`!

## Your Mission (Read-Only Diagnosis -> Exact Surgical Fix Spec)
1. Inspect `/scratch/jjyeung/orch_home_distill/bluesky_20261128/orchard_nan_context/orchard_logs_dump.txt`, `/scratch/jjyeung/orch_home_distill/bluesky_20261128/train_b1_544_gc.sh`, `/scratch/jjyeung/orch_home_distill/bluesky_20261128/train_b0_gcs.sh` (if present), `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_orchard_testl_v3.md` (if present), AND the local preserved `vla_libero` kit under `/scratch/jjyeung/preserved_20261128/b15_vla/` (and batched read-only Orchard SSH via `trinity-0-13` `ossh.sh` ONLY if needed to inspect `j_168293/168298/168348`, `vl_train.py`, `QwenOFT.py`, `ds_config`, `fla` version, or `trace.jsonl`).
2. Pinpoint the **EXACT single root cause** (with `file:line`, exact tensor/kernel/optimizer mechanism) of why **BOTH `B0` and `B1`** hit `non-finite loss` at step `3–5` under `gc=true` on Orchard `4× H100` (e.g., `fla` Triton `chunk_gated_delta_rule` / `fused_norm_gate` / `l2norm` backward bug under activation checkpointing + BF16? DeepSpeed ZeRO-2 `bf16` master-weight/grad-clip config? `QwenOFT` `RegressionHead` / action-query LR / Adam eps? `m544`'s `48` `bf16` `A_log`/`norm.weight` tensors ALSO compounding on `B1`? How did prior `Test L` jobs `168293/168298/168348` avoid this?!).
3. Deliver the **EXACT minimal surgical fix** (preserving sealed kit `e6bccd3deea4d7ab` if fixable via wrapper/env/DeepSpeed config/flags, OR exact minimal diff + hash update if the sealed kit itself has a verified bug!) AND the **exact 10-step Orchard `4× H100` verification command** that proves BOTH `B0` and `B1` train past step 50+ with finite decreasing loss!

Write your concise, surgical root-cause & fix spec (`<=120` lines) to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/astra62_debug_orchard_nan.md`. Read-only; do NOT modify repo code or submit Slurm jobs.
