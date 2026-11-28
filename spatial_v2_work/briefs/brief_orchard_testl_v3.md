# Brief: Unblock & Launch Orchard `4× H100` `Test L` (`B1` & `B0`) — NO Rabbit Holes!

## Context
Orchard `4× H100 advanced` (`mt01` / `adv_4gpu_qos`) is currently IDLE (`0` running jobs!) because two prior attempts stalled:
- `Job 176652`: hit a `Qwen3_5DecoderLayer` / `gradient_checkpointing` issue.
- `Job 176658` (`a15_cot_apb1sd03`, `/scratch/jjyeung/orch_home_distill/bluesky_20261128/train_b1_544_gc.sh`): staged `B1` (`step-544` `m544`) with sealed kit `e6bccd3deea4d7ab` untouched, enabled VLM train-mode + gradient checkpointing, stepped Step 1 (`loss=0.7447`), and exited at Step 3 with `{"step": 3, "reason": "non-finite loss"}`.
- `j_176658.out` showed **`dtype_diffs: {'torch.float32->torch.bfloat16': 48}`** specifically on `model.language_model.layers.*.linear_attn.A_log` and `linear_attn.norm.weight` (all 24 `GatedDeltaNet` layers!).
- Prior lane `orchard_testl_v2` spent 51 turns reading `fla` Triton kernels without launching a single Orchard job. **DO NOT spend >4 turns reading library internals!**

## Strict 5-Minute Execution Mandate
1. **Turn 1–2 (ONE batched Orchard SSH call via `trinity-0-13` `ossh.sh`):**
   - Inspect `/project/community/jjyeung/45e92888780e/logs/j_168293*`, `j_168298*`, `j_168348*` (prior working `Test L` jobs!) AND `/project/community/jjyeung/45e92888780e/logs/j_176658.out` + `train_arm.sh` + `/scratch/jjyeung/orch_home_distill/bluesky_20261128/train_b1_544_gc.sh` to see EXACTLY how prior `Test L` jobs ran without NaN (was `VLM` frozen or unfrozen? `bf16` or `fp32` `A_log`? `deepspeed` ZeRO stage? `lr`? `grad_checkpointing`? `B0` vs `B1`?).
2. **Turn 3–5 (IMMEDIATELY put `4× H100 advanced` to work!):**
   - Remember `Test L` requires BOTH **`B1` (`step-544`)** AND **`B0` (base `Qwen3.5-9B`)** under the EXACT same sealed kit (`e6bccd3d`) & recipe!
   - If restoring `m544`'s `48` `linear_attn.{A_log, norm.weight}` tensors back to `float32` during staging (matching `B0` exact `dtype_diffs == {}`, keeping the sealed kit untouched!) + using the verified working `train_arm.sh` recipe fixes `B1`: **SUBMIT `B1` (`a15_cot_apb1sd04`) on `4× H100 advanced` IMMEDIATELY!**
   - If there is ANY ambiguity about whether `m544` vs `train_b1_544_gc.sh` caused the step-3 NaN, **SUBMIT `B0` (`a15_cot_apb0sd01`, base `Qwen3.5-9B`, exact `train_arm.sh` recipe!) on `4× H100 advanced` FIRST** (so `4× H100` generates required `Test L` baseline data AND empirically isolates `B0` vs `B1` in 6 minutes!).
3. **Ramp-Up Cadence (1–2 min checks):**
   - Watch the submitted job through staging -> Step 1 -> Step 3 -> Step 10 -> Step 50+ (confirm finite decreasing loss, healthy `step_s`, `0` NaN!).
   - If the `1,000`-step shake-down completes within your turn budget (remember ~30–40 min on `4× H100`), also ensure checkpoint export goes to `gs://cmu-gpucloud-jjyeung/vla_libero/` (NOT `/project/community`, which only has `9.0 GiB` free!) and launch `eval_plan.sh` or the next matched arm (`B0`/`B1`)!

## Hard Rules
- Batch Orchard SSH via `trinity-0-13`: `timeout 60 ssh -o BatchMode=yes -o ConnectTimeout=10 trinity-0-13 "timeout 50 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh '...'"`.
- Opaque job names only: `a15_cot_ap<alnum>` (no underscores after `ap`, no benchmark/method words).
- All caches & staging on `/tmp` (`5.8 TB` free); keep `/project/community` writes `<50 MB`.
- Never mutate sealed kit files (`vl_eval.py`, `vl_heads_hook.py`, `vl_replay_server.py`, `vl_server.py`, `vl_train.py`).
- Write concise verified report to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_orchard_testl_v3.md`.
