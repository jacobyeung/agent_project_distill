# D0 milestone reader

The runner stages D0 milestone exports and reads all 2,275 e193c2a3c direct items sequentially on one card. `--model-slot` remains available. The default multi-family read covers main (1,525), away (150), forward/toward (150), and camera (450).

## Export admission

`logical_artifact` admits only runs `469ddece` and `359fcc3c` in lineage `8865619b`, at any positive step, plus the fixed parent m200 artifact. `stage-export` defaults to run `359fcc3c` and requires a completed local tar and `.done` JSON with `object`, `bytes`, and whole-tar `sha256`.

The command hashes the tar before extraction and rejects `.part` files, symlinks, absolute/traversing member paths, links, special files, duplicate names, file/directory collisions, and unexpected layout. It requires one `m<step>/` tree containing `artifact.json`, `heads.pt`, and `full_weights/full_weights.json`. Additional files belong only under `full_weights/`. It checks disk reserve, writes an extraction receipt, and refuses an existing milestone or receipt. Failure retains all evidence.

`work/recv_export.sh` extracts the step-544 stream directly into the `469ddece` run directory. That staged directory contains `m544/artifact.json`, `m544/heads.pt`, and `m544/full_weights/`; the artifact points to the same logical full-weights manifest. `INPUT_PINS_T5B.json` records the script and metadata hashes and immediate directory evidence. No original step-544 tar or arriving D0 tar was scanned. The observed script and tree support the layout assumption; the D0 tar must pass admission when it arrives. An outer run directory, bare artifact, different step, or other top-level content is refused before extraction.

After extraction, the runner invokes the unchanged, SHA-pinned `export_check.py` and `common.py` inside the existing CPU namespace. Header-only mode records `HEADER_ONLY_NOT_VERIFIED`; `--full` records `VERIFIED` after shard hashing. Both compare tensor headers against the staged base. The receipt also records the artifact SHA, command, checker result, and failure. Header-only does not replace the production reader's full export verification.

## Packets and summaries

`read --all-families` and `read --families main,away,forward,camera` run one fresh process per family, sequentially on the selected card. Omitting all family selectors has the same default. Full families require no `--ids` or `--first`; multi-family reads reject either selector. `--family` retains explicit subset support.

`e193_items.json` pins the accepted IDs, task types, cells, task-file hashes, and source hashes. Each full family must match it before GPU admission, and the worker checks its binding. D0 uses the same duplicate layout, 32 anchors, true timing, greedy ON16k, B2048, B4096, and answer-cap policy. Each family retains its accepted packet at `<out>/<family>/direct/<family>/`, plus its original label-specific report exports.

The milestone summary reports B2048 scores by family and task, item/scored counts, card identity, execution and full-invocation wall times, and measured journal token rates. It preserves the accepted reporting rules:

- Main's primary aggregate scores the 1,375 primary rows against released answers.
- Route planning's 150 rows have no released-answer primary labels. Its task score uses own ground truth and remains outside the primary aggregate.
- Away, toward, and camera use own ground truth. Away and toward remain separate.
- JSON also retains all-item own-ground-truth means. All aggregates are item-weighted percentages.

A failure or yield stops subsequent families without retry. The root summary marks incomplete work, and each attempted packet retains its evidence. The runner checks the yield glob before each family; the existing process-group watcher handles yielding during execution. Token rates use generated tokens divided by summed request latency, with budget reuse excluded. They are not measured card throughput.

## Cost model

`cost --proof DIR` reads the three completed proof arms, journals, budget receipts, and EXIT wall time. It prints and writes `DIR/COST.json`. Per-arm seconds per item sum request latency over all proof items; reused ON answers add zero budget-generation time. The one-card projection multiplies measured EXIT seconds per item by all 2,275 e193 items. Family/task counts remain explicit, and per-arm wall allocations are labeled estimates.

The fixture has two items, 60 seconds of total wall time, 10 ON seconds per item, and 5 seconds per item in each budget arm after reuse. It projects 1,137.5 minutes for 2,275 items. This number tests arithmetic; it is not a measured Trinity estimate. The model assumes that the proof mix, concurrency, and setup cost per item transfer to full families. It excludes transfer, staging, and outer preflight. Failed runs and missing timing evidence are refused.

## Validation and limits

All 216 CPU tests pass (`TESTS_T5B_FULL_02.log`). The final targeted checks are recorded in `TESTS_T5B_FINAL_02.log`. Trinity system Python also runs the cost fixture successfully (`COST_FIXTURE_T5B.json`). Tests cover the fixed run allowlist, archive authentication and unsafe-layout refusal, retained checker failures, sequential family execution, early and between-family yields, primary-score agreement with accepted reports, full D0 CPU bindings for all four families, cost arithmetic/reuse, and CLI behavior. A miniature BF16 fixture exercises the unchanged export checker in header-only and full modes, including a bad shard pin. The checker-command fixture verifies a CPU namespace invocation without the llguidance overlay.

The existing yield/audit tests retain their assertions and declare a miniature item inventory for their fake reader. The bundle test includes `milestone.py` and `e193_items.json`. The tested parent/f17 bindings remain covered.

The root's staging record remains incomplete: runtime_0, runtime_2, and base are missing. This session ran no real namespace, D0 archive stage, full-weight verification, GPU proof, or milestone read. The D0 export bytes and real cost remain unverified. Camera execution still depends on the reconstructed wrapper described in `REPORT_T5.md`. Every family retains its own model copies and checks the 200 GiB free-space floor.

Only `build_t5/` was edited. No GPU, SSH, network, Git, download, deletion, heavy-I/O command, or production command ran. `DIFF.md` records changed lines against read-only `build/`, classified as PATH/ENV or BEYOND. The documentation applies `no-archaeology`; no borderline historical prose was retained except the explicitly requested baseline comparison in the diff ledger.
