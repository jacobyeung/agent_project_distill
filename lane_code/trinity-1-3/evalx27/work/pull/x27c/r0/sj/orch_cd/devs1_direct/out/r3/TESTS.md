All 72 CPU regression tests pass: 58 adapter/label/report tests and 14 timing tests. Both reviewed kits also pass the 20-capture metadata proof (40 comparisons total). `TESTS.log` contains the test output and three printed dev/training examples per checkpoint.

- Nine pinned training-row examples also pass stored timestamp, total-frame and two-layout checks in `TRAINING_TIMING_CHECK.json`.
- The timing tests reject fps=1, unknown capture authority, missing authority fields, changed indices, changed timestamps and changed totals.
- Actual HF `VideoMetadata.timestamps` equals index/fps for every capture. CP1 duplicate receipts match the training layout’s repeated timestamps exactly. ARKit lower bounds are explicit.
- Both proofs execute the actual Qwen3VL temporal-patch timestamp method, the kit training layout function and the official VSI metadata path with an injected small RGB decode boundary. No production videos or model weights are read.
- The item list, strata, cell membership and exclusions are byte-identical to pass 2. Every prompt, label, option and provenance field in task/audit rows is byte-identical after removing only timing fields. PNG pins and anchor order are unchanged.
- Both dry binds contain 1,525 tasks, 1,375 primary rows and 150 unavailable routes. Prompt-context inventories are identical between the reviewed kits and pass 2. Each copied evaluator closure matches the reviewed source byte-for-byte.
- Old cell versions, old bindings and old-fps journal rows are refused. Dry bindings cannot launch. Synthetic PNG tests still verify frame order, dimensions, byte pins, receipt loading and tamper rejection.

Validation ran with `/scratch/jjyeung/envs/p1cpu/bin/python -I -s` on CPU. No GPU, SSH, Git, network, deletion, move, /home access or /data access was used. The proof does not establish production pixel or token parity; live binding and the kits’ run-host parity gates remain required.
