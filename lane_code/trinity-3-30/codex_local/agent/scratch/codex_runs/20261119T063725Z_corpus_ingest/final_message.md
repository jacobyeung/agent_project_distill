Built [ingest_read.py](/scratch/jjyeung/orch_n30/corpus/tool/ingest_read.py), [corpus_score.py](/scratch/jjyeung/orch_n30/corpus/tool/corpus_score.py), [SCHEMA.md](/scratch/jjyeung/orch_n30/corpus/tool/SCHEMA.md), and tests.

- **Kit:** reads arm rows, reports, completion markers, and export metadata from directories or streamed tar members.
- **Routed:** reads plain/gzip journals, preserves tool calls and arm identities, and joins embedded or supplied task rows.
- Unrecorded values stay null, including official status, artifact IDs, units, and routed parser status. Unverified task-hash joins are marked explicitly.

**Tests:** 20 passed under Python 3.6; four real-return checks remain unrun. Actual ingest counts, bytes, SHA256s, timings, and report-score agreement are therefore still unverified.

May I run those full-source tests? Your pasted AGENTS.md requires an answer before heavy I/O; the earlier approval question remains pending.