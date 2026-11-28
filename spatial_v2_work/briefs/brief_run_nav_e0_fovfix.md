# Brief: Build & Run `Test N` Habitat `R2R-CE` `E0` FoV-Fix + `DA3` + `ScaleAnchor` Live Probe (`rand100`)

## Objective
Test our breakthrough `w2_ttba` hypothesis LIVE inside real Habitat 3D navigation (`R2R-CE` `rand100` using our verified `navrun` `controller_v2` CUDA-EGL harness):
- Prior `E0` diagnosis found `1.94×` Habitat depth drift on `V-C` (`step-544` depth head), hypothesized as a FoV mismatch (`V-C` trained on `~60°` narrow FoV vs `90°` Habitat: `tan(45°)/tan(29°) ≈ 1.94`).
- Measure directly on Habitat `R2R-CE` episodes:
  1. **Arm N-Baseline (`V-C` raw / existing `navrun` student depth baseline)** — measure metric depth error vs Habitat GT depth (median scale ratio, AbsRel, delta1) AND closed-loop `R2R-CE` `SR` / `SPL` / `NE` (`n=20` fast paired check first, then `n=100` `rand100` if clean!).
  2. **Arm N-FoVFix (`V-C` + focal/FoV scale correction `f_hab / f_train`)** — test whether analytical FoV correction alone eliminates the `1.94×` scale bias and boosts `SR`/`SPL`!
  3. **Arm N-DA3 (`DA3-Nested` depth+pose / `ScaleAnchor` with known Habitat camera height `h_cam = 1.25 m` or floor-plane anchor)** — test whether `DA3` (+ zero-GT camera-height `ScaleAnchor`) delivers accurate metric depth in `90°` FoV Habitat AND raises `R2R-CE` `SR`/`SPL`!

## Hard Rules
- **DO NOT touch `trinity-2-28` GPUs** (`4..7` busy) OR **`trinity-0-13` GPUs** (`0,2,6` currently occupied).
- **Assigned GPU:** Use **`trinity-0-8` GPU `3`** (`0%, 2 MiB` free, wrap EVERY GPU process in `/data3/shared/scripts/vnice/vnice.sh`) OR **`trinity-0-18` GPU `5`** (`0%, 1 MiB` free, `vnice.sh`).
- **CRITICAL `/scratch` cap on `0-8` (`38 GB` free) and `0-18` (`34 GB` free):** Check FIRST what already exists locally on `0-8` and `0-18` (`/scratch/jjyeung/`). NEVER write `>5 GB` to `0-8:/scratch` or `0-18:/scratch`! If `MP3D` + `nav_habitat024` only exist on `trinity-2-28` and are too large (`>10 GB`) for `0-8`/`0-18`, do NOT copy `>5 GB` — instead write the full diagnostic + `controller_v2` probe scripts in `/scratch/jjyeung/orch_home_distill/work_nav_e0_probe/`, run all CPU/offline checks + single-frame `DA3`/`V-C` Habitat depth-scale diagnostic using only the 20 cached/exported frames (`<200 MB`!) on `trinity-0-8:3` (`vnice.sh`), and prepare the 1-command `rand100` launch script ready for `trinity-2-28` the instant GPU `5` or `7` finishes `KT-6` (in ~15–20 min)!
- Zero deletions, zero `git`, zero broad NFS scans, zero touches to other users' or SPLIT's GPUs.
- Keep all new probe scripts in `/scratch/jjyeung/orch_home_distill/work_nav_e0_probe/` (never modify `navrun` in place unless in a local copy).

## Exact Steps
1. Read `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/launch_trinity_vla_prechecks.md`, `/scratch/jjyeung/orch_home_distill/work_vla_prechecks/run_nav_228.sh`, and `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_ttba_scale_calibration.md` (lines covering `E0` `1.94×` Habitat drift) to locate exact paths for `navrun`, `MP3D` scenes, `step-544` (`V-C`) weights, and `DA3` weights.
2. Check which of our assigned GPUs (`trinity-0-13:2` [unwrapped, watch `/scratch`!], `trinity-0-8:3` [`vnice.sh`], `trinity-0-18:5` [`vnice.sh`]) already has `MP3D` + `nav_habitat024` + `step-544` + `DA3` locally on `/scratch` (single batched SSH probe).
3. Run a **paired Habitat GT depth-scale diagnostic** on `20` `rand100` episodes (capturing Habitat RGB + GT depth + camera pose at every waypoint):
   - Measure `V-C` raw depth scale ratio (`pred/gt` median, IQR, AbsRel, `delta1`) — confirm whether the `1.94×` drift reproduces!
   - Measure `V-C` + analytical FoV-scale correction (`tan(hfov_hab/2) / tan(hfov_train/2)` and exact `fx_hab / fx_train`)!
   - Measure `DA3-Nested` (`da3nested-giant-large`) depth scale ratio + `AbsRel` + `delta1` on the exact same Habitat RGB frames, both raw metric `DA3` and `DA3 + ScaleAnchor` (ground-plane / known `h_cam=1.25 m` anchor, zero GT depth!).
4. Run **closed-loop `R2R-CE` `controller_v2` evaluation** on `rand100` (`n=20` first to confirm `0` crashes & wall-clock speed, then full `n=100`!):
   - Compare: (a) `oracle-depth` ceiling, (b) `V-C` raw depth, (c) `V-C + FoVFix`, (d) `DA3` (metric raw or `ScaleAnchor`), using exact same clicker (`oracle-click` first to isolate depth/3D lifting cleanly, plus student clicker if `step-544` clicker is wired cleanly in `navrun`!).
5. Verify every single metric directly from saved per-episode JSONL outputs (bootstrap 95% CI on paired `SR`/`SPL` diffs, `0` EGL crashes, `0` silent NaN fallbacks).
6. Write concise verified report to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_nav_e0_fovfix_da3.md`.
