# Lane: launch_trinity_vla_prechecks (Trinity KT-1 VLA GPU Admission: navrun rand100 + vla_where + dyn_probe)

## Mission
Execute the **zero-training Trinity VLA GPU admission checks (`KT-1c`)** that unblock **Test N (`R2R-CE`)**, **Test L `U1` (`WhereProvider`)**, and **4D Dynamic Evaluation (`dyn_probe`)**, using our already-rescued `/scratch/jjyeung/preserved_20261128/b15_vla/` kits on `trinity-2-28` (`1.8 TB` free `/scratch`, GPUs `6, 7` FREE under `vnice.sh`) and unwrapped `trinity-0-13:0`!

## Hard Cluster, IO & Safety Rules (MANDATORY)
- **ZERO DELETIONS** (`rm_guard`), **NO GIT COMMANDS**, **NO broad NFS scans** over `/home`/`/data*`.
- **SHARED 30 MB/s NFS CAP:** Node-to-node transfers MUST use compute InfiniBand `.ib` tar pipes (`trinity-1-18.ib` -> `trinity-2-28`, **0 MB/s NFS**!). Never write >5 GB to `trinity-0-13:/scratch` (`69 GB` free).
- **GPU rules:** On `trinity-2-28`, ONLY use GPUs `6` or `7` (leave `4, 5` for `E03`/`E04`/`KT-6` and NEVER touch `0, 1, 2, 3` owned by `mgaur`!), ALWAYS wrapped in `/data3/shared/scripts/vnice/vnice.sh`! On `trinity-0-13`, ONLY use GPU `0` or `2` (unwrapped; NEVER touch `1,3,4,5,6`!).
- Do NOT overwrite sealed kit files in `/scratch/jjyeung/preserved_20261128/b15_vla` — create local wrappers/outputs under `/scratch/jjyeung/orch_home_distill/work_vla_prechecks/`.

## Exact Tasks
1. **`navrun` (`R2R-CE` Test N) Env Sync & CUDA-EGL `rand100` Smoke (`trinity-2-28` GPU `6`, `vnice.sh`):**
   - Check size of `trinity-1-18:/scratch/jjyeung/envs/nav_habitat024` (1 SSH call with `timeout 90`), and pull it over `.ib` (`ssh trinity-1-18.ib 'tar cf - -C /scratch/jjyeung/envs nav_habitat024' | tar xf - -C /scratch/jjyeung/envs`) into `/scratch/jjyeung/envs/nav_habitat024` (`0 MB/s` NFS!).
   - Inspect `/scratch/jjyeung/preserved_20261128/b15_vla/navrun/run.sh`, create a clean wrapper `/scratch/jjyeung/orch_home_distill/work_vla_prechecks/run_nav_228.sh` pointing to `/scratch/jjyeung/preserved_20261128/b15_vla` and `/scratch/jjyeung/envs/nav_habitat024`.
   - Run the full CPU unit test suite (`unittest`) AND verify MP3D Habitat scene paths (check whether scenes exist locally or on `/data3`) and run a **real GPU CUDA-EGL smoke test on `rand100` (e.g., first 5–20 episodes with oracle-click policy)** on `CUDA_VISIBLE_DEVICES=6 /data3/shared/scripts/vnice/vnice.sh` to confirm zero EGL/rendering crashes and measure `ep/min`!
2. **`vla_where` (`Test L U1`) & `dyn_probe` Audit + CPU Tests (`preserved_20261128/b15_vla/`):**
   - Inspect `/scratch/jjyeung/preserved_20261128/b15_vla/` directory tree (bounded `ls -la`, maxdepth 2) for `vla_where`, `vla_heads`, and `dyn_probe`.
   - Run their CPU unit test suites (`T-1..T-10` / `vla_where` 73 tests / `dyn_probe` 47 tests) using local `/scratch/jjyeung/envs/sam3_capretry_native_v1` (or `planner_local_v1`).
   - Identify exact GPU commands and input paths needed to run `vla_where` `T-11` (`P-5`) + `P-1..P-4` LIBERO replays and `dyn_probe` Stage 0 on `trinity-0-13:0` or `trinity-2-28:6..7`! If `vla_where` `T-11` (`bf16` parity) or `dyn_probe` Stage 0 has all inputs locally available, run a `<5 min` GPU smoke on `trinity-2-28` GPU `7` under `vnice.sh`!

## Deliverable
Write a crisp, verified admission receipt (max ~160 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/launch_trinity_vla_prechecks.md`
Include: `nav_habitat024` `.ib` sync status, `navrun` unittest + CUDA-EGL GPU smoke results, `vla_where` + `dyn_probe` CPU test counts, and exact 1-line commands to finish full `rand100` / `P-1..P-5` / `dyn_probe` Stage 0. Print a concise <=18-line summary to stdout.
