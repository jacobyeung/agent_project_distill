# navrun CPU build report

Python 3.9.18, habitat-sim 0.2.4, CPU navmesh simulator, no renderer. All training GT and val-unseen metric references come from official R2R-CE preprocessed files.

`run.sh` uses `nice -n 19`, OMP/MKL/OpenBLAS limits of 8 and scratch caches. Work stays in this workspace. No network, SSH, Git, installation, GPU or detached process is used.

```sh
./run.sh -m unittest discover -s tests
./run.sh -m navrun.proofs plans  # tracks, statistics, both replays, 1%/10% rows
./run.sh -m navrun.proofs eval   # dense-reference proofs and both click variants
./run.sh -m navrun.click_diagnostics  # unchanged geodesic policy, decision traces
./run.sh -m navrun.build_report
```

Unit gate: **118 passed, 0 failed, 0 skipped in 7.906 s**. All 105 existing tests pass. Added tests cover official-id loading, coverage, malformed GT, cache refresh, GT arc-length leads, duplicates, endpoint/tie behavior, STOP boundaries and resume identity.

Official GT root: `../navrun_inputs/refs/r2r_vlnce_preprocessed/R2R_VLNCE_v1-3_preprocessed`. The loader validates primitive streams, forward counts, location alignment, complete requested-id coverage and start positions. Official files override cached reconstructions; R2RIE and greedy reconstruction remain labelled fallbacks and serve **0 training episodes**.

| GT file | SHA256 |
|---|---|
| train_gt.json.gz | `b63fa10e5c57d1b80b241c49bdeddc3d481bbe54b41ca0d59f9584c10da7bd5d` |
| val_seen_gt.json.gz | `cf41ac4dc6bcbada202e9cf0c414b0469153a4e1c5d02a21f088edd6032299fc` |
| val_unseen_gt.json.gz | `46a2e02c4a5e3b9d3d3c936009cbe1a4e9ea8f34156589f1e69ff1ff7080c044` |

Nav codec replay matches official actions on **10,819/10,819** training episodes: 0 mismatches, 115,016 answers and 631,244 primitives. Every stream has source `supplied_official_r2r_ce_gt`.

| Simulator replay against GT locations | Episodes | Endpoints within 2e-6 m | Entire path within 2e-6 m |
|---|---:|---:|---:|
| Full train | 10,819 | 10,819 | 10,819 |
| train_10pct_s0 | 1,082 | 1,082 | 1,082 |
| train_1pct_s0 | 108 | 108 | 108 |

Replay executes every action from the episode start pose and compares the start plus every forward endpoint, including blocked moves. Maximum full-training path error: 0 m. Episode 3707 has maximum path error 0 m and endpoint error 0 m. The record’s 0.42 m intermediate discrepancy is not reproduced in this simulator.

| Training plan | Episodes | States / text / chunk | Nav rows | Click rows | Waypoint rows |
|---|---:|---:|---:|---:|---:|
| 1% | 108 | 6,114 each | 1,093 | 1,009 | 1,301 |
| 10% | 1,082 | 62,749 each | 11,370 | 10,396 | 13,763 |

Both seed-0 subsets cover all 61 scenes and nest exactly. The 1% click label counts are {'click': 661, 'near_point_clamp': 90, 'out_of_view': 150, 'stop': 108}. The record reports 6,348 states, 1,158 nav, 1,497 click and 1,232 waypoint rows for its 1% subset; its exact ids and terminal-sampling implementation are unavailable.

Rows carry official GT provenance, prompts, history indices, executed primitives, answers and planned frame paths. Nav packs up to three primitives per token and three tokens per answer. Click rows advance by commanded primitive count and stop at the first within-1m decision. CPU frame paths refer to absent PNGs. `out/rows/rows.jsonl.gz` and `subset_1pct_rows.jsonl.gz` contain the 10% and 1% rows.

| Val-unseen proof | Episodes | SR | SPL | nDTW | SDTW |
|---|---:|---:|---:|---:|---:|
| oracle | 1839 | 1.000000 | 0.998847 | 0.923355 | 0.923355 |
| oracle | 600 | 1.000000 | 0.999043 | 0.927851 | 0.927851 |
| random | 1839 | 0.021751 | 0.018942 | 0.298277 | 0.014421 |
| random | 600 | 0.028333 | 0.023862 | 0.298007 | 0.017337 |
| forward-only | 1839 | 0.039152 | 0.038127 | 0.321639 | 0.032338 |
| forward-only | 600 | 0.046667 | 0.045724 | 0.324624 | 0.037366 |
| instruction-prior | 1839 | 0.047308 | 0.044615 | 0.328833 | 0.037028 |
| instruction-prior | 600 | 0.053333 | 0.049969 | 0.330381 | 0.041687 |

All 1,839 val-unseen episodes use official `val_unseen_gt.locations` for nDTW/SDTW; sparse-reference count is zero. FastDTW uses radius 1 and Euclidean costs after consecutive-position deduplication. R2RIE proofs retain their supplied dense references. The full-val shortest-path oracle record is SR 1.000 / SPL 0.999.

Blind policies use official training statistics: median forward count 35, median turn run 1. Random draws iid primitive frequencies, including STOP, with SHA256(seed:episode_id) RNG. Instruction-prior splits the forward budget around lexical left/right/around occurrences. Record policy details and exact list hashes are unavailable.

| Oracle-click on the fixed 600 ids | SR | SPL | OSR | nDTW | SDTW | 500-step caps |
|---|---:|---:|---:|---:|---:|---:|
| Geodesic lead, STOP <1 m | 0.665000 | 0.657592 | 0.740000 | 0.754820 | 0.607136 | 201 |
| GT-location lead, STOP <3 m | 0.886667 | 0.878669 | 0.886667 | 0.832170 | 0.781288 | 68 |
| Record GT lead, no occlusion | 0.802 | 0.792 | 0.847 | unavailable | unavailable | unavailable |

Geodesic lead interpolates 2 m along the current shortest path to the goal. GT lead chooses the nearest 3-D GT location (first index wins ties), then interpolates 2 m forward along that path, clamping at its endpoint. It requests STOP when geodesic goal distance is strictly below the 3 m success radius. It has no monotonic-index restriction.

Both variants project the lead point and use the same floor-plane lift/controller without occlusion. The GT lookahead uses `vla_where.nav.CLICK.max_leg_m=2.0`; standoff is 0.5 m, turns are 15 degrees, forward steps are 0.25 m, and SENSOR is 512 px / 90 degrees / 1.25 m. The success radius comes from the record and Config. No parameters were tuned to the record’s scores. Lead source and STOP radius both differ, so this comparison does not isolate either effect.

Geodesic diagnostics reproduce **600/600** saved action streams exactly. Its 201 capped tails partition into {'moving_repeated_pose_heading': 34, 'no_repeated_pose_heading': 49, 'stationary': 118}; tails use the last 20 decisions, stationary means every position is within 1e-4 m of the final one, and repeated states round pose/heading to 5 decimals.

| Overlapping observations among 201 geodesic caps | Episodes |
|---|---:|
| At least one blocked forward step | 134 |
| Repeated pose/heading in final 20 decisions | 152 |
| Near-point clamp in final 20 decisions | 122 |
| Out-of-view turn in final 20 decisions | 46 |
| Nonzero bearing rounded to zero turns in final 20 | 148 |
| Bearing sign changes in final 20 | 41 |
| Empty commands in final 20 | 0 |
| Within success radius at a decision boundary | 45 |

Of the 118 stationary tails, 102 have nonzero bearings rounded to zero turns at every one of the last 20 decisions; none of the 201 tails consists entirely of turn-only commands. The controller repeatedly commands blocked forward motion when a small correction rounds to zero turns. Near-point clamps lift y=0.99 to at least 1.276 m forward range and approximately 0.75 m commanded travel, which can sustain overshoot near corners/goals. These are overlapping trace observations, not mutually exclusive causal attributions. The 1 m STOP rule misses 45 episodes that reach the 3 m success radius; 37 finish inside it. No empty-command decision-cap failure explains the 201 step caps.

Resume signatures cover code, config, ordered ids, episode contents, metric references and policy identity; the GT-click identity also hashes its lead references and controller defaults. Journals preserve completed episodes. `out/STOP` stops at primitive boundaries.

Unavailable checks: GPU rendering/depth occlusion, habitat-lab parity, `nav.contracts.validate_public`, MIP rand100 ids, real model/tokenizer integration and real detection AUC/ATD. Scene manifests for student/G3T/SAM3 remain provenance unknown. Train/val-unseen/test scene sets are disjoint.

Source archive: `out/navrun_src.tgz` (package, tests, configs, wrapper, README and pyproject; excludes output data). **SHA256: 496836be8e375da80b807a87a26d1e9899540ede18f42cdb9243061514d51328**.

Evidence: `out/tables/{replay,location_replay,subset_plans,official_gt_sources,oracle_click_diagnostics,evaluation_summary_all}.json`, per-policy tables, journals and `out/unit_tests.log`.
