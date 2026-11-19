# sb_rowA2 delivery

The build contains 6,000 camera training rows and 900 byte-identical held-out items. All row-build checks pass. The separate scorer patch passes CPU tests; cont_ops18 must obtain independent review and apply it before sealing.

N admission uses W19 tree `8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa`. `audit_camera_training.py` verifies the recovered extract SHA256 `9e6aa2bd618588a4054a71dc183bc31821fcb5a2bc7bb1952bbebe15559e7c6b`, its manifest binding to store c48d5b62, N’s complete removal lists (including n/z/u and the K1 union), tiered aliases or verified minting, and pinned room sets.

| Type | Extract | N kept | K1 dropped | withheld-80 dropped | Training |
|---|---:|---:|---:|---:|---:|
| Displacement | 14,020 | 12,218 | 210 | 1,592 | 2,000 |
| Rotation | 9,143 | 8,002 | 125 | 1,016 | 2,000 |
| Direction | 12,260 | 10,713 | 170 | 1,377 | 2,000 |

The withheld-80 rows also match N’s merged dev exclusion. All explicit removal-list hits, R0 hits, original dev-S1 hits, BENCH v2 hits and unresolved scenes are zero. SOURCE_AUDIT.json records marginal and joint counts; SOURCE_ADMISSION.jsonl records all 35,423 decisions.

| Cell | Displacement | Rotation | Direction |
|---|---:|---:|---:|
| t00 | 50 | 50 | 50 |
| t01 | 50 | 50 | 50 |
| t02 | 50 | 50 | 50 |
| t03 | 50 | 50 | 50 |
| t04 | 50 | 50 | 50 |
| t05 | 50 | 50 | 50 |
| t06 | 50 | 50 | 50 |
| t07 | 50 | 50 | 50 |
| t08 | 50 | 50 | 50 |
| t09 | 50 | 50 | 50 |
| t10 | 50 | 50 | 50 |
| t11 | 50 | 50 | 50 |
| t12 | 50 | 50 | 50 |
| t13 | 50 | 50 | 50 |
| t14 | 50 | 50 | 50 |
| t15 | 50 | 50 | 50 |
| t16 | 50 | 50 | 50 |
| t17 | 50 | 50 | 50 |
| t18 | 50 | 50 | 50 |
| t19 | 50 | 50 | 50 |
| t20 | 50 | 50 | 50 |
| t21 | 50 | 50 | 50 |
| t22 | 50 | 50 | 50 |
| t23 | 50 | 50 | 50 |
| t24 | 50 | 50 | 50 |
| t25 | 50 | 50 | 50 |
| t26 | 50 | 50 | 50 |
| t27 | 50 | 50 | 50 |
| t28 | 50 | 50 | 50 |
| t29 | 50 | 50 | 50 |
| t30 | 50 | 50 | 50 |
| t31 | 50 | 50 | 50 |
| t32 | 50 | 50 | 50 |
| t33 | 50 | 50 | 50 |
| t34 | 50 | 50 | 50 |
| t35 | 50 | 50 | 50 |
| t36 | 50 | 50 | 50 |
| t37 | 50 | 50 | 50 |
| t38 | 50 | 50 | 50 |
| t39 | 50 | 50 | 50 |

`build_camera_training.py` asserts these 120 cells, 6,000 distinct sources used once (cap two), and 6,000 unique qids/candidate_ids. It changes only qid, routing.qid, student_input.question and the two added candidate_id fields. Calls, traces, responses, spans, poses, options and answers are byte/value-identical to their sources. The generator skips 13 displacement candidates whose gt_answer uses a different numeric string (e.g. 2.0 versus 2.00; values agree) and one direction candidate whose printed response differs from recomputation; SOURCE_REJECTIONS.json records them. Legacy camera sources have no candidate_id; new IDs use N’s candidate_identity formula.

Frames come from decision.binding and agree with call arguments and clip length. N’s camera pack/validate path is carrier_c1_routing.c1_row/check_row, r1_training.row_check and r2_contract.frame_metadata. All 6,000 sources and 6,000 new rows pass. ground_rows.pack handles object-grounding records and is not the native camera packer.

`verify_camera_training.py` verifies all saved rows against raw source TEXT, repeats native checks and independently recomputes answers and complete printed responses from stored poses/gravity. Its SciPy camera arithmetic also agrees with N’s geometry implementation on 6,000 rows. No frame image is loaded by training-row checks.

The wording filter rejects normalized character Levenshtein distance below 0.20. It checks 3,276 normalized dev/kit questions from 58 files and the recovered legacy questions (3,359 combined forms). It removes 0 reserved-template candidates and 0 training candidates. All 24 held-out templates are checked against every complete training row; hits are zero. WORDINGS.json is a frozen inventory; CHECKS.json states current admission.

READ30.md prints 30 complete training rows. READ30_SHARED.md and READ30_UNIQUE.md factor repeated clip fields losslessly for manual reading; expansion equals every full row. MANUAL_REVIEW.json pins the reviewed bytes and records grammar/correctness checks.

`build_scorer_patch.py` produces SCORER_PATCH/placement.patch and the patched h1eval/scorers.py. Camera M1 uses display_frame_pair. All 636 original devs1_routed items have identical M1 in 3,816 test cases; all 450 camera expected calls match; all 900 held-out stub outputs score. Native load_manifest/map_items admit 900 items and 900 unique keys. Ten invalid frame-pair forms fail closed.

Review findings 2–6: frame binding is explicit (2); endpoint distance/yaw specificity may contribute to twin gaps, and duplicate inline options remain (3); native CPU admission passes (4); rotation h06’s shared phrase advisory remains and the legacy stream is included in the wording check (5); the frozen hash assignment stays at 13–27 items per wording, so use paired twin deltas and treat per-wording comparisons cautiously (6).

Commands: first build the exact edit-distance helper with `g++ -O3 -shared -fPIC wording_distance.cpp -o out/wording_distance.so`. Use `/scratch/jjyeung/envs/p1cpu/bin/python -B` with `check_wording_distance.py`, `audit_camera_training.py`, `build_camera_training.py`, `verify_camera_training.py`, `audit_source_rejections.py`, `build_scorer_patch.py`, `read_training_sample.py`, `finalize_delivery.py --reviewed-read30-sha256 <digest>`, `verify_camera.py`, then `package_delivery.py`. Each JSON pins its inputs; JSONL payloads use companion manifests. The archive checksum is in sb_rowA.tar.sha256.

Not done: independent scorer-patch review/application by cont_ops18, trainer ingestion, training or model inference. No GPU, network, SSH, Git or writes outside this workspace were used. No missing input affects the delivered row build. No borderline revision-history sentence is retained.
