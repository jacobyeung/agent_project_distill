NO-GO

Verified defects:

1. **Streamed source rows can disappear.** [ingest_read.py:212](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:212), [ingest_read.py:593](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:593). A valid kit containing item `q` plus report row `{"key":"devrows:orphan","extra":"KEEP"}` exits 0; that report row appears nowhere in the output or index. The parser removes arrays from `raw_metadata`, but emission preserves only selected matching rows. In the actual A4 output, the manifest row for `devs1cam-0020d0cefc26c693abeb6c4e5951cc07` is also not preserved verbatim: its `room_key` is absent from the selected `raw.input`, and the manifest’s `items` array is absent from the index.

2. **Routed joins accept contradictory task hashes.** [ingest_read.py:461](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:461). Supply mapping hash `digest({"id":"q","question":"Right question","answer":"A"})`, but only task `{"id":"q","question":"Wrong question","answer":"B"}`. Ingestion exits 0 with status `complete`, question `"Wrong question"` and truth `"B"`. Setting `task_hash_verified:false` does not prevent the incorrect join.

3. **Kit validation accepts incompatible budget populations and task identities.** [ingest_read.py:399](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:399), [ingest_read.py:412](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:412), [ingest_read.py:587](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:587). With expected count 1, give `full`/`B4096` item `q` and `B2048` item `other`: ingestion reports `complete` with two items, each missing arms. Alternatively, use ID `q` throughout but different questions/truths in B2048: ingestion merges them and assigns B2048’s question/truth to every arm.

4. **Colon-containing IDs lose supplementary rows and scores.** [ingest_read.py:186](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:186). Give every kit arm `id:"namespace:q"` and its B2048 report row `{"id":"namespace:q","scores":{"answer":0.25}}`. Ingestion exits 0, but `raw.records` is empty and B2048’s `scores` is null. Record indexing strips the prefix from actual IDs, while normalized IDs retain it.

5. **An arm named `input` overwrites the original task.** [ingest_read.py:600](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:600). A valid routed row with `arm:"input"` exits 0, but `raw.input` contains the generation row instead of the joined task. Arm names share the namespace used for reserved raw fields.

6. **Failed supplementary rows pass completion checks.** [ingest_read.py:391](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:391). Add `{"id":"q","family":"main","budget":2048,"status":"failed"}` to root `ITEMS.jsonl` of an otherwise complete kit. Ingestion exits 0 with status `complete`. A matching report row with `status:"failed"` also passes. Only generation rows receive `check_row()`.

7. **Zero-row failed returns succeed with `--archive-partial`.** [ingest_read.py:731](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:731). A return containing only `SPEC.json` declaring a family and `FAILED.json`, without generation rows, exits 0 and publishes an empty gzip. The existing staged `469ddece_s544_R0_direct_aed15a8b7cb_partial` demonstrates this outcome: **0 items, 20-byte gzip, status `partial`**.

8. **Routed population extraction assumes manifest filename `3.json`.** [ingest_read.py:438](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:438). Put a valid task manifest with `name:"room134"` at `metadata/reads/0/metadata/a/4.json`, without a supplied `--set`. Ingestion succeeds but normalizes `set` to null. The staged room134 metadata confirms this manifest layout exists. This contradicts [SCHEMA.md:15](/scratch/jjyeung/orch_n30/corpus/tool/SCHEMA.md:15).

9. **The documented output-directory restriction is not enforced.** [SCHEMA.md:4](/scratch/jjyeung/orch_n30/corpus/tool/SCHEMA.md:4) requires output inside the tool workspace; [ingest_read.py:40](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py:40) accepts any `/scratch/` or `/dev/shm/` path. The supplied `corpus/stage` output location is one concrete counterexample.

Verified with in-memory reproductions and read-only source/output inspection. No files changed.