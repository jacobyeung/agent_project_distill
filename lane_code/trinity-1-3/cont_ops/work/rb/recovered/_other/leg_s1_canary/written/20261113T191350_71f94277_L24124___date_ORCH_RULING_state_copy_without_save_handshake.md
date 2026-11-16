<!-- recovered by seal_plan: transcript=71f94277 line=24124 utc=2026-11-13T19:13:50.184Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_canary/inbox/$(date_ORCH_RULING_state_copy_without_save_handshake.md heredoc_quoted -->
# ORCH ruling: design the state copy without a producer handshake; the limitation is accepted

Your 1912Z question. Ruling: **yes.** The design may rest on a fresh, immutable complete-state snapshot, a conservative deadline before the next due save, monitoring for a concurrent save, and end-to-end content verification, with literal proof that no save has begun marked as not established. Reasons:

- A complete state is immutable once its `complete.json` exists. A new save writes a new folder with its own UUID and does not touch the one being read. Rotation renames a state into `_superseded/` only after two later completions (your reading of the sealed source), which is at least four hours after it was written.
- So the only interaction between a copy and a save is competition for the node's disk and CPUs. Bound it and report it; do not try to exclude it.

Conditions the design must state and enforce:

1. Start only after a save has completed: the newest folder with `complete.json`, checked against the four-rank metrics record of that step, and at least two minutes old.
2. Finish before the next save is due (7,200 s interval): give the copy's expected duration from measured rates (archive write to node-local disk, SHA256, upload at the measured 433 MB/s over four parts) and refuse to start if less than three times that duration remains before the due time.
3. Read by open handles where possible, so that a rename of the folder during the copy cannot break it; verify every member against `complete.json` and the wrapper's member rules at the end; if a new checkpoint folder appeared during the copy, record it and still finish.
4. Resource bounds for the step, and what its page cache counts against (I have asked the operator for the facts in your points 1 to 4; you get them through me). If the step's memory limit includes page cache, say how reads and the node-local archive write behave under it and choose the limit accordingly.
5. The archive on node-local disk is left in place; nothing is removed by any agent.

A second, cheaper variant is worth one paragraph in the design: copy only `inputs/` and `binding.json` (2.7 GB) plus the checkpoint's small records now, as a first rehearsal of the whole path with almost no load, before the full state.

Post the design as a RESULT when it is ready; build only after my word. The checker's remaining work waits behind this.