# Build: rebuild the `navrun` package (R2R-CE closed-loop navigation runner, habitat-sim 0.2.4) from its design record. CPU only.

You work ONLY inside /scratch/jjyeung/orch_n30/b15_vla/navrun (your workspace; write nothing elsewhere). The original package was lost with its node; no copy survives. Rebuild it from the record, keeping the recorded interfaces, names and conventions.

## Hard rules
- No network, no ssh, no git, no pip install, no GPU, no deletion outside your workspace. Read other paths only by exact file name (no recursive find/grep/du over /home or /data*). Under /scratch you may list directories normally.
- Limit threads: export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8; run heavy loops under `nice -n 19`; never more than 8 worker processes.
- Do not write detached background processes; every command finishes before you end.

## Read first (exact files)
- Record (the spec): /data2/jjyeung/agent_project_data/distill_design/VLA_NAV_RUNNER_20261111.md
- Design (Test N, section 4.2 and the nav parts of 5): /data2/jjyeung/agent_project_data/distill_design/VLA_ACTION_HEAD_DESIGN_20261111.md (read in bounded parts; grep it for "4.2", "Test N", "nav", "click", "R2R").
- Grammar + codec (schema 8.1; vendor it by sha256 and add a drift check test): /scratch/jjyeung/orch_n30/b15_vla/work/orchard_kit/kit/ext_v2/vla_heads/vla_heads/codecs/nav_text.py
- Click lift + controller + ClickTranslator (schema 8.2, 8.4; the `click_backend`): /scratch/jjyeung/orch_n30/b15_vla/work/orchard_kit/kit/ext_where/vla_where/nav.py, its vendor/ (nav_text.py, VENDOR.json), geometry.py and types.py in the same package. Import vla_where from /scratch/jjyeung/orch_n30/b15_vla/work/orchard_kit/kit/ext_where on PYTHONPATH (do not copy it); vla_heads from .../kit/ext_v2/vla_heads.
- The schema file VLA_SCHEMA.md is lost; the vendored code is its executable form. Where the record and code disagree, the code wins; note it in the report.

## Inputs (local, read-only)
- Python env: /scratch/jjyeung/envs/nav_habitat024/bin/python (py3.9, habitat-sim 0.2.4, numpy 1.23.5, scipy, numpy-quaternion). It has no habitat-lab, no fastdtw, no pytest. Write tests with `unittest` so `python -m unittest discover -s tests` runs them; if `/scratch/jjyeung/envs/p1cpu` holds a pytest importable under py3.9 you may additionally support it, but unittest is the gate.
- R2R-CE v1-3: /scratch/jjyeung/orch_n30/b15_vla/navrun_inputs/refs/r2r_vlnce/R2R_VLNCE_v1-3/{train,val_seen,val_unseen,test}/*.json.gz. R2RIE-CE: .../navrun_inputs/refs/r2rie/R2RIE_CE_1_3_v1/ (direction split = val_unseen_error_v1_direction, *_gt.json.gz and *_bertidx.json.gz).
- Scenes: /scratch/jjyeung/orch_n30/b15_vla/navrun_inputs/scenes/mp3d/<scene>/<scene>.{glb,navmesh} for the 61 train and 11 val-unseen scenes (test scenes intentionally absent). If this directory is still empty when you start, wait (sleep 60, up to 20 min) — a copy is landing.
- Rendering needs a CUDA EGL device and is NOT available here. Every CPU path must run blind: habitat-sim with `create_renderer=False` / no sensors, or habitat_sim.nav.PathFinder loaded from the .navmesh, with VLN-CE movement (forward 0.25 m with sliding via try_step, turn 15 deg, stop, 500-step cap, success radius 3 m, agent height/radius as VLN-CE). Keep a render mode (RGB 512x512, HFOV 90, camera 1.25 m) behind a flag for the later GPU job; it need not run here.

## Build (package /scratch/jjyeung/orch_n30/b15_vla/navrun/navrun)
Everything the record lists: episode loader; episode loop with one policy interface `act(history_frames, instruction, state)`; 32-frame history `[i*t//31 for i in range(32)]` (length configurable; prompt and click frame number follow it); the five output formats `text`, `nav` (default for N0/N1), `waypoint` (+ local controller), `click` (nu_dec strict full match, floor-plane lift, fixed controller; vla_where `ClickTranslator` pluggable as `click_backend`, seeing only the schema-8.4 whitelist plus commanded forward metres), `chunk` ([K,3], physical or normalised, quantised residual execution); parse-failure rule from nav_text (re-query once, then FALLBACK, logged); metrics NE, SR, SPL, OSR, TL, nDTW, SDTW (port fastdtw's algorithm, radius 1, euclidean, as VLN-CE uses it; also offer exact DTW and test they agree on short paths); blind baselines random (RNG keyed by episode id), forward-only, instruction prior (use training action statistics; record your exact definition); shortest-path oracle (greedy geodesic follower on the navmesh); lists with ordered-id sha256 (val_unseen_600_s0: seed 0, proportional over the 11 scenes by largest remainder, interleaved so positions 0-199 stay proportional; val_unseen_full_1839; r2rie_direction_300 = 300 pairs; rand100 = MIP's OpenNav-100 — its id list is NOT available locally: implement the list loader that takes an id file and verifies position/scene/trajectory against val_unseen, and mark rand100 BLOCKED_IDS_MISSING); training subsets seed 0, nested, scene-balanced, 1% = 108 and 10% = 1,082 episodes covering all 61 scenes; row builder (T1-schema-like rows for nav, click, waypoint, text, chunk; record the fields; replaying every nav answer must reproduce GT actions on all training episodes; the train/val-unseen/test scene-overlap audit runs before writing); R2RIE-CE loader, detection AUC/ATD and SR/SPL drop over pairs; `navrun.compare` (GAIN, HARM, EQUIVALENT, INCONCLUSIVE, Holm within a family; paired bootstrap); `navrun.audit` (scene audit of manifests); resume of an interrupted evaluation, stop file, step cap, determinism. Configs for N0 (control-only, gated), N1, NU.

## CPU proofs to run and report (numbers, not claims)
1. All unit tests (target: cover what the record's 58-test list names; report count, pass/fail, wall time).
2. Shortest-path oracle SR/SPL on all 1,839 val-unseen episodes and on val_unseen_600_s0 and the 600 R2RIE-CE episodes (record: SR 1.000, SPL 0.999 on 1,839).
3. Blind priors (random, forward-only, instruction prior) on val_unseen_full, val_unseen_600 and R2RIE direction 300+300 (record table: e.g. full 0.024 / 0.041 / 0.042).
4. Oracle-click ceiling on val_unseen_600_s0 without occlusion (record SR 0.802, SPL 0.792, OSR 0.847).
5. 1% and 10% subset plans: decisions per episode, nav/click/waypoint/text/chunk row counts (record 1%: 6,348 states, 1,158 nav rows, 1,497 click rows, 1,232 waypoint rows) and the replay check on all 10,819 training episodes.
6. Blind CPU throughput (episodes/hour).
Write outputs under navrun/out/ (lists, tables as JSON). Differences from the record are findings, not failures: report each with its likely cause; do not tune to hit the record's numbers.

## Deliver
/scratch/jjyeung/orch_n30/b15_vla/navrun/BUILD_REPORT.md (<= 120 lines): module map; how to run tests and each proof; every proof's numbers beside the record's; deviations and why; what is blocked (rendering, rand100 ids, nav.contracts.validate_public which is not available here, habitat-lab cross-check because habitat-lab is not installed). Then make navrun/out/navrun_src.tgz of the package + tests + configs (no out/ data) and print its sha256 in the report.
