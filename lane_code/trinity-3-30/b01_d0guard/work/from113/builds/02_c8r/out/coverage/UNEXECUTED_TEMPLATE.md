# Coverage review contract

Run `review.py` with pilot, full, and test coverage files. It accepts coverage SQLite data or JSON reports. Supply `--pilot-source` or `--full-source` when the evidence came from a different source tree; only identical lines transfer to the current tree.

| File | Mode | Missed lines | Classification | Condition | Test executed |
|---|---|---|---|---|---|
| source path | pilot or full | exact executable lines | other mode only; error/refusal branch; tool or family not used by dev-S1; UNEXPLAINED | named branch or concrete reason | true or false |

The script fails for any changed executable line missing from all evidence, any executable statement of `native_worker.full` missing from full-mode evidence, or absent full-mode data. The full-function gate includes the full report tail and the `IN_JOB_ADMISSION` write. It never treats a test of admission as a completed full rehearsal. Unknown paths remain UNEXPLAINED.

Parallel-mode coverage data must be combined before review. The harness calls `Coverage.combine(keep=True)` and records that action; no sharded serving run is claimed by this build.
