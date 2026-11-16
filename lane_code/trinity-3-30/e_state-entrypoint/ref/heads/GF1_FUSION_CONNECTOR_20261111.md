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

