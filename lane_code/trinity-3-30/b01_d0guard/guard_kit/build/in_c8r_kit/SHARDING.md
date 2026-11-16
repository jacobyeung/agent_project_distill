The full rehearsal retains the real single-process worker.

`native/out2/nomdg.py:477` iterates `request['keys']` without a shard argument. Its completion at line 520 pins the request and journal and records the served count. `merge` at lines 526–553 requires one complete journal, a count equal to the complete request, and parity. `admit_bundle` independently repeats those checks. `native_worker.full` invokes these paths directly.

A per-shard request would differ from the bound request. A harness-produced aggregate completion would replace the production completion path. This build chooses the brief's fallback: it adds a checked `--shards` option but refuses values above one before staging. No process coverage merge is claimed. Coverage files use parallel naming and are combined with coverage's combine API, preserving input files.
