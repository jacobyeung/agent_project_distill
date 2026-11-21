<!-- boot-order -->
The boot gate stages the complete CPython tree from runtime group 0, the base environment from group 1, the interpreter wrapper and overlay from input 3 (`a4.tar`), and policy from input 4. It then boots the real worker and imports all 411 audited modules before staging any checkpoint, weight or frame. Runtime group 0's other members, group 2, and inputs 0–2 wait for the successful boot receipt. `boot_order.py:30` selects these archives; `runtime/boot.py:105` authenticates and filters their members.

The missing executable came from selecting input 2 (`a2.tar`) for `v/py`. That archive contains no `v/` members. Input 3 (`a4.tar`, SHA256 `c867d40addcf35c55db1ec511c4dc2b8a4cec80cef9003be93179ef82c30b0ea`) contains the 160-byte executable shell wrapper `v/py`, the 443-byte `v/boot.py`, and the overlay. The wrapper executes the base environment's `bin/python` symlink, which resolves through the uv namespace bind to the staged CPython tree. The failure was an omitted archive, not a dangling `v/py` symlink.

Pre-bulk authenticated source bytes total **10,237,337,443**: package **3,829,123**, runtime groups 0–1 **10,088,151,040**, overlay and policy **145,285,120**, and pinned bwrap **72,160**. Group 0 is streamed and only CPython is materialized. These source-read bytes include discarded mixed-archive members; no bulk member is copied or extracted before boot. Production pre-bulk seconds remain unmeasured; metadata/25.json records them for each job.

`tests/test_vpy.py` uses the real pinned archives through the delivered `job.stage`, reproduces the old missing-executable failure, and tests the corrected worker through the production bwrap constructor. The local bwrap executable and an extra same-location bind expose the scratch fixture. The authenticated vnice script runs with its terminator helper bound to an inert script so the test cannot signal processes or delete marker files. The test audits staged links, the ELF loader/shared libraries, and the worker closure; `out/VPY_CHECKS.json` records its result. Missing-module tests also require zero bulk bytes and an authenticated failure through production fetch.

Token `a7e29d4c8f103` supersedes the placed token `a6f198d3c7b20`; placement and submission use fresh paths and one-use locks.

The pinned-archive regression passed: 411 modules imported, 2,104 symlinks resolved, and the ELF loader/shared-library audit passed. The old selection reproduced the execvp failure; both cases staged zero bulk bytes.

<!-- /boot-order -->

The package submits directly to durable regular files. Both launchers pre-create and size-check `a/19`, `a/24`, and `a/21`, then call sbatch once. The submission helper accepts only the sealed `BATCH.sh` bytes, so alternate batch bodies cannot bypass the cap. No FIFO or separate collector is involved. Both submission layers preserve a nonzero return code even when stdout contains a numeric job ID.

Token: `a7e29d4c8f103`. Delivery: `out/delivery.tgz`, **3,700,123 bytes**.
SHA256: `86836622ee2b2b002510448d5777cfd3023817893b6f3d2649c21a716f055285`.

The batch's first command sets a 524,288-byte file-size limit. ERR/EXIT traps record status, line number and job ID. The shell and supervisor keep that limit; the worker restores its limit only after receiving bounded output pipes. Child sinks retain at most 131,072 bytes of durable output. Every supervisor or sink exception sets a nonzero status, including cleanup after a successful child. Recovery replaces an existing success receipt with an authenticated failure return and preserves the exception even if diagnostic saves fail. This policy makes incomplete diagnostic capture visible to the lane as FAILED. The pool write probe uses 131,072 bytes so supervisor recovery can run under the limit.

Production fetch recovers shell failures that precede publication. It requires a nonzero terminal trap record matching the requested job, creates an authenticated failure return from the bounded diagnostics, and then validates and fetches it through the normal path. Recovery files remain on local temporary disk. Existing supervisor diagnostics are preserved. Output overflow identifies the capped file with `E83`.

The **48,000,000-byte** `/project` budget includes 10 MB for delivery and installed files, 2 MB for shell/scheduler diagnostics, 2 MB for Python metadata and CPU receipts, 12 MB for pool publication, 20 MB for fetch copies/logs/summaries, and 2 MB for scheduler controls and reserve. The three shell diagnostic files together occupy at most **1,572,864 bytes**. Metadata and pool writes reserve their charges before writing; fetch refuses oversized archives and reused destinations. Bulk staging requires an ext4 `/dev/` mount assigned to the job.

CPU and GPU submissions share the sealed batch, clean environment, output handling, general partition, 50-minute allocation, 16 CPUs and 200G memory. Only the GPU request differs. The worker cap remains 30 minutes. The forecast is 23.75 worker minutes and 37.75 allocation minutes, leaving 12.25 allocation minutes; a full-cap worker plus staging and publication fits in 44 minutes. These allowances are unmeasured.

`out/REVIEW9_CHECKS.json` records the exhaustive output-route scan, pre-submission file checks, overflow enforcement and production fetch after overflow. `out/REVIEW10_CHECKS.json` records sink startup failure, premature sink exit, first-line exceptions inside and before the supervisor, and submission failure despite a numeric job ID. `out/REVIEW11_CHECKS.json` verifies production fetch after a successful child publishes an authenticated success receipt and sink cleanup then fails with a drain error, timeout, or persistent diagnostic-save error. Each fetched return reports FAILED and contains the sink exception. `out/VALIDATION.json` records all 73 tests and two import checks against the exact delivery hash, including CPU rehearsal, serving-source pins, naming, telemetry, parity and production failure fetch. No live GPU or scheduler behavior is claimed.

The delivery was built and CPU-tested locally. It has not been placed or submitted.
