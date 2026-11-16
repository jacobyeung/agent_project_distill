# C1 memory fallbacks and frame layouts

`skip_unsupervised_lm` defaults to false in both training modes, preserving the
smoke-proven zero-valued LM-head dependency. Set it to true explicitly in the
configuration to enable lever A. When no shifted label is supervised, the enabled
pose path never calls `lm_head` or computes an LM loss. CPU tests compare loss, states, gradients
and updates bit-for-bit for arms a/b/c. The unused LM head has `grad=None`:
AdamW neither decays its weights nor creates its gradient/moment state. The old
zero gradient did decay those weights. Already restored optimizer moments are
not discarded. Supervised VQA/pointing behavior stays unchanged.

Set `C1_FSDP_CPU_OFFLOAD=1` on every training rank to request
`CPUOffload(offload_params=True)` with the existing FULL_SHARD wrap. The default
is 0. Base masters, reduced gradients and their Adam state live on CPU;
replicated pose/private-depth parameters remain on the compute device. Four
microbatches still reduce independently. The trainer explicitly sums CPU
shards because FSDP overwrites its CPU gradient buffer between backward calls;
it never uses `no_sync`. NCCL clipping transfers only the norm scalar to CUDA.
The checkpoint, restore and export formats stay unchanged; each rank's metrics
record whether offload was enabled. Offload can change timing substantially.

Every rank's step metrics contain `memory.microbatches`, with zero-based
microbatch index, stream, `after_forward`, `after_backward`, and peak allocated
and reserved bytes. Phase snapshots contain `allocated_bytes` and
`reserved_bytes`. `memory.after_optimizer_step` records the final snapshot.
Peaks reset before each microbatch; the top-level step peaks retain the largest
microbatch or optimizer peak. CPU metrics contain zeros and call no CUDA memory
API. These are allocator measurements, not device-wide usage measurements.

Choose `frame_layout` in the frozen run configuration before preparation:

| Layout | Processor input for sampled views A, B | C1-a / C1-c positions | C1-b positions |
| --- | --- | --- | --- |
| `spread` (default) | A, B | Two CAMs after each fused-pair patch | All 32 CAMs after the last video patch |
| `duplicate` | A, A, B, B | One CAM after each view's own patch tokens | All 32 CAMs after the last video patch |
| `paired` | A, A+g, B, B+g | One CAM per anchor/partner patch, targeting the anchor | All 32 CAMs after the last video patch |

Explicit `spread` and an omitted layout have the same configuration identity;
the original encoder and tensor bytes remain unchanged. Other layouts bind
different identities and are carried through preparation, training, frozen
readout, clip evaluation, and artifact validation. Each C1-b CAM retains its own
viewpoint's learned frame embedding and frame-grid RoPE anchor at that viewpoint's
first visual token, including when duplicate/paired CAMs form the appended tail.
Private depth uses one target slot per patch in non-spread layouts. Target
order and the 32 original viewpoint labels never expand or change.

Duplicate expands RGB **after** augmentation so both halves of each temporal
patch are identical. Source frame indices repeat; fps and recording length do
not change. Native timestamp averaging therefore yields each original view's
true timestamp. No frame sampling or timestamp renumbering occurs. The per-frame
pixel budget stays fixed, so 32 viewpoints become 64 processor frames and 32
temporal groups, approximately doubling visual tokens. This increases memory.

Paired requires positive `frame_pair_gap_seconds` and prepared
`student_input.recording_id` plus `student_input.partner_frames`, one entry per
sampled anchor in the same order. Each partner entry contains `path`, `sha256`,
`recording_id`, `frame_index`, and `timestamp`. Its index must be in the source
recording, later than the anchor, and its timestamp must equal index/fps and
anchor timestamp + g (within 1e-6 seconds). Preparation refuses missing,
unpinned, mismatched-recording or mistimed partners; it does not invent them.
Both source timestamps reach the processor; the native fused-patch timestamp
is their midpoint. Paired held-out/clip rows need the same partner schema.

Memory estimates for eight ranks, FP32 masters/gradients/Adam moments, BF16
compute, and one row of approximately 2,312 tokens per microbatch:

| Lever | Estimated GPU allocation reduction per rank |
| --- | --- |
| A: omit unsupervised LM head | 1.421 GiB steady gradient + moments; also avoids a 1.895 GiB BF16 head all-gather and its backward temporaries |
| B: CPU offload, after A | About 15.47 GiB of base masters + gradients + moments moved to CPU |
| B alone | About 16.89 GiB moved to CPU |
| duplicate/paired | No saving; twice the visual tokens, with attention-dependent activation growth |

These estimates use the library's Qwen3.5-9B configuration: 9,407,453,936 base
parameters, 8,953,803,264 trainable LM parameters, and an untied
248,320 x 4,096 head (1,017,118,720 parameters). A saves
`12 * head_parameters / 8 / 2**30`; B after A moves
`(4 * base_parameters + 12 * (lm_parameters - head_parameters)) / 8 / 2**30`.
Verify those counts against the deployed snapshot. The existing pose code
computed only **one token** of logits (~0.00046 GiB BF16), not 2,312 logits;
claiming a full-sequence logits saving would be incorrect. Peak reductions
depend on overlap and allocator reuse and cannot be added to steady reductions
as a measured fit claim. CPU accumulation adds about 3.70 GiB host RAM per rank
after A, beyond offloaded tensors. Replicated heads, activations and live
all-gathers remain on GPU; reserved memory need not fall by the estimated amount.

CPU coverage includes native video patch packing/timestamps, all-arm pose and
depth backward/generation, phase metric resets, partner preparation refusal,
CPU accumulation equivalence, scalar transport, checkpoint/resume/export, and
an optional two-rank gloo FSDP offload fixture. That fixture substitutes only
`Tensor.pin_memory` on CPU builds; it cannot measure PCIe transfer or CUDA fit.


The `c1-paired-prefix-v2` store retains the original 283,200-index sampler
population and source IDs. It covers the first 25,600 seed-17 samples plus up to
2,560 margin samples; preparation rejects missing required IDs, reordered IDs,
extra database rows, changed targets, anchor hashes, or source metadata. `Rows`
raises `Missing planned C1 row` for requests outside the admitted prefix.

For P0.5, bind `streams.pose` to the partner job's manifest path and SHA-256,
set `frame_layout="paired"` and `frame_pair_gap_seconds=0.5`, and copy its
`readout` bindings. The training manifest needs the 38-scene sparse bank but
can omit `contiguous_clips`. A later clip job supplies that pin without changing
the training identity or prefix manifest. Preparation checks the late clip pin,
38-scene coverage, disjoint training scenes, and partner pixels/metadata.
The m400 gate still requires both sparse and contiguous readouts.
