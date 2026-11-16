# VLA LIBERO kit for Test L (lane vla_libero, 2026-11-11)

**Question.** Can Test L (design record VLA_ACTION_HEAD_DESIGN_20261111 §4.1 under `vla_schema_v1`: LIBERO-Spatial at 5 demos per task, B1 and U1, primary endpoint U1 − B1 on 500 paired episodes at 10k steps) launch on Orchard without any debugging at launch time?

**Answer.** Yes for the B1 shake-down and the decisive B1, once the orchestrator gives the go for one GPU test of the hooked recipe. U1 waits for vla_where's cache and loader. B0 and other control-only arms stay disabled until the user says yes. The kit lives on Trinity at `/scratch/jjyeung/orch_cd/vla_libero/work/kit` and is sealed by `KIT_SHA256`; its Orchard copy, with the environments and data, is `/project/community/jjyeung/vla_libero`. `out/STACK.md` holds the versions and hashes, `out/PRELAUNCH_CARD.md` the arms, the readout and the cost, and `out/HEADS_HOOK.md` the head interface (all under `/scratch/jjyeung/orch_cd/vla_libero/`).

**What the kit is.**
- The stack: StarVLA 985c2238 with the pilot's overlay, plus LIBERO and LIBERO-Plus. Everything was reinstalled from upstream at the October pilot's pinned hashes, because nothing of the pilot's stack survived. Rendering is OSMesa, because the compute nodes have no EGL device.
- The data: the four no-noops LeRobot suites at pinned revisions, with fixed subsets d1, d5 and d50 per suite (seed 0). LIBERO-Spatial's lists equal the pilot's, so `d5_s0` is 50 demos and 6,281 frames.
- The recipe (`arm_testL.yaml`, schema 10): seed 17, LR 3e-5 for the LM and 3e-4 for the head, warm-up 3%, cosine to 1e-6, batch 64, 10k steps, exports at 1k, 2k, 5k and 10k, full state every 500 steps.
- The trainer (`vl_train.py`) wraps StarVLA's. It builds the model under `set_seed`, samples by step index (the same batch stream for every arm), resumes the full state exactly, and keeps two alternating state slots. It stops itself on a non-finite loss or a slow step, and its per-step trace records the gradient norm, memory, gate norms and batch fingerprints.
- The data patch (`vl_data_patch.py`): every frame is a chunk start, steps past the episode end are masked with the last action repeated, and the sample at index i is always the same.
- The head (`vl_heads_hook.py`): vla_heads' head (a) in StarVLA's OFT configuration, with 8-D proprio (min-max over the subset) through a zero-initialised map and the gripper regressed as g = 1 − 2·a6. The prompt is template `starvla_qwenoft_985c2238_v1`, with its sha256 in every run and server log. The policy server (`vl_server.py`) loads the same hook.
- The launch and readout:
  - `train_arm.sh`: `B1 d5_s0 1000` is the shake-down (100 paired episodes) and `B1 d5_s0 10000` the decisive run. The job never requeues and runs an in-job stall watch.
  - `eval_plan.sh`: 500 paired episodes at 10k; 200 at each of 1k, 2k and 5k; 376 LIBERO-Plus camera tasks; both blind priors.
  - `compare_arms.py`: task-stratified bootstrap and exact McNemar; GAIN or HARM on the 95% CI, EQUIVALENT on the 90% CI inside ±3.
- Supporting tools: `libero_render.py` writes renders with depth, segmentation, intrinsics, extrinsics and GT for vla_where and dyn_probe (`out/renders_v2`). `conformance.py` runs T-4, T-5 and T-6 and fits the hand-eye transform (`kit/hand_eye.json`).

**How it was tested.**
- CPU, tiny Qwen3.5 on real frames:
  - HOOK_OK: step-0 loss parity with StarVLA's head, a masked tail chunk, proprio gradients and a strict server reload.
  - HOOK_RESUME_EXACT and REPEAT_EXACT: resumed and repeated runs are bitwise equal.
- Parity (`parity_check.py`): the eval state equals the LeRobot state exactly after 10 settle steps; the eval client's `raw[::-1, ::-1]` matches the training images; all 40 instructions equal training strings. The eval client's BILINEAR resize was replaced by the loader's PIL call.
- Conformance:
  - T-4: 19/20 wrist projections land in the GT mask. The hand-eye translation is (0.050, 0.000, −0.097) m with residual 6e-8 m.
  - T-5 passes.
  - T-6 passes, with per-axis correlations 0.932, 0.970 and 0.962.
- Closed loop: random policy 0/10, demo replay 10/10.
- GPU (stock head, 1 H100 with optimizer offload): B0 168293 and B1 168298 pass first batch, steps and resume. Peak memory is 53.2 GiB at batches 4 and 16 alike. The policy server ran an episode inside the job.
