# Camera wording read

Use `HELDOUT_CAMERA_ITEMS.json` for 900 camera items: 450 unchanged dev-S1 originals and 450 reworded twins. Each type has 150 pairs. The R0-dev item files under out3 contain no camera items. `HELDOUT_CAMERA_TWINS.json` maps IDs and records the seeded wording assignment. Training coverage rows are MISSING; this read does not establish robustness after training on new wordings.

The inspected read is `sb_callrate/in/cont_ops/work/r1route/out3/bases/b1/src`. Its `h1eval/h10/parity_adapter.py:map_items` requires each item ID and question to match a native task. A new item file alone is insufficient. `HELDOUT_NATIVE_TASKS.jsonl` supplies all 900 matching tasks, derived from the pinned camera tasks by changing only the new twin's ID and question. Original task fields, labels, and clip bindings are preserved.

Apply these changes in the read owner's package workspace:

1. Stage the three `HELDOUT_*` files under the package's `items/` directory. In `orchard_h10/build.py:sources`, add each file with its corresponding `items/<filename>` archive member. Keep `auth/R0_ROOMS.txt` at its existing pinned location. The item manifest uses that portable reserve pin.
2. In `orchard_h10/job.py`, set `run_cfg['items'] = p + '/items/HELDOUT_CAMERA_ITEMS.json'` before serializing the worker configuration. Select `['camera_displacement', 'camera_rotation', 'camera_movement_direction']` as the read's types, in that order. Do not enable the optional R0 read for this camera-only package.
3. In the staged settings JSON, use the same frame, dense-frame, frame-root, tree, export, and model settings as the existing dev-S1 read. Set `tasks` to a one-element list containing the package's absolute path to `items/HELDOUT_NATIVE_TASKS.jsonl`. If settings depend on `item_sets['devs1_routed']`, give `item_sets['heldout_camera_wording']` the same effective settings and the new task path. The task list must contain each ID once.
4. Rebuild the package through its builder so `payload_pins`, payload/archive hashes, plan hash, `PACKAGE.json`, settings pins, and submission inputs bind the changed files. Use a fresh output/journal location. Runner and summarizer already honor `config['items']`; no native-binding bypass or question-parser relaxation is needed.
5. Run the native `h1eval.items.load_manifest` and `parity_adapter.map_items` CPU admission with the staged settings before any model read. The local metadata checks pass, but this workspace's Python lacks `torch`, so the full native imports were not exercised here.

Compare call placement, response copying, and answer accuracy between each pair using `HELDOUT_CAMERA_TWINS.json`. Group metrics by question type and wording ID. Report the unchanged originals separately from their reworded twins. Keep this evaluation set and its 24 wordings out of training.

`CHECKS.json` distinguishes completed evaluation checks from unavailable training checks. It does not certify camera row admission or independent pose-based label recomputation. No package was changed outside this workspace, and no read was submitted.
