# C1 carrier-pose placement sweep: arms and gates (heads_up5, 2026-11-08)
- Question: with pose read from LM final-norm states at per-frame CAM tokens (Cambrian-P style, pose-only, LM trainable), which placement lets the head read per-frame pose?
- Arms (identical recipe, rows, seed 17; only placement differs): C1-a CAM_k after frame k (causal); C1-b all 32 CAMs after the video, with frame embeddings and frame-grid RoPE (without them it failed the 200-step guard); C1-c = C1-a plus a bidirectional prefix mask in the full-attention layers only (Gated DeltaNet stays causal).
- Gates: CPU overfit guard A 7.57 / B 18.77 deg on AWS. C fails on AWS CPU (37.84; kernel-fragile) but passes on GPU (bf16 9.04 deg; A control 9.83). The GPU mask check reaches the kernel: earlier-CAM delta A 0.0 vs C 0.268. Independent review train_review/C1_REVIEW.md: GO for spread.
- Prior result: A1 (decoupled single-frame-feature head) FAILED m400 at 80.9 deg vs the 39 bar, so dense labels alone did not close the gap; the bottleneck is the features.
- Status (16:06Z 11-08): C1-a trains toward 800 steps as the pose specialist (m200 rotation mean 39.5 deg). C1-c lost the m200 paired read and stopped at step ~217. C1-b stopped at step ~153.

## Layout decision (orchestrator 12:00Z, 11-08)
- The sweep runs C1-a/b/c in the DUPLICATE layout (each viewpoint fed twice; one viewpoint per temporal patch) on the B43/B45/B46/B48 trainer line. It is unfused like P0.5 and needs no partner frames. FP1 middle layer: D 75.2, P0.5 68.1, spread 88.0 deg. P0.5 is held back: the partner job refused anchors past recording ends, and its decode plan (~14 M frames over 3,509 recordings) took far over 1 h. Partner job v2 (keyframe seeks, -0.5 s partner at recording ends) serves the final run and a possible P0.5 confirmation.
- Readouts use the same layout as training (shared readout-layout bug, C1R_REVIEW B3, fixed in B48).

## Placement verdict (m100-m150, duplicate layout, trainer 6f974710): a > c > b; C1-b stopped
| Arm | m100 rotation median (even gate, 608 slots) | m100 centre median | Loss ratio to the no-pixel constant: m100 / steps 131-150 |
|---|---|---|---|
| C1-a (CAM after each frame) | 47.0 deg | 1.26 m | 0.736 / 0.644 |
| C1-c (C1-a + bidirectional full-attention mask) | 66.7 deg | 1.68 m | 0.879 / 0.703 |
| C1-b (all CAMs after the video + frame embeddings) | 91.4 deg (chance) | 1.61 m | 1.039 / 1.001 |
- C1-b does not read frames. Its losses track the no-pixel constant row by row (r = 0.99 at step ~78). Its frame embeddings are distinct, so the bottleneck is architectural: only 1 layer in 4 (full attention) can point an appended carrier at its frame. Sources: heads_up event 20261108T1440Z (readouts 107440-107442), loss_doctor 1429Z and 1503Z.
- Stopped 15:04Z on 11-08 (job 105290 at step ~153; leg 105470 cancelled). Kept on code-aws: runs/b343b001/m100/ and the resume state checkpoint_000134_6e883ce9e553433f98df72cec7af334d (root ap/7b30c1e4).

## m200 paired read: C1-a wins; C1-c stopped (16:03Z 11-08)
| m200 | Even-gate rotation mean / median (all; ScanNet; ScanNet++) | Centre mean / median |
|---|---|---|
| C1-a | 39.5 / 26.5; 36.5 / 23.9; 42.2 / 28.0 deg | 1.38 / 0.99 m |
| C1-c | 48.7 / 35.1; 49.3 / 35.6; 48.1 / 34.3 deg | 1.62 / 1.10 m |
- Paired per scene (C1-c minus C1-a, 90% bootstrap CI): rotation +9.2 deg [+5.6, +12.8], centre +0.22 m [+0.13, +0.31]; worse in both datasets. Readouts 108971/108972 (o/<job>.5.json), summarized by heads_up h6/readout_summary.py.
- Why C1-c stalls (loss_doctor 1553Z): its carrier-token gradient grew to ~55% of the heads' squared norm under the joint clip, and its loss ratio has been flat at ~0.60 since step ~155. C1-a's carrier norm stays ~0.45.
- C1-c stopped at step ~217 (kept: runs/b343c001/m200/, checkpoint_000213_ca212c94...). C1-a continues as the pose specialist and is the duplicate control for C1-a-sw. Its step-170 state is pinned at ap/7b30c1e4/pin/a170 (hard links) for the C1-a-sw fork.
- Lever arms on C1-a (heads_up6), in priority order: C1-a-sw forks C1-a's step-170 state into the P0.5 layout and trains to m400 (the switch test; FRAME_DENSITY_DESIGN_20261108.md); C1-a-p trains P0.5 from base over steps 1-200 (ablation); C1-a-ei starts the CAM carriers at real-embedding scale (`carrier_init: text_mean_v1`, trainer 50566e81; prep done). They run in separate kit roots (paired arms ap/a5ed51d1, C1-a-ei ap/01c9cbad), because receipts bind the trainer commit and root ap/7b30c1e4 must keep serving C1-a's 6f974710 legs.

