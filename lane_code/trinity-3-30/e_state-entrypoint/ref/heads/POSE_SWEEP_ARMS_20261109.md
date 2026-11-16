# Pose sweep: readout, resolution and representation arms against the 49% centre plateau (2026-11-09)

## Question
Held-out camera-centre error stays at ~49% of distance for f17, C1-a m800 and T0 (~20 deg translation direction, worst on short paths). The user asks whether one camera token per frame is too narrow, whether the pose head should read all image tokens, whether more pixels per frame help, and whether rotation and translation should be represented together or separately. Which arms test these, and against which control?

## Answer
- **The direction error lives in t itself, not in the rotation coupling.** The harness centre is c = -R^T t from the code E_g = inv(C_g) C_0 = [t, q xyzw, FoV]. On the 312 ScanNet harness scenes (C1-a m800, |c| > 0.2 m), predicted t with GT rotation gives 19.6 deg (full 20.1); GT t with predicted rotation gives 12.3. Short paths: 26.6 deg from t alone. |t| shrinks to 0.86x. T0 m200: 17.7 of 20.0 (`pose_sweep/work/diag/dir_decomp.py`).
- **HEADATTN needs no arm.** The CPDM head already is Cambrian-P's VGGT head: carrier final states -> Linear(4096->2048) -> 4 bidirectional self-attention blocks across the 32 frame tokens, adaLN pose modulation, 4 refinements (`camera_head.py` CameraHead).
- **Arms (each a `pose_arm` config switch on the C1 trainer; absent = control, byte-identical):**
  - **CTRL:** C1-a m800 warm start (LM full + pose head), C1-a recipe (LR 1e-4 heads, 1e-5 LM/encoder, warmup 3%, cosine, wd 0.01, clip 1, seed 17, B 32, world 8, duplicate layout, placement a), 300-step horizon, milestones 100/200/300, A1 rows continuing C1-a's seed-17 order after its 25,600 rows (`row_start_step` 800), fla kernels. Shared with gx_build's GXC (gx_build agreed 05:46Z).
  - **RES2:** per-frame pixel budget 128^2..640x480 (A1 frames are native 640x480): 300 instead of 140 merged tokens per viewpoint, ~9.8k tokens per row. Step 0 differs (same weights, sharper input).
  - **DIR:** translation term = 0.5 x chordal |t_p/|t_p| - t_g/|t_g|| + 0.64 x |log((|t_p|+0.01)/(|t_g|+0.01))| where |t_g| >= 0.05 m, the control L1/dbar term otherwise. The weights match the control term's mean at C1-a m800 (chordal 0.529, log-mag 0.412, L1/dbar 0.526; `diag/dir_scale.py`).
  - **PAIRS:** the same outputs, plus a relative-pose L1 over all 496 frame pairs per row (R_ij = R_j R_i^T, t_ij = t_j - R_ij t_i), weight 1.
  - **CPARAM (ORCH 0549Z):** translation supervised as the frame-0 camera centre c = -R^T t with R detached, plus a zero-init centre-space residual read from each refinement stage's trunk (t_out = t_raw - R residual). Step 0 equals the control head bitwise.
  - **DR:** 8 learned queries per frame cross-attend (dim 1024, 8 heads) to that frame's visual-token final states plus its carrier; a zero-init Linear adds the result to the CPDM input. Step 0 identical.
  - **MC8:** 8 carriers per frame (extra 7 embeddings = c_rest + zero-init offsets), attention-pooled into a zero-init residual on the CPDM input. Step 0 differs (224 extra tokens in the sequence); the head adds nothing beyond the primary carriers at init.

## Pre-registered bar (each arm vs CTRL at matched steps, m200 primary, evalx 312-scene harness, `tp/centre_split.py`, paired per scene, 90% bootstrap CI)
GO needs all of: direction median <= 0.85x CTRL's; raw centre/distance <= 0.85x; rotation median <= 1.10x; CI of the paired direction difference < 0; and the short-path tertile direction gain >= the all-path relative gain (mechanism). Report m100 as supporting only. RES2 and MC8 also report step time and peak memory.

## Options considered and rejected
- HEADATTN build: rejected, it exists (see above).
- Replaying C1-a's first rows: rejected for continuing its order; the control and every arm see identical new rows.
- A pure centre output (head slots reinterpreted as c): rejected for the residual form, because reinterpretation breaks the warm start at step 0.
- Per-arm 800-step horizons: rejected; 300 steps fit one 4-h allocation at ~30 s/step (fla) and anneal by m300.

## What might not work and how we would notice
- The fresh LR cycle on an annealed m800 may first raise pose error; CTRL measures exactly this, and every arm is read against CTRL, not against m800.
- RES2 may not fit memory at ~9.8k tokens (C1-a peaked 39.8 GiB at ~4.6k); the run logs peak memory per microstep.
- DIR's direction term is ill-defined for tiny |t|; the 0.05 m floor hands those groups to L1.
