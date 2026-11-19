Camera wording packet: **PASS with eval-room exclusions**. All 5,979 rows pass the pinned shared grammar; native intake admits 5,143 and refuses 836 `excluded:eval_rooms` rows.

The full envelope ran at `limit=2000`; disjoint shards of 2,000 / 2,000 / 1,979 rows cover the complete file. No other refusal remains.
By type, admitted/refused: displacement 1,717/277; rotation 1,722/271; direction 1,704/288. The 280 exposed exclusions in the input become 836 because grammar failures masked 556 further eval-room overlaps.

All 3,977 grammar refusals come from two forms: 1,993 rotation convention lines (`unit_quantity`) and 1,984 direction score lines (`number_not_allowed,unit_quantity`). CLASSIFICATION.json retains every exact line and diagnostic.
CAM-ROT-WORDS-v1 replaces the numeric wrap/half-turn convention with the shortest signed turn, positive for left, and a positive half-turn tie. CAM-DIR-SYMBOL-v1 removes only the numeric restatement after a negated component, e.g. `backward = -dz = 0.68 m` becomes `backward = -dz`.

The uniform rules edit 1,993 rotation and 1,988 direction traces: 3,981 changed and 1,998 unchanged. Four already-passing direction rows share the edited form. Calls, response bytes and values, questions, options, answers, GT, and all other substantive fields remain unchanged; response offsets are regenerated.
GRAMMAR.md states the exact number/unit rules. Numeric provenance can come from printed responses, question constants, valid frames/labels/lists, or verified binary arithmetic. Unit quantities require a matching response value or the result occurrence of correct arithmetic. A symbolic negation alone does not license a numeric restatement.

All 5,979 answers and GT labels are recomputed from printed responses and agree. Native replay, per-QID digests, source admission/lineage hashes, and the unchanged independent coverage entries pass.
All 450 reworded held-out items and their original twins match registered pins. The unchanged sb_rowA filter finds zero training wording hits below normalized Levenshtein distance 0.20, against both actual held-out questions and all 24 instantiated templates.

Room audit: R0=0, dev-S1=0, BENCH=0, withheld-80=0, K1=0; unresolved rows=0. This audit is separate from the native eval_rooms exclusion list.
READ40.md prints 40 complete before/after targets across all types, both edit forms, and unchanged cases; it includes questions, options, answers, GT and printed-response recomputation.

Both forms occur in P-source extracts: 2,000 rotation and 2,000 direction lines among 6,000 authenticated CAMERA_SOURCES rows. Unchanged source traces and edited wording traces therefore differ in prose. The full P routing base is MISSING locally; no global base counts are claimed.

Admitted counts per type × wording follow. Target=50 per cell; every cell below 50 is short by `50 − count`. CHECKS.json also records counts before exclusions and each refusal deficit.

| Wording | Displacement | Rotation | Direction |
|---|---:|---:|---:|
| t00 | 44 | 43 | 40 |
| t01 | 46 | 46 | 40 |
| t02 | 41 | 43 | 39 |
| t03 | 43 | 43 | 38 |
| t04 | 45 | 38 | 40 |
| t05 | 40 | 42 | 41 |
| t06 | 46 | 42 | 46 |
| t07 | 43 | 42 | 40 |
| t08 | 44 | 42 | 43 |
| t09 | 47 | 42 | 46 |
| t10 | 40 | 40 | 41 |
| t11 | 44 | 39 | 41 |
| t12 | 43 | 45 | 44 |
| t13 | 39 | 46 | 44 |
| t14 | 41 | 46 | 41 |
| t15 | 44 | 44 | 43 |
| t16 | 44 | 41 | 46 |
| t17 | 42 | 42 | 42 |
| t18 | 45 | 45 | 46 |
| t19 | 42 | 41 | 42 |
| t20 | 47 | 45 | 43 |
| t21 | 42 | 48 | 44 |
| t22 | 39 | 47 | 42 |
| t23 | 44 | 48 | 45 |
| t24 | 41 | 47 | 44 |
| t25 | 45 | 41 | 40 |
| t26 | 44 | 38 | 44 |
| t27 | 43 | 45 | 43 |
| t28 | 44 | 38 | 47 |
| t29 | 44 | 40 | 41 |
| t30 | 40 | 40 | 40 |
| t31 | 45 | 42 | 44 |
| t32 | 40 | 43 | 41 |
| t33 | 43 | 45 | 42 |
| t34 | 44 | 46 | 42 |
| t35 | 38 | 42 | 44 |
| t36 | 41 | 44 | 44 |
| t37 | 49 | 45 | 46 |
| t38 | 41 | 44 | 41 |
| t39 | 40 | 42 | 44 |

Commands producing all numbers (from this workspace): prefix Python commands with `nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -B`.

`work/build.py`: row/form/edit/shared-grammar counts. `work/rebind.py`: digest, coverage and exclusion accounting. `work/intake.py`: full-envelope and shard admission/refusal counts, using execute/tree_reads copied unchanged from fbp_route.
`work/verify.py`: unchanged fields, printed GT, held-out distance, cells and READ40. `work/source_forms.py`: source authentication and line-form counts. `work/grammar_notes.py`: six provenance boundary cases.

`/scratch/jjyeung/orch_n30/sb_auditfix2/store_room_audit.py --store "$PWD/out/rows/camera_wording.jsonl" --tree /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1 --lists /scratch/jjyeung/orch_n30/sb_auditfix2/inputs/lists --out "$PWD/out/room_audit"`: room counts; use an empty output directory.
`work/finalize.py`: rehashes recorded inputs and checks exact QID/shard/coverage bindings. `work/package.py`: writes and byte-verifies out/fbp_cam.tar; PACKAGE.json records bytes and members. Verify with `sha256sum -c out/fbp_cam.tar.sha256`.

Every output JSON carries input SHA256 pins; JSONL rows use BUILD.json and CHECKS.json as companion manifests. The archive includes rows, compressed shards, code, reports and active metadata dependencies; it contains no RGB bytes.
Tree seal: `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7`; grammar: `a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268`. Production composition still requires the tree owner to bind/reseal the changed source and downstream pins. This packet makes no tree changes or training claim.

Gate document file-byte SHA256 is MISSING: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/swarm_build/GATE_CAMERA_CALL_RATE_V1.md. Its text was read once; the initial read did not capture a hash. The three local held-out/wording files match its registered pins.
No-archaeology review: no borderline historical wording is retained. Before/after trace pairs and refusal counts are the requested controlled comparison.
