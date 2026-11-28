# Lane: build_run_c2_sam3_lora (KT-4 Grounding Breaker: C2 SAM 3 Native-Res Detector/Presence LoRA Pilot)

## Scientific Motivation (Backed by Live `KT-1a` `J1-T` Proof!)
Our full 46-capture `J1-T` diagnostic (`result_kt1_j1t_da3_full.md`) just proved two huge facts:
1. GT boxes -> frozen `SAM 3` mask decoder recovers **`+11.03 [+0.66, +20.90]`** MRA on `DEV-MASK 117` (`80%` of the `+13.76` GT-mask ceiling), while deleting `SAM 3` (`k_notower`) loses `-9.06` (`NO-GO`).
2. **Low-precision boxes FAIL:** `IoU 0.50` boxes **BREAK (`-3.68 pp`)**, missing `<1%` small objects **BREAKS (`-7.09 pp`)**, and false-positive box spam **BREAKS (`-4.27 pp`)**!
- **Why `C2` (`SAM 3` Detector/Presence LoRA Fine-Tune) Is Now Our #1 Grounding Lever:** `SAM 3` ALREADY operates at native high resolution (`1008×1008`, seeing `<1%` small objects crisply!) and its mask decoder is already strong — it fails ONLY because its frozen text/presence front-end self-vetoes **`92%`** of empty visible frames (`presence < 0.05`) and mis-ranks indoor names! Fine-tuning `SAM 3`'s detector/presence front-end (`LoRA` on text-vision cross-attention + presence/scoring head) on our **`233` clean K1 train rooms (`0` overlap with `K1-heldout` / `DEV-MASK 117` / `dev-S1` / `R0-dev` / `BENCH v2`!)** directly attacks BOTH small-object recall AND FP precision!

## Ground-Truth Inputs to Read First (Exact Paths Only)
1. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_kt1_j1t_da3_full.md` (lines 1–80)
2. `/data2/jjyeung/agent_project_data/distill_design/MASK_QUALITY_DESIGN_20261119.md` (read the `C2` / `sam3ft` section only via `rg -n` + bounded `read`!)
3. Check `/scratch/jjyeung/orch_home_distill/work_e03_e04/run_e03_j1t_smoke.py` to see exact local `SAM 3` weights, env (`/scratch/jjyeung/envs/sam3_capretry_native_v1`), and how `DEV-MASK 117` is scored cleanly!

## Hard Cluster, IO & Safety Rules (MANDATORY)
- **STRICT ZERO LEAKAGE:** Enforce the exact same `RoomExclusionGuard` from `/scratch/jjyeung/orch_home_distill/spatial_v2/data_k1_local.py` (`233` clean train captures / `214` rooms ONLY; strictly `0` overlap with `DEV-MASK 117` [`46` captures / `35` rooms], `K1-heldout` [`53` captures], `dev-S1`, `R0-dev`, `BENCH v2`!). Assert `0` overlap at startup!
- **Compute & Disk Rules:**
  - Build & unit-test on `trinity-2-28:/scratch/jjyeung/orch_home_distill/work_c2_sam3/` (`1.8 TB` free!).
  - **GPU selection:** Check `trinity-0-13` GPUs `0, 2` (UNWRAPPED! Only if `sam3_capretry_native_v1` or `sam3` env + weights are accessible cleanly without heavy NFS IO — **NEVER write >2 GB to `0-13:/scratch` [69 GB free]!**), OR check `trinity-2-28` GPU `4`/`6` (`vnice.sh`, check `nvidia-smi` first so you NEVER collide with `Arm A` on `5`, `Arm B` on `7`, `Arm C` on `4`, or `VLA prechecks` on `6`, and NEVER touch `0..3` [`mgaur`]!). Actually, if `0-13` GPU `0` or `2` is free and can read `/scratch` or run locally with `<1 GB` checkpoint saved back to `2-28` via `.ib`, `0-13:0` is UNWRAPPED and fast! Otherwise check `trinity-0-18:4` (`vnice.sh`) or wait for GPU `6` on `2-28`! (Prefer `2-28` GPU `6` once `launch_trinity_vla_prechecks_r3` finishes its ~3 min `T-11` check, since ALL K1 frames & `SAM 3` env are ALREADY local on `2-28:/scratch` with **0 MB/s NFS**!! Check `nvidia-smi` before launching GPU training!).
- **ZERO DELETIONS**, **NO GIT COMMANDS**, **NO broad NFS scans**.

## Exact Execution Plan
1. Inspect `SAM 3` model modules in `/scratch/jjyeung/envs/sam3_capretry_native_v1` (identify exact vision-text fusion, query decoder, box/presence head layers, and whether frozen-backbone + trainable/LoRA detector+presence head fits in `<20 GiB` VRAM!).
2. Build `work_c2_sam3/train_c2_sam3_lora.py`:
   - Trains lightweight LoRA (`r=16`) on `SAM 3`'s text-vision cross-attention + presence/scoring head (keeping image backbone & mask decoder frozen so `<15 GiB` VRAM and zero catastrophic mask forgetting!) using exact GT masks & boxes from the `233` clean K1 train captures (with hard scene-absent negatives so presence precision stays `>=90%` and FP spam doesn't trigger `kP-fp`!).
   - Evaluates **Step 0 (frozen `SAM 3` baseline)** -> **Post-LoRA** on `K1-heldout` (`53` rooms: frame-level presence AUROC, `<1%` small-object recall, box `IoU>=0.70` recall, FP rate) AND runs the paired **`DEV-MASK 117`** distance-MRA read against baseline `a` (`55.81`)!
3. Run a **fail-fast pilot** (`~1–2 hours` max on 1 GPU, evaluating at step `250`, `500`, `1,000`; stop early if `K1-heldout` presence AUROC or `IoU>=0.7` recall doesn't improve!). Check GPU liveness + loss every 1 min -> 5 min.

## Deliverable
Write a crisp, quantitative result report to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_c2_sam3_lora.md`
Include: zero-leak room assert, trainable param count & VRAM, Step-0 vs LoRA `K1-heldout` presence/recall/IoU>=0.7/FP breakdown (including `<1%` small objects!), and paired `DEV-MASK 117` MRA delta vs `a` (`55.81`) & `J1-k` (`+11.03`), plus `GO`/`NO-GO` verdict (`GO` bar: `>= +5.0` to `+7.0` paired MRA over `a` with `LB > 0` and refusals `<= 6%`). Print a <=18-line summary to stdout.
