The CPU deliverables are complete for the available K1 training measurements; live hook binding and selected-arm pricing remain blocked.
The accepted specification matches SHA256 640e8deb8fe7d661abbeb3bb0d345aeb2b6eda4f50af346f0f16b0cf4788cce3.
The named specification, 0749Z ruling and pilot record were each copied once from NFS; NAMED_INPUTS.json records their hashes.

The pinned workload has 1,037 rows on 209 captures and 192 physical rooms. Its legacy table-covered subset has 883 rows.
All 209 captures now have rebuilt label tables. The retain-A0 rule affects 0 rows; its nonzero-score behavior is regression-tested.
A0 uses sb_kbox4 serving geometry: own-depth scale and own gravity. No S4 reconstruction serves as the present path.
The CPU pass re-scores 33 merged variants and S4-today on both fixed rowsets, pooled and by dataset: 272 paired contrasts.
K1_TRAIN_TABLES.md contains the tables; K1_TRAIN_RESULTS.json contains full dataset contrasts and input hashes.
Command for workload binding and table availability: `bash scripts/train_cpu.sh code/bind0749.py`.
Command for every score, count and interval below: `bash scripts/train_cpu.sh code/train0749.py`.

The distance detector is the pilot’s explicit rule: the rarer object is grounded in fewer than 3 frames. It never uses truth to fire.
It fires on 565 rows; 529 have two numeric values. Both measurements refuse on 36 rows.
Diagnostic 0.25/best1 re-measurement is closer on 66, worse on 46, and tied on 417 paired rows.
Its closer rate is 12.48% [95% CI 8.37, 16.86].
Switching only flagged rows changes full-row MRA by +0.463 points [-0.081, +1.084].
All 33 diagnostics, paired row evidence, closer-minus-worse intervals and refusal counts appear in DOUBT_REMEASURE.json.
These diagnostics do not select a repair arm. No merged variant meets the box kit’s eligibility rule; no rows were built.
The fitted three-field detector coefficients and threshold, and a size-specific trigger, are MISSING from the named pilot record.

A0 first-seen order is correct on 1006/1314 operand pairs (76.56%).
K1_TRAIN_DIAGNOSTICS.json gives each merged variant’s first-seen rate, merge precision and capture/name object counts.
Today-only size diagnostics use 770 deduplicated objects: serving MRA 52.364, S4 MRA 46.416.
The paired size change is -5.948 [-8.616, -3.466] points, with refusals scored zero.
That diagnostic cannot satisfy the selected-construction screen. P0 is refused; P1 evidence is MISSING; P2 requires CUDA.
The size gate requires the selected P0/P1/P2 construction on the same object set under both geometries before any size look.

The final sb_kbox4 DECISION.json is bound: replace_box, size_screen and first_seen_screen all FAIL; frozen_variant is null.
The hook binds serialized object_source, count_objects and stage1_replay through code/kbox_snapshot.py.
Native count_objects, object_source, price_k1_tracks and stage1_replay exports are MISSING from sb_kbox4’s top-level modules.
Expected native module: /scratch/jjyeung/orch_n30/sb_kbox4/box_math.py. The tracking-price adapter refuses explicitly.
Expected P1 input: inputs/TOWER_DECISION.json. Expected P2 output: out/object_route/K1_TRACK.json.
The package-D binding has MISSING step-544/job-172957 and step-200 slots, each for 290 twins plus 290 reworded items.
Expected returns: /scratch/jjyeung/orch_n30/cont_ops*/; bounded `ls -d` found no directory. No return filename was invented.
The absolute-distance comparison refuses without pinned package-D path/SHA256 records; its S4 reconstruction branch is removed.

GPU_NEED.json retains K1 tracking only: 1.3 hours estimated, 1.75-hour cumulative hard stop, one 48-GiB card; none used.
scripts/gpu_k1_track.sh uses vnice, /scratch caches, a local lock and separately required authorization/ledger receipts.
No CUDA predictor was attempted. The retained first GPU minute checks the staged predictor before the full pass.
Validation: 13 regression checks pass; `bash scripts/train_cpu.sh code/test0749.py`; `bash -n scripts/train_cpu.sh scripts/gpu_k1_track.sh`.
The checks cover retained nonzero A0 scores, pairing, truth-independent triggers, refused repairs, construction order and missing-input gates.
No R0-dev, K1 held-out, GPU, network, SSH, Git, process termination or tmux operation ran. All writes stayed in this workspace.
Archive and member verification: `bash scripts/train_cpu.sh code/final0749.py`; `sha256sum -c out/sb_kobj4.tar.sha256`.
Deliverables: out/REPORT.md, out/K1_TRAIN_TABLES.md, out/GPU_NEED.json, out/sb_kobj4.tar and its SHA256 sidecar.
No borderline revision-history prose is retained.
