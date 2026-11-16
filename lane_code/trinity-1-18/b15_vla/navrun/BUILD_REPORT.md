# navrun CPU build report

Python 3.9.18, habitat-sim 0.2.4, CPU navmesh simulator, no renderer. All training GT and val-unseen metric references come from official R2R-CE preprocessed files.

`run.sh` uses `nice -n 19`, OMP/MKL/OpenBLAS limits of 8 and scratch caches. Work stays in this workspace. No network, SSH, Git, installation, GPU or detached process is used.

```sh
./run.sh -m unittest discover -s tests
./run.sh -m navrun.proofs plans  # tracks, statistics, both replays, 1%/10% rows
./run.sh -m navrun.controller_proofs  # both controllers/leads and rand100
./run.sh -m navrun.build_report
```

Unit gate: **132 passed, 0 failed, 0 skipped in 25.832 s**. All 118 existing tests pass. Tests cover the 102-episode stall replay, recovery direction and reset, external click backend, config defaults, rand100 order/identity and malformed releases.

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

Blind policies use official training statistics: median forward count 35, median turn run 1. Random draws iid primitive frequencies, including STOP, with SHA256(seed:episode_id) RNG. Instruction-prior splits the forward budget around lexical left/right/around occurrences. The record does not specify its blind-policy implementations.

| Oracle-click, fixed 600 ids | Version | SR | SPL | OSR | nDTW | SDTW | Step caps | Stationary tails |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Geodesic lead, STOP <1 m | v1 | 0.665000 | 0.657592 | 0.740000 | 0.754820 | 0.607136 | 201 | 118 |
| Geodesic lead, STOP <1 m | v2 | 0.683333 | 0.674559 | 0.751667 | 0.728940 | 0.623265 | 190 | 0 |
| GT-location lead, STOP <3 m | v1 | 0.886667 | 0.878669 | 0.886667 | 0.832170 | 0.781288 | 68 | 45 |
| GT-location lead, STOP <3 m | v2 | 0.886667 | 0.878669 | 0.886667 | 0.824599 | 0.781288 | 68 | 4 |
| Record GT lead, no occlusion | record | 0.802 | 0.792 | 0.847 | unavailable | unavailable | unavailable | unavailable |

Geodesic lead interpolates 2 m along the current shortest path to the goal. GT lead chooses the nearest 3-D GT location (first index wins ties), then interpolates 2 m forward along that path, clamping at its endpoint. It requests STOP when geodesic goal distance is strictly below the 3 m success radius. It has no monotonic-index restriction.

Both variants use the same floor-plane lift without occlusion. Schema 8.2 supplies the 2 m maximum leg, 0.5 m standoff, 15-degree turn and 0.25 m forward step. SENSOR supplies 512 px / 90 degrees / 1.25 m. The 3 m success radius comes from the record and Config. Lead source and STOP radius both differ between variants.

`Config.controller_version="v2"` is the NU/oracle-click default; `"v1"` preserves vla_where exactly. Config files use `vla.nav.eval.controller_version`. The sealed vla_where source is unchanged. V2 retains normal v1 commands, cancels the remaining leg at the first blocked forward step, then turns one quantum and probes one forward step per decision until motion resumes.

A blocked step moves less than 1e-6 m, the existing diagnostic zero-motion tolerance. Recovery starts toward the blocked leg’s bearing (left for zero) and keeps that direction despite subsequent bearing changes; this prevents alternating corrections from stalling. STOP takes precedence. Recovery uses no fitted bearing threshold, budget or score-dependent parameter.

Both the model-facing click decoder and an injected vla_where `ClickTranslator` pass through the same versioned controller. Only navrun receives displacement. Backend observations remain the five schema-8.4 fields; `executed_commanded` receives actual issued forward primitives × 0.25 m. Waypoint decoding and GT training-row conversion retain schema 8.2 behavior.

The fixture `tests/fixtures/controller_v1_stalls.json` stores the 102 ids, v1 action streams, controller-source hash and final 20 decision observations. CPU replay reproduces all 102 v1 streams/tails exactly; v2 leaves **0/102 stationary tails**. Full evaluation also reproduces **1,200/1,200 v1 action streams and metrics** across both leads.

Stationary tails require at least 20 decisions, with every last-20 decision position within 1e-4 m of the final decision position; heading changes do not count as movement. The step cap is 500 primitives. Residual step caps remain failures even when a tail moves.

The four residual GT-lead stationary tails (619, 1077, 1076, 1369) alternate explicit 90-degree left/right outputs and issue no forward primitives in their last 20 decisions. Blocked-forward recovery therefore does not trigger. Their traces are in `out/tables/controller_v2_residual_tails.json`.

Changes to the reported click numbers are logged below as **v2 minus v1** (metric fractions, not percentage points). Training proofs and the full/600 blind-policy numbers are unchanged.

| Lead | ΔSR | ΔSPL | ΔOSR | ΔnDTW | ΔSDTW | ΔStep caps | ΔStationary tails |
|---|---:|---:|---:|---:|---:|---:|---:|
| Geodesic | +0.018333 | +0.016968 | +0.011667 | -0.025880 | +0.016129 | -11 | -118 |
| GT-location | +0.000000 | +0.000000 | +0.000000 | -0.007572 | +0.000000 | +0 | -41 |

rand100 is **READY**: 100 episodes / 10 scenes from Open-Nav’s OpenNav_R2R-CE_100 release, in file order. All ids, scenes, trajectories and start positions match v1-3 val-unseen. The .json.gz source is plain JSON; gzip is detected by magic bytes. Drive id: `1SfrPWqCIiivwduCYPMe-Za1wOt4eU6G9`.

Source SHA256: `f4770f1baf87b936989e24c64ab10f69468676f485147ac528c7b8b9d639852f`. Ordered-id SHA256 (UTF-8 ids, trailing LF): `230eada875768a98552c2b2ad8eb56f09dbfe72cc55757b1bfa2b7fb9f64835f`. Frozen list: `out/lists/rand100.json`.

| rand100 policy | SR | Record SR | ΔSR | SPL | OSR | nDTW |
|---|---:|---:|---:|---:|---:|---:|
| oracle | 1.000000 | 1.000 | +0.000000 | 0.999739 | 1.000000 | 0.940710 |
| random | 0.020000 | 0.030 | -0.010000 | 0.014647 | 0.030000 | 0.280427 |
| forward-only | 0.050000 | 0.060 | -0.010000 | 0.048129 | 0.060000 | 0.321660 |
| instruction-prior | 0.060000 | 0.060 | +0.000000 | 0.056389 | 0.070000 | 0.328389 |

rand100 uses official dense GT references and the same fixed training statistics and policy definitions as the full/600 proofs. Blind-prior differences from the record are reported without fitting policies to those scores.

Resume signatures cover code, config, ordered ids, episode contents, metric references and policy identity; the GT-click identity also hashes its lead references and controller defaults. Journals preserve completed episodes. `out/STOP` stops at primitive boundaries.

Unavailable checks: GPU rendering/depth occlusion, habitat-lab parity, `nav.contracts.validate_public`, real model/tokenizer integration and real detection AUC/ATD. Scene manifests for student/G3T/SAM3 remain provenance unknown. Train/val-unseen/test scene sets are disjoint.

Source archive: `out/navrun_src.tgz` (package, tests including fixtures, configs, wrapper, README and pyproject; excludes output data). **SHA256: 4e85320b37314837c09eb77ac4049a57430e59cd795bfed28713ec05dc95c607**.

Evidence: `out/tables/controller_comparison.json`, versioned click tables, `*_rand100.json`, existing training/metric proofs, journals, `out/controller_proofs.log` and `out/unit_tests.log`.
