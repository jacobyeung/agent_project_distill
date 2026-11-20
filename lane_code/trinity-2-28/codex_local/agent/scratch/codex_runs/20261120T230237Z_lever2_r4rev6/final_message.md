**GO AFTER FIXES — close the naming-coverage gap.** Review 5’s three blockers are fixed; the requirement covering every job-written file remains unverified.

- **Remaining fix:** GPU libraries can write cache files outside the authored-source encoding layer. Those paths and contents have neither a universal deny-list guard nor production evidence. Disable those writes or enforce the naming rule before they occur. The audit explicitly acknowledges this gap: [NAMING_AUDIT.json:407](/scratch/jjyeung/orch_n30/lever1_c/r4kit/NAMING_AUDIT.json:407). Delivery text/names and guarded launch arguments/environment pass; immutable external assets retain documented exceptions.

- **CPU preflight passes inspection.** Head tensors load onto `meta`; the worker loads libraries, tokenizer/processor, image pixels and two prompt batches, then returns before resident full-model loading. Its 32 GiB address-space cap plus conservative staged-file allowance gives approximately **111 GB before overhead**, comfortably below 200G. The charged-memory stop is **110 GiB**. This is a planning bound, not a measured production peak.

- **Diagnostics fix passes.** No `/dev/null` redirection remains in the reviewed execution path. Both streams receive bounded hex journals and **16,000-byte tails**. Recorded real-fetch tests cover early failures, SIGKILL, SIGTERM, hard exit and deadlines in both modes, retaining code/signal, last stage and peak RSS. These tests substitute the namespace; controller/node death cannot guarantee a return.

- **Staging and project budget pass.** Both modes require the active **ext4 job_tmp** mount before bulk staging, including the approximately **71 GB GPU staging workload**. PLACE/REPORT document a **44,000,000-byte cumulative `/project` ceiling**: 20 MB placement, 6 MB returns, 16 MB fetches and 2 MB metadata/ledger. Reservations precede writes; repeated fetches are refused.

- **GPU host-memory safeguards pass inspection.** The request is **200G**; the forecast is **187 GB / 174.2 GiB** including RSS, page cache and buffers. Supervisors poll every 50 ms and stop at **180 GiB**. Batch/final telemetry includes host RSS and GPU allocation. Staging is safe against tmpfs residency; full-model memory safety remains conditional on the forecast and polling guard, with production peaks unmeasured.

- **Submission parity passes.** CPU/GPU use identical export policy, sanitized environment, chdir, output handling, entry script, memory and time. Only `A_M=c/g` and GPU `--gres=gpu:1` differ.

- **Scientific constraints pass.** Independently verified FROZEN `3743891f…`, checkpoint pin `5083243c…`, and all **290 pairs** differing only by the requested phrase. Greedy decoding, 64-token cap, unserved tools, scorer acceptance of `3.jsonl`/`4.json`, and complete-pair admission/retention remain intact.

- **Documents and delivery agree.** Token `e71c940a6b283`; delivery **4,247,712 bytes**, SHA-256 `4662e14cbefe9d149a3cdb7ca58bd3ff8f9030ae5e6ff98b96bc53867b67f989`. Delivered implementations match source. Forecast remains **1367.2 seconds**, with unmeasured GPU throughput assumptions.

Read-only inspection and independent hash checks; existing records report **33 passing tests**. No tests rerun.