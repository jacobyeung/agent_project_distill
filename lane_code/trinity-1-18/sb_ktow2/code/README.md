# Tower frames v2

Run CPU validation from this workspace with `bash scripts/cpu.sh code/dryrun.py` and `bash scripts/cpu.sh code/test_kit.py`. The CPU interpreter is `/scratch/jjyeung/envs/p1cpu/bin/python`. Run `bash scripts/cpu.sh scripts/finalize_v2.py` to rebuild the report and review archive.

`evaluate_v2.py A` prices context, `B` prices views independently, `C` reports camera diagnostics, and `heldout` consumes one held-out look after both training decisions are complete. All choices use pinned K1 train rows. The three factor names are `C32_V32_today`, `C64_V32_today`, and `C64_V64_today`, with corresponding `obj` arms only when the box kit freezes a variant. A2 uses `GTmask` as its box-rule label.

`configs/KBOX_WINNING_BOX_RULE.json` is the single box-kit hook. It names the A0 row artifact, stage-1 source and decision. A frozen object implementation requires `status=PASS`, `decision_sha256`, `pass_pointer`, `module_path`, `module_sha256`, and `callable`; the function receives capture/cache/geometry/N and returns the lifting callable. Missing references stay MISSING.

Part C reads staged step-544 records. It never substitutes `heads.pose9` for the tower output. The named `/scratch/jjyeung/devs1_r2/REQUEST.json` must provide `items`, keyed by the staged item `id`, with 32 `frames` containing `index`, `/scratch/jjyeung/devs1_frames` path, and sha256. Optional 64-frame entries require `dense_frames` and explicit `anchor_slots`. Unbound items and unavailable dense frames are skipped and counted. The current request lacks this item-level mapping.

Future GPU entry points are `scripts/run_A.sh`, `run_B.sh`, and `run_C.sh`. They require the orchestrator's code-bound `inbox/GPU_GO.json` and `inbox/SHARED_GPU_RESERVATION.json`. The latter names the single shared ledger, its sha256 and a reservation ID. The ledger lists completed GPU seconds, active reservations, the specification's order, and `next_authorized_part`. Each reservation binds part, card, workspace, code hash, hard seconds and RESERVED status. This workspace writes start/stop receipts; the orchestrator owns the shared ledger. Local admission cannot replace that ledger.

The hard stops are 0.75, 3.0 and 0.75 hours. The runner accepts one 48-GB card, limits allocation to 40 GB, records peak allocation for every capture/pass, and skips units only when their binding and output hashes match DONE.json. Incomplete attempts and HALTED receipts require operator review. No GPU scripts run during the CPU build.

`policy.read_r0dev_once` refuses any R0-dev read until `PRIMARY_ARMS.json` is frozen on K1 train, with exactly a baseline and treatment per category and pinned input hashes. It consumes an exclusive receipt before opening data and refuses another look. This kit neither freezes R0-dev arms nor reads R0-dev or official items.

Use the v2 entry points above. The copied builder scripts are not runtime entry points and are excluded from the review archive. Every produced result records its input hashes. The archive contains code, configurations, pinned inputs, CPU evidence and the report; it excludes weights, frames, GPU tensor caches and runtime fixtures.
