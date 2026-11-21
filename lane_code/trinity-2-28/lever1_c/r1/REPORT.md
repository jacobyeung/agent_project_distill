<!-- boot-order -->
The boot gate imports all 411 audited modules before staging any checkpoint, weight or frame. It stages CPython from runtime group 0, the base environment from group 1, `v/py` and its overlay from input 3, and policy from input 4. Pre-bulk authenticated source bytes total **10,237,337,910**, including **3,829,590** package bytes. Runtime group 0's other members and all bulk inputs follow a successful boot receipt.

The pool probe writes and fsyncs 131,072 random bytes, verifies their SHA256, and reserves 131,104 bytes including the ledger write. Both CPU guards read `WRITE_TEST_BYTES` from the sealed pool writer and verify the retained file, receipt, ledger and guarded helper. The cumulative pool and metadata budgets remain unchanged.

`out/WT_OLD_5.py:53` and `:77` preserve the two stale 4 MiB expectations from the placed CPU entry. `revision8.py:49` had reduced the writer to 128 KiB. The first comparison failed deterministically after staging; no job ID, node, time, token or previous placement changed its expected size. The CPU check creates its own fresh `root/wpool/token/.wtest` through `orchard_results.write_test`, the guarded subprocess and `return_io.operate('test')`. It does not compare against a placement-time receipt. Existing tests invoked the operator directly or stopped at boot, so they never exercised this pair of guards.

`tests/test_write_receipt.py` runs the delivered BATCH CPU route and both guards with different job IDs, fresh state and three spent sibling placements. Remote staging and model execution use tiny fixtures; the pool writer, reservation ledger, guarded subprocess, bootstrap dispatch and authenticated fetch are real. The old entry reproduces the mismatch. Wrong receipt sizes, changed evidence sizes or hashes, exhausted budgets, changed settings and later preparation failures all fail with bounded diagnostics.

`a/30.json` records the CPU failure and up to 16 comparisons, with each expected/found value bounded to 2,048 characters. Supervisor recovery returns the matching job/plan record as `metadata/30.json`, alongside boot status and the traceback. A later CPU failure retains the successful write-test comparison. A failed pool subprocess records its expected and actual exit status and bounded stderr.

`tests/test_vpy.py` separately checks all 411 imports through the real pinned archives, production capture and namespace argv. The host bwrap executable, scratch bindings and sleeping watcher helper are substituted. New fixtures remain in the approved sibling directory; no files are deleted.

Token `ad07f53341bc0` supersedes the placed tokens `a6f198d3c7b20`, `a7e29d4c8f103` and `a38bd627f901e`; placement and submission use fresh paths and one-use locks.

<!-- /boot-order -->

The package submits directly to durable regular files. Both launchers pre-create and size-check `a/19`, `a/24`, and `a/21`, then call sbatch once. The submission helper accepts only the sealed `BATCH.sh` bytes, so alternate batch bodies cannot bypass the cap. No FIFO or separate collector is involved. Both submission layers preserve a nonzero return code even when stdout contains a numeric job ID.

Token: `ad07f53341bc0`. Delivery: `out/delivery.tgz`, **3,725,962 bytes**.
SHA256: `a9d25c7318374eb4a5a5af002a04a81e4e75fe4c7a9715893dc4a9550f5947c7`.

The batch's first command sets a 524,288-byte file-size limit. ERR/EXIT traps record status, line number and job ID. The shell and supervisor keep that limit; the worker restores its limit only after receiving bounded output pipes. Child sinks retain at most 131,072 bytes of durable output. Every supervisor or sink exception sets a nonzero status, including cleanup after a successful child. Recovery replaces an existing success receipt with an authenticated failure return and preserves the exception even if diagnostic saves fail. This policy makes incomplete diagnostic capture visible to the lane as FAILED. The pool write probe uses 131,072 bytes so supervisor recovery can run under the limit.

Production fetch recovers shell failures that precede publication. It requires a nonzero terminal trap record matching the requested job, creates an authenticated failure return from the bounded diagnostics, and then validates and fetches it through the normal path. Recovery files remain on local temporary disk. Existing supervisor diagnostics are preserved. Output overflow identifies the capped file with `E83`.

The **48,000,000-byte** `/project` budget includes 10 MB for delivery and installed files, 2 MB for shell/scheduler diagnostics, 2 MB for Python metadata and CPU receipts, 12 MB for pool publication, 20 MB for fetch copies/logs/summaries, and 2 MB for scheduler controls and reserve. The three shell diagnostic files together occupy at most **1,572,864 bytes**. Metadata and pool writes reserve their charges before writing; fetch refuses oversized archives and reused destinations. Bulk staging requires an ext4 `/dev/` mount assigned to the job.

CPU and GPU submissions share the sealed batch, clean environment, output handling, general partition, 50-minute allocation, 16 CPUs and 200G memory. Only the GPU request differs. The worker cap remains 30 minutes. The forecast is 23.75 worker minutes and 37.75 allocation minutes, leaving 12.25 allocation minutes; a full-cap worker plus staging and publication fits in 44 minutes. These allowances are unmeasured.

`out/REVIEW9_CHECKS.json` records the exhaustive output-route scan, pre-submission file checks, overflow enforcement and production fetch after overflow. `out/REVIEW10_CHECKS.json` records sink startup failure, premature sink exit, first-line exceptions inside and before the supervisor, and submission failure despite a numeric job ID. `out/REVIEW11_CHECKS.json` verifies production fetch after a successful child publishes an authenticated success receipt and sink cleanup then fails with a drain error, timeout, or persistent diagnostic-save error. Each fetched return reports FAILED and contains the sink exception. `out/VALIDATION.json` records all 84 tests and two import checks against the exact delivery hash, including CPU rehearsal, serving-source pins, naming, telemetry, parity and production failure fetch. No live GPU or scheduler behavior is claimed.

The delivery was built and CPU-tested locally. It has not been placed or submitted.
