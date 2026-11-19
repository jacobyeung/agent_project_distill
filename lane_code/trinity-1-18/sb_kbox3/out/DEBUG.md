BLOCKER: the spec’s A0 is not the R1 serving reader.
The reviewed convert guard rejects two captures covering 12 registered training rows; R1 accepts both and answers 11 rows.
The labelled table is also the wrong reference for GD: it uses S4 scale and G1 tower-pose gravity.

Expanded replay: 149 operand choices in 45 training captures, with 15 captures per dataset.
Against the original isolated table: GD 132/149 (88.59%); table geometry 149/149 (100.00%).
GD on available exports only: 132/142. Missing exports count as failed replays.
Requiring the same ID and member frames: GD 127/149; table 149/149.
Table geometry gives exact candidate sets and feature vectors for 149/149 objects.
The unmodified table geometry producer reproduces 45/45 recorded geometry SHA256 values byte for byte.
Command: bash run.sh debug_geometry.py > out/box_ladder/replay_expanded.log 2>&1

ARKitScenes 41048124: table scale 2.7102517570; convert scale 2.2971098979.
Table choice tv:002 has 4 frames; GD choice tv:000 has 5 frames.
Table geometry SHA256: 6eee40bb764f956ba2a5fae5d98f30f171f5b3693a3a36526f6af5420bb4fd43.
The failing capture’s run_convert_1 and run_convert_2 exports are byte-identical: True.
Table origin: PACK/r1_src/b/heads/selector/sl118/sl_tables.py:71–87,129–166; isolation: isolate_tables.py:25–35.
The table uses no own-depth scale: SCALES_S4.json supplies exp(b0 + b1 log(h_raw) + b2 log(span)).
Coefficients: [0.5137804954677572, -0.8576678588049728, -0.0673900524654034].
run_iso/selector_head.json records caps_iso as the training input and weights 6d97c52407b7e106a7b475040558ba313589514c23c33b6994f4e7a0bb1df6c1.

Convert and serving median scales agree on 240/240 available training exports; the range-gate difference has no effect here.
Command: bash run.sh audit_serving_scale.py > out/box_ladder/serving_scale_audit.log 2>&1
Convert uses own_170235/native/probe/<digest>/own.npz and tower_scale_rule.estimate; OwnDepthScale uses stage1.median_ratio.
Serving also rounds exp(log(scale)) through float32; replay records this separately.

Missing exports: /scratch/jjyeung/k1/run_convert_2/{45511ef70c22b11e,9baa923934276385}/geometry.npz.
Their CACHE_COMPLETE.json files record reference_camera_up_opposes_gravity and retain REFUSED_GEOMETRY.npz.
Captures: scannetpp/0f69aefe3d and scannetpp/2c7c10379b.
R1 geometry.py:22–39 removes the terminal up-axis check; both from_npz and from_tower accept these arrays.
Command: bash run.sh audit_guard.py > out/box_ladder/serving_guard_audit.log 2>&1
The serving replay uses stored checkpoint own outputs; it does not claim to rerun the current language-model prefill.

Required orchestrator action: reconcile the registered A0 gravity contract with R1 serving; the reference rebuild must use the same contract.
Rebuild candidate labels and isolated features through the table producer on that geometry; candidate IDs cannot carry labels across geometries.
The 95% replay bar is unchanged. No training pricing, rule fitting, or held-out evaluation ran.
All evidence JSON files record input SHA256 values; commands above produced every numerical comparison.
