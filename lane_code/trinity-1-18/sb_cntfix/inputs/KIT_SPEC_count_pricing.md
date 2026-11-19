# Counting pricing protocol

## 1. Scope
The kit evaluates one frozen counting proposal. All rule selection, constants, thresholds, response choices, row filters, and the launch decision use K1 TRAINING captures. `kit/files/FROZEN_CONFIG.json` is the executable freeze and includes training input hashes. K1 held-out records are diagnostic only. Official item files are prohibited.

## 2. Decision
The training selector evaluates the complete raw/NMS × maximum/second maximum × joint-threshold family on training pairs with truth ≥5. It selects the highest unrounded MRA, breaking ties in listed order. Constant 5, 6, or 7 is selected on the same training pairs and frozen once. The proposal proceeds only if its training MRA exceeds that constant and its paired capture-bootstrap lower bound exceeds zero.

The primary evaluation category is `counting`, on the pinned R0-dev IDs. An eligible proposal receives ONE comparison against direct S1_544. Acceptance requires tool MRA above direct, at least the frozen constant's MRA, and a paired room-bootstrap lower bound above zero. The gain threshold and lower-bound threshold are zero; bootstrap uses 10,000 draws and seed 20261119. Every comparison uses unrounded values. There is no NEAR branch, floor-response branch, alternate comparator, or pooled verdict. dev-S1 is diagnostic only and cannot change any decision.

## 3. Input authority
`DEV_AUTHORIZATION.json` copies the reviewer's verified capture/frame/category manifest and pins `COUNT_ITEMS_535.jsonl`. The builder verifies exact captures, names, frame indices, frame hashes, and resolved scratch paths. The runner requires that complete allowlist; arbitrary item files, subsets, dry manifests, and symlink escapes fail. dev-S1 has no supplied frame authority and is MISSING. `out/MISSING_INPUTS.json` lists every unavailable pilot file and fixture frame by exact expected path.

## 4. Rules and metric
`freeze_training.py` reads only captures marked train in `K1_LIFT_META.json`, verifies each label's split and teacher hash, and records every input hash. The candidate family includes both raw and NMS rules; NMS constraints are IoU .5, containment .8, and mask stride 2. Threshold candidates are .35, .5, .6, .7, .8, and .9. Maximum and second maximum follow the supplied pilot's nonempty-frame convention. The teacher contract is inherited unchanged: joint floor .2, cap 10, resolution 1008, bf16, mask threshold .5, verbatim category prompts, and the pinned checkpoint. The scorer imports the verbatim pinned `official_mra` function from N's tree; `MRA_SOURCE.json` records its location and hashes. No dev-best constant is computed by the scorer.

## 5. CPU checks
Run all Python commands through `bash cpu.sh` for nice 10, eight threads, scratch caches, and hidden GPUs. `out/COMMANDS.md` supplies the exact reproduction commands. Required checks are the self-test, all stored scores and boundary fixtures, full verified manifest, complete CPU stub, score/category report, reviewer CPU audit, reviewer invalid-DONE audit, and adversarial control tests. Stub evidence has its own namespace and never qualifies as real completion.

## 6. One look and launch
Before real inference, `count_guard.py --register` atomically creates the fixed shared `state/R0-dev-counting.json` ledger. Registration binds authorized IDs, configuration, code, settings, contract, and manifest hashes, plus an absolute Unix deadline and a cumulative budget of at most 1,800 seconds. A training rejection prohibits registration. The scorer atomically creates the category's consumed marker before opening any teacher result. A repeated or changed read fails across output directories. A crash after consumption does not restore the look. The ledger root is fixed in code and has no CLI override; all copies on this host use it. Cross-host evaluation is not authorized.

Run real inference only through `launch_count.sh`, with an admin vnice executable supplied by the launch owner. This CPU task does not validate GPU availability or the vnice executable. The runner enforces nice 10, eight CPU threads, scratch caches, registered settings, source pins, and checkpoint hash. It forbids sharding and automatic relaunch. The runtime ledger locks the category, pins the output root, preserves the absolute deadline, and charges elapsed time across explicit clean resumes. An active or failed attempt blocks restart. Alarm exceptions and checks around encoding and each prompt enforce the time budget; a native call that does not return to Python may delay the alarm. This is not a claim of an external GPU watchdog.

## 7. Completion and error reporting
A DONE file is valid only when its teacher checksum, capture, manifest, config, code, contract, settings, stub status, and frame/category coverage match. The scorer validates every capture and rejects missing payloads or incomplete provenance. It emits category zero/under/over counts and per-item evidence. Multi-category items have only item-total truth, so the report does not invent category-specific truth.

## 8. Response and rows
Training alone fixes the response and row filter in `FROZEN_CONFIG.json`. An accepted proposal would print per-category frame counts and the selected count/frame. Eligible rows must be K1 train, have truth ≥5, and have an exact selected count. A training rejection disables this response and these rows. Dev diagnostics cannot enable, alter, or select them.

## 9. Release boundary
`GPU_NEED.json` states the frozen launch decision. A rejection ends this kit without spending the R0-dev look. The missing learned/geometry pilot inputs remain MISSING; no reproduced full pilot table is claimed. Store-form, identity-head, and future-feature gates have no authority under this kit and require separate K1-training freezes and evaluation-category registration.
