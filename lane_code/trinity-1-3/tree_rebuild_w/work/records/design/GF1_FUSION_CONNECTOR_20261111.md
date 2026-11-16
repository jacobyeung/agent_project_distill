# GF-1 / B2: geometry features into the language model

## Question

Does a zero-initialized connector from frozen G3T features improve the current student's direct spatial answers before the LM adapts?

## Answer

The local implementation adds GF-1 to the current C1/GXC training and decoding path. Its default bank uses zero-based aggregator indices 11/17/23. Each layer has LayerNorm and a linear projection. Exact area integration maps the valid G3T image region to the Qwen merger grid, then a layer sum and zero-initialized output matrix produce the residual. An optional per-token top-2 router selects from layers 12–23. `pre_lm` injects after the visual merger; `lm_012` injects three bank layers at decoder layers 0/1/2.

G3T runs without gradients on the dense clip. The LM uses explicit nested frames, including the first dense frame. Dense and sparse paths share the same augmented RGB bytes at those positions. A row-owned cache shares frozen features between a routed prefix read and the supervised forward; the supervised call releases the cache reference so prefetched rows cannot accumulate GPU banks. The routed head tower shares the registered aggregator and camera heads after checking asset pins, device and dense-frame count. Its retained layer bank feeds GF-1 directly; routed depth/point heads and fusion use one reconstruction. Shared inference tensors become ordinary detached tensors before connector backward. Connector checkpointing recomputes projection and pooling, not G3T. Permanent decoder hooks receive per-call residuals through checkpointed kwargs. Cached generation injects only during prefill.

The GXC camera-token and pose9 path remains in place. Stage 1 freezes that path and all existing parameters; only GF-1 trains. A nonzero inherited camera connector requires the donor's dense context and tower precision, and its saved RMS scale remains intact. A change in that context refuses initialization because a zero GF-1 matrix alone cannot preserve the checkpoint's logits.

## Base and scope

The base is `/scratch/jjyeung/orch_cd/integ_v3/work/tree`, selected because it contains the newest native C1/GXC model, trainer, generation, full-FT checkpoint implementation and CPU fixtures. `out/BASE_MANIFEST.json` pins its bytes. `work/tree_gf1` is the changed copy; `work/tree_baseline` is a private baseline verification copy. No Git, SSH, GPU training or external publication was used.

Integration changes affect `carrier_c1.py`, `g3t_online.py`, `carrier_c1_data.py`, `carrier_c1_sweep.py`, `carrier_c1_run.py`, `full_ft.py`, `tower_read.py` and `_tower_native.py`. They are opt-in through `geometry_online.gf1`. The final C1 runner is the active model/trainer path; the older generic adapter trainer is not the integration point.

Stage 1 admits world size 1 with a frozen BF16 base. Stage 2 admits world size 4, full LM fine-tuning and the inherited head recipe. The Qwen ViT stays frozen, as in the base recipe. The FSDP constructor now explicitly admits frozen FP32/BF16 bases without relaxing the FP32-master requirement for full fine-tuning. Empty frozen gradient groups report zero and avoid a CPU-tensor NCCL reduction.

## Evidence and tests

The CPU environment uses Torch 2.10.0 and Transformers 5.12.1, CUDA hidden, offline loading and one CPU thread. Native tiny Qwen3.5 and native tiny G3T perform the numerical forwards. Fixture dimensions are reduced; the stage files supply the stage, world size, learning rate and schedule.

`out/ACCEPTANCE.json` contains final acceptance counts and evidence paths. The final GF-1 set passes 18 tests. The combined GF-1/head-tower run passes 36 of 39 tests and skips three unavailable live-input checks. The affected-module run passes 146 of 149 tests and skips three socket-dependent checks. The tests cover exact step-0 logits, both injection modes, patch/ROI alignment, all four streams on each logical rank, connector-only gradients, nonzero upstream projection gradients after the output matrix opens, router gradients, BF16 frozen-base forward/backward, checkpointed decoder gradients, native cached generation and dense/sparse RGB identity.

The native `optimize_step`, `checkpoint` and `restore` functions execute for Stage 1 rank 0 and Stage 2 ranks 0–3. Step 3 after resume matches uninterrupted model tensors, optimizer state and losses exactly. Collectives are mocked and ranks execute serially: these checks do not prove real FSDP communication, sharding or GPU behavior. The separate basic serializer check also compares complete optimizer state.

Full existing-suite discovery is **not green**. `out/SUITE_COMPARISON.json` records the modified and pristine-base attempts. The untouched base reproduces every existing failure ID. Shared causes include the restrictive runner interrupting a Torch compiler import, unavailable external fixtures, legacy storage-root requirements, and forbidden subprocess/socket/deletion tests. `out/affected_suite.json` records the isolated checks of the affected model/trainer modules with the compiler loaded before the operational guard. Operational skips remain disclosed; they are not passes.

## Configs and launch

`configs/gf1_stage1.json` and `configs/gf1_stage2.json` describe the stages. `student_pilot.gf1_config` binds either stage onto the current pinned native run and preserves its global stream budgets. It requires current checkpoint/tower pins and dense row inputs; no live training manifest or checkpoint pin is fabricated. MDG/alignment combinations require a separate integration review. Existing preparation, source-seal and allocation checks remain in the launch path.

Stage 1 uses 1e-4 for GF-1. This is an explicit assumption from the existing head/adapter rate: the controlling design record gives no numeric Stage 1 rate. Stage 2 follows the actual LM learning rate, nominally 1e-5 multiplied by the source run's `lm_lr_scale`. The record wins where the brief differs. The 48 GB fit statement is treated as a planning estimate, not a measured admission result.

The two launch scripts retain stdout/stderr in a new log, monitor inactivity and terminate only their own launcher group on a stall. They never retry. They require a non-loopback compute-node address and the operator's allocation wrapper. No launcher was run on a GPU.

## Memory estimates

These are shape-based per-rank envelopes with a 20% reserve, not measured peaks. Assumptions: 9B base, 1.2B frozen BF16 tower, 0.5B own heads, LM width 4096 with 32 layers, 130 visual tokens/frame, 1,024 text/supervised tokens, memory-efficient SDPA and layer checkpointing. The default connector has 10,501,120 parameters. `out/MEMORY_ESTIMATES.json` gives every term and `student_pilot.gf1_memory` reproduces it.

| LM frames | Dense frames | Stage 1, world 1 GiB | Stage 2, world 4 GiB |
|---|---|---|---|
| 32 | 64 | 35.46 | 64.23 |
| 64 | 64 | 40.15 | 68.92 |
| 96 | 96 | 46.77 | 75.54 |
| 128 | 128 | 53.38 | 82.16 |

A frozen FP32 tower adds about 2.68 GiB including the reserve. Preserve donor precision for step-0 parity. These training estimates exclude eager quadratic attention, long tool traces, decoder-side residual buffers and the optional routed depth/point tower’s loading peak and retained head layers. The 96/128-frame entries are analytic extrapolations; the existing row/carrier/token limits do not admit every such training layout. The launch configs train at 32 LM / 64 dense frames. Native production exports still include full base weights; provision scratch accordingly.

## Options considered and rejected

- A scalar gate can remain closed; the controlling record reports PDG v3 gates at 0.0008–0.011 after 400 steps. GF-1 uses an output matrix that receives gradients at step 0.
- A nonzero random output can swamp the RGB signal; the record reports PDG v2 at 32.2 on VSI-500 m200. Internal projections initialize normally, but the output matrix is exactly zero.
- A single final-layer feature discards the requested multi-layer bank. The default uses three layers; the router is an explicit ablation.
- A vision-encoder replacement or 4D tower changes the experiment's question and is outside B2.
- A second G3T reconstruction for routed prefix reads wastes work and changes the shared-tower contract. Row-scoped frozen features serve both consumers.
- Silent sparse-frame duplication would falsely claim a dense reconstruction. Missing or mismatched dense inputs fail validation.

## Risks and how we would notice

Monitor step-1 loss above 1.02× step 0, early residual/visual RMS above 0.5, VSI-500 m50 below the checkpoint by more than 3 points, and held-out token loss above 0.99× step 0 at m100. Report per-type and per-corpus results. A null frozen-LM result does not settle whether fusion helps joint training. A wrong ROI/frame map can move geometry to another token; the synthetic patch and nested-RGB tests address that failure.

A trained GXC camera path with a different dense context cannot satisfy exact checkpoint identity through GF-1 zero initialization alone. The loader refuses it. Real-checkpoint parity, real-device memory, distributed FSDP behavior, production dense input coverage and benchmark gains remain unmeasured. The shared routed tower inherits the registered encoder’s storage precision; live GT/head parity still needs the unavailable real-input fixtures.

## Tests that settle the experiment and status

`out/PRELAUNCH_CARD.md` carries the FUS-1 rule: step-400 pooled direct gain at least +1.5 points, a paired scene-clustered 95% interval above zero, and no type below −5. The result decides whether LEG-S1 receives a trained connector, a zero-initialized connector or a redesign. The record estimates Stage 1 at 40–80 GPU-hours on 48 GB cards and zero H100-hours.

Status: implementation and CPU evidence are delivered; the complete legacy suite remains blocked by reproduced baseline/environment failures. Production bindings, GPU calibration and the independent Astra review remain pending. The inherited `AGENTS.md` assigns that reviewer to the orchestrator, so this lane did not launch another agent. No research score or measured GPU fit is claimed. The no-archaeology writing audit retained no borderline revision-history prose.
