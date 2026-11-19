BUILT_FOR_INDEPENDENT_REVIEW

Config `774503e26f274a10c96ad06210d339c49ebc9a704ac254df81f389b0da4d98a1`; run `6ed2c7aa`; job `a15_cot_ap6ed2c7aa`; bundle `/project/community/jjyeung/okh7/i_ee227714`; kit `/project/community/jjyeung/okh7/x_ee227714`.

Archive `p_32337655.tar`; SHA256 `3233765535fc95eb34b876b2e96895b5f684bd8b4e6c5c93f9e23123d320317b`; 20,234,240 bytes. Two builds produced the same archive. The archive contains 43 regular files with an exact SHA256 inventory. Existing archives and snapshots remain intact.

B1r SHA256 `caba6a5695781491036de5b3acdb20db2d42ab581e5775fec3fe07fbd2114aad`; original B1 SHA256 `25c3db82b4c590a39924b6b9636b7b4372cf91134a6242fe9895daaca179ceba`. Both lists have the same ordered 17,879 row keys. Each pool value becomes `p` plus the first eight hex characters of its SHA256. Every byte outside the pool JSON string stays identical, including line order, key order, separators and reason. `out/B1R_MAPPING.json` records the private mapping and both hashes; it is absent from the archive and kit.

Loader evidence: `work/tree/student_pilot/row_removals.py:27–46` validates row keys and optional defect filters; lines 48–61 match those keys against row identities. The loader never accesses pool or restricts reason. The unchanged `count_diag_first_seen_list_form` reason is accepted. B1r has zero matches against the content deny expression used for this build; the independent whole-kit CLEAN certificate remains required. The opaque staging name is `z.json` in both the bundle and records.

The config resumes A’s real step-200 slot, stops at 600, exports 400 and 600, and uses `continuation.rows = rebind`. Counting is 1046 cents, totals 0 and direction 3499. Routing, other VQA cells, trainer, stores, selection, units, S2, seed and learning-rate horizon retain C4’s pins.

| Config field | C4 | Cprime |
|---|---|---|
| continuation.rows | "exact" | "rebind" |
| output | "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/05b8ac69" | "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/6ed2c7aa" |
| preparation_output | "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/05b8ac69" | "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/6ed2c7aa" |
| remove_files | [{"path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_0.jsonl", "sha256": "62113ff38f918528341d3c38c6cce372736f2b44ca932c3b706be29397798dc3"}, {"path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_1.jsonl", "sha256": "4701e195ffc04fe256b916a05eb0a669df6cf3f97d73c9986bfe5de3170b089c"}, {"path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_2.jsonl", "sha256": "6eb00a2de04c84d6dd9a0aa5d67d822bf2af6c9d408b1815b25ec6248bef27cc"}, {"defects": ["identity", "absent", "merged"], "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_3.jsonl", "sha256": "8a97fcc4f1f4fd7a302a8b16c461d3095fbcf9ece3a39cce7db24d5a363dd1b2"}, {"path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_4.jsonl", "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}, {"path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_5.jsonl", "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}, {"path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/n.json", "sha256": "02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411"}] | [{"path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_0.jsonl", "sha256": "62113ff38f918528341d3c38c6cce372736f2b44ca932c3b706be29397798dc3"}, {"path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_1.jsonl", "sha256": "4701e195ffc04fe256b916a05eb0a669df6cf3f97d73c9986bfe5de3170b089c"}, {"path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_2.jsonl", "sha256": "6eb00a2de04c84d6dd9a0aa5d67d822bf2af6c9d408b1815b25ec6248bef27cc"}, {"defects": ["identity", "absent", "merged"], "path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_3.jsonl", "sha256": "8a97fcc4f1f4fd7a302a8b16c461d3095fbcf9ece3a39cce7db24d5a363dd1b2"}, {"path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_4.jsonl", "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}, {"path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/remove_5.jsonl", "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}, {"path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/n.json", "sha256": "02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411"}, {"path": "/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/z.json", "sha256": "caba6a5695781491036de5b3acdb20db2d42ab581e5775fec3fe07fbd2114aad"}] |
| type_mix.streams.vqa.cells.counting.cents | 1087 | 1046 |
| type_mix.streams.vqa.cells.direction.cents | 3119 | 3499 |
| type_mix.streams.vqa.cells.totals.cents | 339 | 0 |

The census applies all seven C4 REMOVE lists, then B1r, to the SHA256-verified v7 SQLite store. It reproduces all C4 eligible counts. Eligible rows fall from 203,812 to 185,933; all 2,617 remaining counting rows use procedure form. No cents adjustment is needed.

| VQA cell | Before B1r | After B1r | Cents | Rows/step | Ceiling: 4 × eligible / 1,000 | Draws over 1,000 steps | Unique drawn rows | Max draws/row |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| appearance | 27587 | 27587 | 1442 | 14.42 | 110.348 | 14420 | 14420 | 1 |
| box | 3813 | 3813 | 182 | 1.82 | 15.252 | 1820 | 1820 | 1 |
| camera_absolute_distance | 0 | 0 | 0 | 0.00 | 0.000 | 0 | 0 | 0 |
| camera_obj_rel_dist_v1 | 1930 | 1930 | 200 | 2.00 | 7.720 | 2000 | 1930 | 2 |
| camera_obj_rel_dist_v2 | 1957 | 1957 | 200 | 2.00 | 7.828 | 2000 | 1957 | 2 |
| camera_obj_rel_dist_v3 | 1978 | 1978 | 200 | 2.00 | 7.912 | 2000 | 1978 | 2 |
| counting | 11295 | 2617 | 1046 | 10.46 | 10.468 | 10460 | 2617 | 4 |
| direction | 49901 | 49901 | 3499 | 34.99 | 199.604 | 34990 | 34990 | 1 |
| facing | 43469 | 43469 | 1817 | 18.17 | 173.876 | 18170 | 18170 | 1 |
| first_seen | 6985 | 6985 | 200 | 2.00 | 27.940 | 2000 | 2000 | 1 |
| obj_obj_relative_pos_lr | 1978 | 1978 | 200 | 2.00 | 7.912 | 2000 | 1978 | 2 |
| obj_obj_relative_pos_nf | 1982 | 1982 | 200 | 2.00 | 7.928 | 2000 | 1982 | 2 |
| obj_obj_relative_pos_ud | 1974 | 1974 | 200 | 2.00 | 7.896 | 2000 | 1974 | 2 |
| relative_distance | 20665 | 20665 | 2274 | 22.74 | 82.660 | 22740 | 20665 | 2 |
| room | 425 | 425 | 170 | 1.70 | 1.700 | 1700 | 425 | 4 |
| route | 8894 | 8894 | 970 | 9.70 | 35.576 | 9700 | 8894 | 2 |
| size | 9778 | 9778 | 0 | 0.00 | 39.112 | 0 | 0 | 0 |
| totals | 9201 | 0 | 0 | 0.00 | 0.000 | 0 | 0 | 0 |

Every cell satisfies its measured ceiling. The direction card’s 373.48 combines direction (49,901 rows) and facing (43,469 rows). The sealed loader treats them as separate cells, so direction’s measured ceiling is 199.604. Its configured 34.99 rows per step is below that ceiling.

The native VQA-only loader audit passed over 1,000 steps with all eight REMOVE lists. It drew 128,000 rows, with at most four draws per row. Counting draws: procedure 10,460; first-seen list form 0; other 0. This audit checks local structural eligibility and the native sampler. Production RGB, division recomputation and routing admission remain in-job checks.

The canary_delta gate authenticates C4 identity `6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74` through admission job 172180 and the exact receipt/log pins. It compares the complete sealed C4 and Cprime configs, permits only the seven reported differences, verifies derived paths and staged pins, and records `canary_delta=true`. GO authority is `sha256:1f3dff81041a58c45966e83535ec50182a616de94d036fcfcfa5142141862b7e`. It requires no PROOF_JOB. PASS and canary branch bodies remain byte-identical to C4.

| Validation | Result |
|---|---|
| Delta gate and B1r byte/row-key tests | 17 passed |
| Driver pin, review, pending-state and session tests | 5 passed |
| Legacy suite | 112 selected: 50 passed, 62 not run for missing recovered inputs, 0 failures, 0 errors |
| Archive reseal | PASS; exact deterministic archive |
| D0 OFF identity | PASS; all four rank states exact |
| Cprime native first batch | PASS; four ranks, finite losses and S2 checks |
| Two H1 deployment derivations | NOT RUN; missing pinned k/s1_record.json |

All suites ran sequentially through `tools/cprime_local.sh`, under `prlimit --as=21474836480` with thread limits at most eight. `tools/run_local_checks.py --cprime` runs the Cprime package, derivation and native checks; its derivation-only recheck uses the verified local H1 recovery. No network, SSH, Orchard operation, Git, deletion, minting or submission ran.

The mint helper matches `b7388f557f941ccd0e3c2d82bf3ade0e1ad34e8a96e5f995d35dcefef79cf57d`. The recovered D0 tree has 792 files and inventory `b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99`; reconstructing its deterministic archive reproduces `845b17895e466671bc5c5ecdb6a5a5d697a43a5e02d07d1555b11be74f8fd415`. H1 recovery reproduces its pinned tree, archive and code record and restores 11 manifest entries without changing their pins.

The recovered H1 view still lacks the following pinned members. `H1_RECOVERY_CPRIME.json` records each expected SHA256; no replacement pin is fabricated.

- `/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/c2db2a1a.json`
- `/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/frame_map.jsonl.gz`
- `/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/frame_plan.json.gz`
- `/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/input_mdg_rasters.json`
- `/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/input_source_tokenizer.json`
- `/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/np226_5204b3a0.tar`
- `/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/pool_exclusion_0.tsv`
- `/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/pool_exclusion_1.tsv`
- `/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/pool_exclusion_2.tsv`
- `/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/pool_indices_6.json`
- `/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/pool_selection.json`
- `/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/s1_record.json`
- `/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/t_e6456bcecb8d4a8f4f68158eb68275f8befff128.tar`

The unavailable native division input is `/scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m3/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/z/4c230a7e.json`. Its check is not run and does not block this review build; Orchard admission recomputes the division. The complete per-test missing-input ledger is `LEGACY_TESTS_CPRIME.json`. It includes filtered older derived-kit inventories, frozen snapshot artifacts, frame maps, row slices, and admission logs. These omissions prevent claims that the full legacy suite or local deployment derivation passed.

The reviewer must check the exact config delta and B1r byte-only rewrite; census and draw evidence; C4 admission pins; the production H1 derivation and its manifest; the unchanged p/t/u authority; the twelve-review chain; independent whole-kit CLEAN classification; the real A donor; 20 fresh sessions; and final archive/driver checksums. The missing-input checks are waived only for this local review build. Drivers retain the production gates.

Operator sequence and expected outputs: `/scratch/jjyeung/orch_n30/r1_ops/work/drv_cp/README.md`. Driver hashes: `/scratch/jjyeung/orch_n30/r1_ops/work/drv_cp/DRIVER_SHA256SUMS.txt`. rv1, sc1 and si1 are intentionally inert until the independent review, CLEAN certificate and fresh sessions arrive.
