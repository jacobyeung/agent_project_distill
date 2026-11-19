# Camera wording read: cont_ops18 handoff

The delivery contains 6,000 training rows and the frozen 900-item paired evaluation (450 originals, 450 reworded twins). The three HELDOUT_* files and WORDINGS.json retain the SHA256 values in HELDOUT_FREEZE.json. CAMERA_ROWS.jsonl is the N-filtered training payload; CHECKS.json and INDEPENDENT_TRAINING_CHECK.json certify it. CAMERA_LINEAGE.jsonl and CAMERA_SOURCES.jsonl.gz bind every row to raw recovered source TEXT.

The read owner must apply SCORER_PATCH/placement.patch to its staged package before sealing. The patch changes only h1eval/scorers.py: camera placement builds the expected call from the item's display_frame_pair and refuses missing/invalid pairs. Other task types retain expected_calls(question,type). The original rows/expected_calls.py stays byte-identical.

SCORER_PATCH/CHECKS.json records exact M1 parity on 636 devs1_routed items over 3,816 call-output cases, agreement with all 450 original camera calls, 900 successful held-out measure() stub outputs, and native loader/mapping admission for all 900 items. Ten invalid pair forms are refused. The builder has not supplied an independent reviewer: obtain that review before applying and sealing.

1. Check the patch's source and destination hashes in SCORER_PATCH/CHECKS.json. Apply the diff under out3/bases/b1/src, or stage the supplied patched file at h1eval/scorers.py. Re-run the CPU parity and 900-item stub checks in the staged package.
2. Stage HELDOUT_CAMERA_ITEMS.json, HELDOUT_CAMERA_TWINS.json and HELDOUT_NATIVE_TASKS.jsonl under items/. Add them to orchard_h10/build.py:sources with those archive members; keep the portable auth/R0_ROOMS.txt pin.
3. Set run_cfg['items'] to the package path items/HELDOUT_CAMERA_ITEMS.json and select camera_displacement, camera_rotation, camera_movement_direction. Use the existing dev-S1 frame/tree/export/model settings, with tasks=[<package>/items/HELDOUT_NATIVE_TASKS.jsonl]. If settings use item_sets, give heldout_camera_wording the same effective settings and this task path. Each task ID must occur once.
4. Seal the patched evaluator, parser, settings, item/task payloads and archive together. merge.py checks evaluator_code_sha256 and expected_calls_sha256 against launch-time bindings. Use a fresh output/journal location; patching after launch invalidates the binding.
5. Run h1eval.items.load_manifest and parity_adapter.map_items with the staged settings before inference. The working CPU interpreter is /scratch/jjyeung/envs/p1cpu/bin/python. Put the package's b/ ahead of h1eval/reader_core on sys.path; if e2e_reader was already imported from reader_core, use a fresh process with the correct order.

Use HELDOUT_CAMERA_TWINS.json for paired placement, response-use and answer metrics. Report original and reworded results separately by type. Per-wording cells are small and uneven (13–27); endpoint/yaw specificity and the rotation h06 shared phrase remain interpretation advisories. Keep all 24 held-out wordings out of training.

No production package was modified and no model read was submitted by this lane. cont_ops18 owns patch review, application, sealing and launch.
