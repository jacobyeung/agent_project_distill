# Brief: `vla_where` `P-1..P-4` LIBERO Replays + `d5_s0` `WHERE_CACHE` Build (Prep for Orchard `U1`)

## Objective
Execute the pre-requisite LIBERO explicit-3D (`U1`) pipeline on Trinity so that Orchard `4× H100` can launch **`U1` (explicit 3D `WHERE_CACHE` VLA)** immediately after `Test L` (`B1`/`B0`) without waiting:
1. Run `vla_where` `P-1..P-4` LIBERO replay & `3D where-head` (`step-544` + `DA3` comparison if supported!) extraction on `LIBERO-Spatial` demos (`d5_s0` first, and check full `d5` / `LIBERO-Plus +Cam` scope).
2. Build the verified `WHERE_CACHE` artifact (`d5_s0` + check whether `d5_s0..s2` or `50-demo` cache is fast enough to build too!).
3. Verify schema integrity, exact frame/key alignment against `vla_libero`'s `U1` loader, finite values (`0` NaNs), and stage the cache compactly (`tar.gz` or GCS upload via `trinity-0-13` `ossh`/gcloud if `<2 GB`) ready for Orchard `U1`!

## Hard Rules
- **Assigned GPU:** Use **`trinity-0-18` GPU `6`** (`0%, 1 MiB` free; MUST wrap EVERY GPU process in `/data3/shared/scripts/vnice/vnice.sh`). **CRITICAL `/scratch` limit:** `trinity-0-18` has only **`34 GB` free `/scratch`** — NEVER write `>5 GB` onto `0-18:/scratch`! Check first whether `step-544` + `vla_where` + LIBERO datasets already exist on `0-18:/scratch` (or via NFS `/data*` read if tiny `<1 GB`). If `step-544` (`~18 GB`) is NOT already on `0-18:/scratch`, DO NOT copy `18 GB` onto `0-18`! Instead check whether `0-18` already has it, OR prepare & unit-test the exact `P-1..P-4` + `d5_s0` `WHERE_CACHE` runner script on `2-28` (where `step-544` + `1.8 TB` free already live!) so it can fire on `2-28` GPU `5` or `7` the instant `KT-6 Stage-1A` completes (~15–20 min!).
- **DO NOT touch** `trinity-0-13` GPUs (`0,1,2,3,4,5,6` all currently occupied!), `trinity-2-28` GPUs `0..7`, or SPLIT's GPUs (`0-18:0..3`, `0-8:1..2`, `0-23:1,7`).
- Wrap any GPU job NOT on `trinity-0-13` in `/data3/shared/scripts/vnice/vnice.sh`.
- Zero deletions, zero `git`, zero broad NFS scans, zero `>30 GB` NFS IO.

## Exact Steps
1. Read `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/launch_trinity_vla_prechecks.md` and `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_vla_bridge.md` to locate the exact `vla_where` repo/kit path, `P-1..P-4` commands, `d5_s0` demo manifest, and `vla_libero` `U1` cache contract.
2. Inspect `vla_where` scripts and tests (`T-11` already passed on `2-28` GPU 6!). Check where `LIBERO` HDF5/demo files and `step-544` checkpoint live across `0-13` and `0-18`.
3. Run `P-1..P-4` replays and build `d5_s0` (and `d5_s1`, `d5_s2` if total time < 30 min!) `WHERE_CACHE` on `trinity-0-13:0` (unwrapped, `<3 GB` scratch footprint) or `trinity-0-18:6` (`vnice.sh`).
4. Also run a quick **diagnostic comparing `step-544` depth/pose vs `DA3` depth/pose on LIBERO `d5_s0` frames** (checking robot wrist/third-person camera scale accuracy against MuJoCo/LIBERO GT depth & FK camera extrinsics if exported by LIBERO!) — this tells us whether `U1-DA3` or `ScaleAnchor` improves LIBERO 3D lifting even further!
5. Verify cache completeness (`100%` of `d5_s0` keys present, exact tensor shapes/dtypes expected by `vla_libero` `U1`, `0` NaN/Inf, deterministic reload test).
6. Write concise verified report to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_vla_where_cache_prep.md` with exact cache paths, byte sizes, and exact Orchard `U1` launch command flags.
