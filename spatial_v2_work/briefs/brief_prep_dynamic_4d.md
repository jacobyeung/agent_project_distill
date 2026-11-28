# Brief: Dynamic 4D (`Point4D`/`Any4D` + `DA3`) & Cross-View (`VSTI`/`ReSTI`/`DSI`/`Ego-Exo4D`) Recon & Pilot

## Objective
Our `/goal` requires a spatial model that solves **static, dynamic, multi-view, and long-horizon video** — not only static rooms! Recent Nov-2026 SPLIT work proved massive dynamic/cross-view gains (`Point4D+MapAnything` `+16–27 pp` DSI/ReSTI, `98% vs 10%` reversed VSTI; HD-EPIC streaming `87.0 vs 53.2`; Ego-Exo4D `+33.5 pp`), and our Hour-0 audit confirmed `Point4D` (`5.8 GB`), `Any4D` (`7.7 GB`), and `MoGe-ViT-L` (`1.3 GB`) are ALREADY staged in `gs://cmu-gpucloud-jjyeung/ae/`!

Your mission:
1. **Inventory exact local dynamic/cross-view assets on Trinity (`/scratch` only, zero broad NFS scans!):**
   - Check top-level `/scratch/jjyeung/` on `trinity-2-28`, `trinity-0-13`, `trinity-0-18`, and `trinity-0-8` (exact paths from `w1_split_breakthroughs.md`, `w1_student_state.md`, and `exec_h0_rescue_and_orchard.md`) for:
     - `Point4D` / `Any4D` / `MapAnything` code & weights
     - `VSTI-450` / `VSTI` / `ReSTI` / `DSI-Bench` / `Ego-Exo4D` / `HD-EPIC` benchmark datasets, splits, and room/scene exclusion lists (`75` ReSTI ScanNet rooms!).
2. **Design & verify the clean dynamic 4D teacher extraction contract for `Spatial-V2` Stage-2 (`spatial_v2/dynamic_4d_schema.py`):**
   - Exact tensor schema for `has_4d_teacher`: per-frame metric depth, camera pose `SE(3)`, per-pixel dynamic probability `p_dyn` (`1 - p_stat`), and 3D scene-flow / world-space point tracks (`ΔX_3D`) aligned to `Spatial-V2` `GeoHeads` (`Geo4DHead` / `static_flow_loss`).
   - Exact zero-leak room/video split guard ensuring zero overlap with `BENCH_v2`, `ReSTI` (`75` ScanNet rooms), `VSTI-450`, `DSI-Bench`, `Ego-Exo4D`, and `HD-EPIC` eval splits!
3. **Run a live GPU pilot on `trinity-0-8` GPU `5` (`0%, 2 MiB` free; MUST wrap in `/data3/shared/scripts/vnice/vnice.sh`; keep local `0-8:/scratch` writes `<3 GB`!)** — OR if `Point4D` weights are only in GCS and `0-8` only has `38 GB` free `/scratch`, stage a single tiny dry-run / Orchard extraction script (`orchard_extract_4d_teachers.sh`) ready for Orchard `1× H100 general` (which sits right next to `US-CENTRAL1` GCS at 10+ Gbps and has `6 TB` `/tmp`!), AND run a real **`VSTI-450` / `ReSTI` / `DSI` zero-leak evaluation harness check** + `spatial_v2/tests/test_dynamic_4d.py`!

## Hard Rules
- **Assigned GPU:** `trinity-0-8` GPU `5` (`vnice.sh`, `<3 GB` writes to `0-8:/scratch`). Do NOT touch `2-28:0..7`, `0-13:0..7`, `0-18:0..3`, or `0-8:0..2,4,6,7`.
- Zero broad NFS scans, zero deletions, zero `git`, zero `>30 GB` NFS IO.
- Write concise verified report to `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/result_dynamic_4d_prep.md`.
