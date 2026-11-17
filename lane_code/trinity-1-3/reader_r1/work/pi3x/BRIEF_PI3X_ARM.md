# Codex build brief (lane reader_r1, NOT dispatched): tower as a serving pin, with a Pi3X tower arm, on payload 9f891bc1 (package e09e45fda45db)
Dispatch only if lane tower_redecide recommends Pi3X for distance and ORCH says so. Workdir a fresh folder under /scratch/jjyeung/orch_n30/reader_r1/work/pi3x/w. No ssh, Git, kills, submissions, network.
## Inputs to stage first (lane does it; over InfiniBand from trinity-1-18)
- Pi3X source, weights and runtime from the bake-off kit trinity-1-18:/scratch/jjyeung/geo_bakeoff_assets/kit (record distill_design/GEOMETRY_BACKEND_BAKEOFF_20261111.md; Pi3X passes 8-frame CPU inference); K1 pricing arm `pi3x_native` (distill_design/GEO_TOWERS_K1_PRICING_20261116.md, code trinity-1-18:/scratch/jjyeung/orch_n30/geo_k1/k1towers).
- Base: /scratch/jjyeung/orch_n30/reader_r1/work/b1g (package e09e45fda45db: REPORT.md, out/src, build scripts, tests); replay harness /scratch/jjyeung/orch_n30/reader_r1/work/b1/in/replay.
## Change
1. Serving pin `tower` in read settings (values `g3t`, `pi3x`; missing key fails), bound into read identity, memo key and pairing; `g3t` byte-identical to e09e45fda45db.
2. `TowerPi3X` in b/e2e_reader/real.py beside TowerG3T with the same output contract (raw_pose9, anchor_slots, frame_indices, depth_grid, depth_conf_grid, grid_uv, source_hw), weights as a pinned artifact component, run inside the call, memoizable under `perception_memo_modules` = [pi3x].
3. Package the Pi3X weights and deps as authenticated inputs (no download in the job), with the operator commands to stage them on Orchard once.
4. Check that the selector head (trained on G3T-geometry features) still selects well on Pi3X geometry: CPU stage-1 replay of the 294 dev-S1 pairs on Pi3X depth x own-depth scale, both selector rules, beside the G3T replay.
5. Kit: one 1-H100 job, distance only (150 items) under the rule ORCH names, tower pi3x; estimate time (Pi3X seconds per capture measured on CPU fixture, scaled).
## Gates
g3t identity (all b1g suites + replay 0 mismatches), Pi3X CPU forward on an 8-frame fixture through TowerPi3X, EAT-1 generate-path scan no new A3/A4, empty-root rehearsal, return members include all journals.
