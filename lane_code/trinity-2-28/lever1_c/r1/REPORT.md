The worker now writes capture 1 before staging any later RGB capture. It checks the 26-file tower source digest before large archive staging, indexes RGB members without extracting them, runs the first tower before loading the shared carrier, and reuses that result for the first depth record. The writer flushes each record before the next capture begins.

Token: `a784b94c2e6af`. Delivery: `out/delivery.tgz`, **3,704,563 bytes**.
SHA256: `fba95b8b0b00c87ec7900817a0977084e18efed504b8918e24eccf9224302974`.
`PLACE.md`, `out/BUILD.json`, and the placement descriptor describe this same rebuild.

`runtime/s.py` implements the early source gate and authenticated per-capture RGB extraction. `external_inputs.py` installs the gate ahead of large archive copies and binds the first capture. `runtime/w.py` runs the first tower ahead of carrier loading and preserves its exact output for the unchanged scale/geometry path. `depth_format.py` flushes each committed record. All retained serving/evaluator source bytes remain unchanged.

`runtime/m.py` writes per-capture elapsed seconds, sampled RSS peak, cumulative kernel process RSS high-water mark, and GPU maximum allocated bytes since capture start to `metadata/5.json`. It snapshots once per second and at phase transitions, including active/incomplete captures, and keeps a bounded log in `metadata/13.json`. Both files use atomic a0-hex publication. Capture-1 timing includes shared worker startup. Sampling can miss subsecond RSS peaks; the kernel high-water mark is cumulative across the worker and exact at each snapshot. Abrupt death can lose the last heartbeat. Existing bounded traceback receipts remain enabled.

The forecast is **23.75 worker minutes**, below the 30-minute cap, and **37.75 allocation minutes**, below 40 minutes. The calculation adds six minutes of shared loading and one minute of indexed staging/telemetry to the 16.75-minute T1 replay, then allows ten minutes for shared staging and four for publication. Margins are 6.25 worker minutes and 2.25 allocation minutes. These allowances remain unmeasured.

The first served scale requires the shared carrier/private-head weights, tower weights, processor assets, and runtime environment. Their authenticated archive copies and preparation remain up front. Full authentication also reads later RGB bytes co-packaged in those archives once; extraction and image loading are capture-local. Missing/corrupt vendor code fails before this work. A two-minute bound for arbitrary GPU/tower failures from allocation start remains unverified because shared staging can take longer.

Validation: the rebuilt payload compiles and all seven shell scripts pass syntax checks. The full CPU suites, real rehearsal deny-list scan, CPU-double capture, and new ordering/memory regressions are pending a workspace-cap resolution. Previous test results are not evidence for this delivery. No GPU, network, placement, or submission ran.
