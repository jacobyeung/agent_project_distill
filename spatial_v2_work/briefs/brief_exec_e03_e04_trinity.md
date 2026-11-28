# Lane: exec_e03_e04_trinity (Immediate Trinity GPU Kill-Test Builder: E03 Grounding + E04 DA3/TT-BA + Geo-Maj@K)

## Mission
We have **6 free 49 GB RTX 6000 Ada GPUs RIGHT NOW** (`trinity-0-13:0,2` unwrapped + `trinity-2-28:4,5,6,7` under `vnice.sh`, plus `trinity-0-13:6` in ~30 min and `trinity-0-18:4..7` under `vnice.sh`).
Your mission: locate the exact existing local assets/code on `trinity-2-28` (`/scratch/jjyeung/...`) and `/home/jjyeung/agent_project_distill` / `/home/jjyeung/agent_project`, and **build & CPU-test runnable, self-contained kill-test scripts** under `/scratch/jjyeung/orch_home_distill/work_e03_e04/` for our three fastest, highest-EV Trinity GPU wins:
1. **`E04-A` (Zero-Training `DA3-Nested` + 5-Step Levenberg-Marquardt `TT-BA` + `K5-S` Uncertainty Gate):** Runs on existing `dev-S1` (`38` GT captures incl. `23` ARKit where `G3T` failed `21/23`!) and `K1-X` (`n30_mirror/lever1/` on `trinity-2-28`!). Proves whether `DA3-Nested` + `<20 ms` `TT-BA` slashes ARKit `>15°` pose failures by `>=50%` and beats `G3T x s` on distance + room MRA without a single training step!
2. **`E03-A` (`J1-T` Box-Tolerance Diagnostic + `C3+` 2D Box/Presence Head Prototype):** Uses existing `lever1`/`lever8`/`lever9`/`lever10` K1 caches ALREADY on `trinity-2-28:/scratch/jjyeung/orch_n30/` (look! `lever8`, `lever9`, `lever10`, `k1`, `k1_frames` are RIGHT HERE on `trinity-2-28:/scratch`!!). Verify `J1-T` (~10 GPU-min on `0-13:0` or `2-28:4` under `vnice.sh`!) and prepare the clean `C3+` 2D box+presence head -> frozen `SAM 3` mask decoder trainer!
3. **`Geo-Maj@K` Zero-Training Probe (Bonus, <2 GPU-h):** Checks whether our existing `K1` / `dev-S1` predictions + `K5-S` stability + mirror/subset geometric consensus beats single-pass geometry on ARKit & distance MRA!

## Hard Cluster, IO & Safety Rules (MANDATORY)
- **ZERO DELETIONS** (`rm_guard`), **NO GIT COMMANDS**, **NO broad NFS scans** over `/home`/`/data*`.
- **Inspect local `/scratch/jjyeung/` on `trinity-2-28` FIRST** (fast NVMe, 0 NFS cost!): check `ls -la /scratch/jjyeung/k1 /scratch/jjyeung/n30_mirror/lever1 /scratch/jjyeung/orch_n30/lever8 /scratch/jjyeung/orch_n30/lever9 /scratch/jjyeung/orch_n30/lever10 /scratch/jjyeung/geo_bakeoff_kit`.
- Check what `DA3`, `SAM 3`, and `G3T` python envs/weights are locally available on `trinity-2-28` (`/scratch/jjyeung/envs/`, `/data2/jjyeung/envs/` — explicit `ls -1` only!).
- Read `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_ttba_scale_calibration.md` (if present), `w2_native_grounding_3d.md`, and `w1_heads_bottlenecks.md`.
- **DO NOT launch heavy GPU training without CPU unit tests passing first**, EXCEPT you MAY run a quick `<2 min` single-GPU smoke test on `trinity-2-28` GPU `4` wrapped in `/data3/shared/scripts/vnice/vnice.sh` (`CUDA_VISIBLE_DEVICES=4 /data3/shared/scripts/vnice/vnice.sh ...`) to verify `DA3` / `SAM 3` / `J1-T` imports & 1-scene forward pass work cleanly! NEVER touch GPUs `0,1,2,3` on `trinity-2-28` (`mgaur`).

## Deliverables
1. Runnable scripts + CPU unit tests under `/scratch/jjyeung/orch_home_distill/work_e03_e04/` (`ttba_lm.py`, `run_e04_da3_ttba.py`, `run_e03_j1t_smoke.py`, `test_ttba_synthetic.py` — ALL tests passing!).
2. Crisp report (max ~160 lines) at `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/exec_e03_e04_trinity.md` documenting:
   - Exact local paths of K1 / `lever10` / `DA3` / `SAM 3` / `geo_bakeoff_kit` assets verified on `trinity-2-28`.
   - Synthetic `TT-BA` unit test results (convergence on perturbed SE(3) + 1.94× scale drift + outlier rigidity mask, measured wall-clock ms!).
   - Exact 1-line `vnice.sh` (`2-28:4..7`) and unwrapped (`0-13:0,2`) launch commands ready to run `J1-T` (10 min), `E04` `DA3+TT-BA` (2–4h), and `C3+` box head (`6h`) immediately!

Print a concise <=18-line summary to stdout when done.
