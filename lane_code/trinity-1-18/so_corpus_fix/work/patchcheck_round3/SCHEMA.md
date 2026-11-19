# Corpus v1

`ingest_read.py ingest --source RETURN --read-id ID --out ROOT` writes
`reads/ID.jsonl.gz` and `index/ID.json`. The output root may be any path under `/scratch/` or `/dev/shm/`.
Use `--inputs DIR_OR_TGZ` for routed task rows. A fetched directory prefers its
`result.tar.gz`; an explicit `x/` directory reads those files directly. Tar members
stream without extraction. Multiple routed reads produce `ID.r0`, `ID.r1`, etc.;
`--read-index 1` writes only that read as `ID`. Unknown values are JSON `null`.

| Item field | Meaning |
|---|---|
| `schema`, `read_id` | Literal `corpus-v1`; caller's stable evaluation identifier. |
| `official`, `partial` | Declared official status, or null; detected incomplete return. Official status is never inferred from a scorer's name. |
| `export` | `run`, `step`, `artifact_id`, `artifact_sha256`, `generation`; export binding, with nulls for absent identifiers. Additional supplied export fields survive. |
| `vehicle`, `set`, `family` | Supplied vehicle and population; kit directory family. Routed set comes from its embedded task manifest; family stays null when absent. |
| `item_id`, `question_type`, `category` | Exact original item ID as text (including colons); recorded question type; offread report category. Category uses the longest exact or underscore-prefix match against `report/B2048.json` group names; original fields remain in raw. |
| `question`, `options`, `room`, `scene` | Original task text, choices, room and scene identifiers; values retain their original JSON types. |
| `truth` | `scored`: ground truth (fallback: task `answer`); `released`: released answer; `released_in_options`: recorded released-choice membership; `stratum`, `scorer`, `units`: recorded scoring provenance. |
| `arms` | Map of distinct scored arms. Kit directories `0`, `budget_2048`, `budget_4096` become `full`, `B2048`, `B4096`. Nested `at_4096` remains in raw; it is not a separate budget run. Routed names use row arm, then output arm, then mode; non-default mode/intervention append a canonical JSON suffix. |
| Each arm | `answer`: extracted prediction, never kit's truth-bearing `answer`; `response_text`: final response; `trace`: full `raw_generation` or routed `output.text`, including inline tool responses; `tool_calls`: recorded structured calls, preserving every key; `finish_reason`, `output_tokens`, `prompt_tokens`, `hit_cap`, `parse_failed`, `score`, `scores`: recorded generation/scoring values. Routed token count is token-list length. Routed cap includes forced decoding budget and max-call termination. Missing parser status stays null. |
| Routed arm extras | `identity` preserves row `arm`, `mode`, `intervention`; `output_arm` preserves the serving arm. If no extracted answer was recorded, `answer` and `response_text` use the explicit segment after `</think>`, removing the EOS marker. This is text extraction, not rescoring. Without that segment they stay null. |
| `serving` | Kit models/scope; routed identity, settings and cards; supplied fields override extracted fields. |
| `reader` | `format`, `build`, sorted logical `source_files`. Routed `task_hash_verified` records a verified mapping hash; `task_join_rule` records `exact`, `unambiguous_id`, or the documented room134 rule below. |
| `job_id`, `date` | Recorded or supplied job identifier and date; no ingestion timestamp is substituted. |
| `raw` | `arms.<arm>` holds each original parsed row without dropped or changed fields, including token IDs and nested budgets. `input` holds the joined task; `mapping` holds routed binding evidence; `source` preserves each arm's logical file and original directory; `records` holds matching source rows, including supplementary items, reports, task manifests and mappings. Reserved fields cannot collide with arm names. Records index exact IDs. Key-only `devrows:<id>` records can match the explicit benchmark-key alias; an actual `id` is never stripped. “Verbatim” means JSON values, not original whitespace/key order. |

Each index entry contains supplied metadata (`purpose`, `reported_by`, `notes`,
`arms` included), `provenance` for metadata precedence (CLI > meta > return > absent),
`status`, `partial`, `partial_reasons`, `item_count`, `arm_stats` (items, scored,
mean_score), family/type counts, `output` (relative path, SHA256, bytes), and
`tool_version` (ingester SHA256). `sources` records every consumed source's SHA256
and bytes, including whole archives and selected member bytes before inner gzip
decoding. `raw_metadata` preserves document fields; streamed item/report arrays
live beside their corresponding items or in the per-read orphan sidecar. `unparsed_records` preserves torn JSONL
lines when explicitly archiving a partial return.

Completion requires format-specific markers: kit root/family markers, routed root/read/shard markers, offread root COMPLETE, or native root and paired-results COMPLETE. Kit/offread require equal populations, consistent question/truth and exact expected counts in all three arms. Native requires exact expected counts per arm. False completion flags, failed row statuses and short
counts return exit 2 unless `--archive-partial`. Missing or ambiguous routed task joins fail explicitly. A contradictory mapping hash always returns exit 2, even with `--archive-partial`. Zero result rows always return exit 2. Gzip uses level 6, mtime 0 and no filename; canonical JSON lines
sort by `(family, item_id)`. Identical existing bytes print `SAME`; conflicting
bytes return exit 3. Publication uses a lock and atomic rename. Existing index
provenance stays immutable on `SAME`. Scratch databases and abandoned temporary
files remain under `t/` or the chosen output root; no deletion commands run.

For new read IDs, pass `--review2-checks` explicitly, including through
`add_read.sh`. The switch defaults off to preserve the legacy output path.
With this switch, native validates declared arm names and key sets. Missing arms
and subsets of declared keys produce partial issues (exit 2 unless
`--archive-partial`, then `partial=true`). Undeclared arms, extra keys, invalid
or contradictory declarations, and conflicting labels always refuse ingestion.
Kit report lookup prefers exact IDs, then key-only `devrows:<id>` aliases;
actual-ID rows cannot supply alias scores. All eligible report rows at the
selected precedence must agree on `scores`, or ingestion refuses even with
`--archive-partial`. Original rows remain in raw records or the orphan sidecar.

`lost --meta FILE` records only reported evidence with status `lost` or
`orchard_only`; it creates no read. `index --out ROOT` rebuilds `INDEX.jsonl`,
sorted by read ID. `corpus_score.py READ --arm B2048 --by question_type` averages
stored non-null scores. Optional `--family`, `--stratum`, `--question-type` filters
match report populations. `--compare FILE --key dotted.path` reports `MATCH` or
`DIFF` at 1e-6 fraction tolerance; `_pct`/`percent` keys and values above 1 scale
by 100. It never silently selects a report's population.

Run `python3 -m unittest t.test_review` for review regressions and
`CORPUS_REAL_TESTS=1 python3 -m unittest t.test_real_round1` for the approved real
returns, each limited to 1800 MiB of address space. Fixtures and outputs stay
under `t/`; final metrics and headlines live in `t/real/validated/`.

Every consumed streamed row is preserved in an item's raw data or in
`index/ID.orphans.jsonl.gz`. Each sidecar line contains `source`, the original
array `field` (null for JSONL), and the unchanged `row`. The index records
`consumed_row_count`, `orphan_count`, and sidecar path/bytes/SHA256. Orphans include
unmatched inputs and rows belonging to other reads; no consumed evidence is
silently dropped when selecting a read. All consumed rows receive status checks.
JSON values are limited to 128 MiB; SQLite staging keeps whole reads off the heap.

Routed joins require the exact canonical task hash when a mapping provides one.
The only transformed hash rule is the supplied reader's
`h1eval/room134.py:bind`: for an R0-dev room-size task, hash
`dict(row, answer=row["ground_truth"])`. The hash must still match exactly.
`raw.input` retains the unmodified source row, and `reader.task_join_rule` records
`room134.bind:answer=ground_truth`. Submission-root `--inputs` selects its `src/`
directory, including the explicit source symlink used by B5. Without a hash, only
an unambiguous task-ID join is allowed. Manifest names come from named documents
containing task rows, independent of their filename.

`offread` reads root SPEC/COMPLETE, `a0/results/0/items_a0.jsonl`, the sibling
`budget_2048.jsonl` and `budget_4096.jsonl`, supplementary budget metadata and
`report/*.json`. It also accepts budget directories with `0/items_a0.jsonl`.
It maps predictions, traces, tokens and scores through the direct/kit fields;
SPEC supplies step/artifact SHA256 and the launcher supplies Orchard job/date.
Unknown export run/artifact ID and unrecorded structured calls stay null.

`native` streams `native/paired/results/items.jsonl` and the arm arrays in
`native/R1.json`, preserving both scripted and unflagged arms. Identical
journal/report duplicates share an arm; conflicting duplicates fail. `decode.text`,
`decode.calls`, `decode.finish`, `decode.generated_tokens`, `decode.prompt_tokens`,
row `scores.answer`, `capped` and `no_answer` supply normalized generation fields.
Every call/response/audit key survives. Scored geometry refusals without decoding
keep null text/calls and their recorded zero scores/token counts. Optional
`--inputs` joins native `devrows:<task id>` keys to task IDs and rejects conflicting
question/truth candidates. Without task inputs, absent question/truth stay null;
no external task paths are followed automatically. COMPLETE supplies step/artifact
SHA256; ORCHARD_NATIVE supplies job/date; request fields describe serving.

With `--review2-checks`, native compares all supplied task-candidate fields and
shared row/task identity fields before joining. An unresolved key with explicit
`--inputs` always refuses, even with `--archive-partial`. Report rows in `arms.X`
without an `arm` field use X for validation and normalization; their original raw
rows remain unchanged. Conflicting journal/report duplicates always refuse.
Compatible additive fields in unselected tasks remain in the orphan sidecar;
they are not merged into `raw.input` or normalized fields.

`--mean-of-types` averages question-type means within each `--by` group, then
averages those group means. Original item-weighted means remain in
`item_mean_score`. Both official headlines use
`--arm B2048 --by category --mean-of-types`: VSI averages six task categories;
ReVSI averages subtypes within five categories and then averages those categories.
Compare against `report/B2048.json` keys `six_task_mean.score` and
`five_category_mean.score`, respectively.

For the a8102c3207b main primary population, stored `score` matches
`summary.primary.released_answer`; the separate `own_gt_by_stratum.primary`
column uses a different label. Both report score columns remain in `scores`/raw.
The provided tar and `x/` contain different supplementary ITEMS rows, so their
lossless corpus hashes differ even though their 3,120 generation records match.
