# Brief: Diagnose Orchard `Job 176658` (`step 3 non-finite loss`) & Relaunch `Test L` (`B1` & `B0`) on `4× H100`

## Context
- Prior lane `launch_orchard_vla_testl` stalled (`task-406` killed).
- Orchard **Job `176658` (`a15_cot_apb1sd03`, `B1` `step-544`, `4× H100`)** staged cleanly (`kit=e6bccd3deea4d7ab` untouched!), enabled VLM train-mode + gradient checkpointing, stepped `step 1` (`loss=0.7447`), and then failed at `step 3` with:
  `2026-11-28T14:45:07Z train rc=1 {"step": 3, "reason": "non-finite loss", "utc": "2026-11-28T14:44:22Z"}`
- **Strong hypothesis already visible in `j_176658.out`:**
  `B1_CHECK_OK ... dtype diffs {'torch.float32->torch.bfloat16': 48}` — specifically **`model.language_model.layers.*.linear_attn.A_log`** and **`linear_attn.norm.weight`** (48 GatedDeltaNet tensors!) were exported in `bfloat16` inside `step-544` (`m544`) instead of `float32` as in base `Qwen3.5-9B` (`B0`)!
  (Also check whether `train_b1_544_gc.sh`'s `VLM train-mode` or `gradient_checkpointing` or `grad_norm` / `AdamW` caused the NaN — DO NOT guess; verify from `j_176658` logs + `vl_train.py`!)

## Hard Rules
- Batch Orchard SSH via `trinity-0-13`: `timeout 60 ssh -o BatchMode=yes -o ConnectTimeout=10 trinity-0-13 "timeout 50 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh '...'"`.
- **NEVER mutate the sealed `vla_libero` kit files (`vl_eval.py`, `vl_heads_hook.py`, `vl_replay_server.py`, `vl_server.py`, `vl_train.py`) unless explicitly justified and verified!** Note: `stage.sh` / pre-staging weights (e.g., casting those 48 `A_log`/`norm.weight` tensors back to `float32` in the staged `/tmp` copy to match `B0` exact dtypes!) does NOT alter the sealed kit!
- **Opaque Orchard job names:** `a15_cot_ap<alnum>` (no underscores after `ap`, no benchmark/method words).
- **Orchard `/project/community` only has `~9 GiB` free** — keep all caches (`HF_HOME`, `TORCH_HOME`, `TRITON_CACHE_DIR`, `PIP_CACHE_DIR`, `XDG_CACHE_DIR`) and training runs on `/tmp` (`5.8 TB` free!) and export saved checkpoints to `gs://cmu-gpucloud-jjyeung/vla_libero/` (only small `<50 MB` logs/evals on `/project/community`).
- **Keep `4× H100 advanced` busy!** Remember we need **BOTH `B0` (base `Qwen3.5-9B`) AND `B1` (`step-544`)** for `Test L`!

## Exact Steps
1. Inspect `j_176658` full error output, `trace.jsonl` (steps 1–3, `loss`, `grad_norm`, `lr`), `/scratch/jjyeung/orch_home_distill/bluesky_20261128/train_b1_544_gc.sh`, and `/project/community/jjyeung/45e92888780e/` (`vl_train.py` around `non-finite loss` / `gradient_checkpointing` / `A_log` / `stage.sh` / `train_arm.sh`) in ONE batched Orchard inspection!
2. Identify the **exact root cause** of `step 3 non-finite loss`:
   - Compare how `B0` vs `B1` (`m544`) behaves (`48` `bf16` `A_log`/`norm.weight` tensors vs `VLM train-mode` vs `grad_checkpointing` vs `max_grad_norm`).
   - Also check why `176652` failed earlier (inspect `j_176652.out` tail if helpful — probably the earlier `grad_checkpointing` issue that `train_b1_544_gc.sh` patched!).
3. **Execute decisive fix & launch on Orchard `4× H100 advanced`:**
   - If the `48` `bf16 -> fp32` `linear_attn.{A_log,norm.weight}` dtype mismatch in `m544` (or another verified surgical wrapper fix) explains the NaN, fix it cleanly in the staging wrapper (verify `dtype_diffs == {}` vs `B0`!) and submit **`B1` (`1,000`-step shake-down or full decisive `B1` `d5_s0`)** under opaque name `a15_cot_apb1sd04`!
   - Verify with 1–2 min cadence during ramp-up that it passes **step 1, step 3, step 10, step 50+** cleanly with **finite decreasing loss** and healthy `step_s`!
   - If `B1` still hits NaN on a second check OR needs deeper `GatedDeltaNet` debugging, immediately submit **`B0` (`a15_cot_apb0sd01`, base `Qwen3.5-9B` `d5_s0`)** on `4× H100` to isolate `B0` vs `B1` empirically AND report exact `vl_train.py` trace so we can escalate cleanly!
4. Stay alive monitoring the live Orchard `4× H100` job through at least step 50+ (or full completion + `eval_plan.sh` if fast enough!) and write a concise verified report to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_orchard_testl_b1_fix.md`.
