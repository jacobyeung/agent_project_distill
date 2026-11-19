# Corpus v1

`ingest_read.py ingest --source RETURN --read-id ID --out ROOT` writes
`reads/ID.jsonl.gz` and `index/ID.json`. The root must be inside this tool workspace.
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
| `item_id`, `question_type` | Original item ID as text; recorded question category. |
| `question`, `options`, `room`, `scene` | Original task text, choices, room and scene identifiers; values retain their original JSON types. |
| `truth` | `scored`: ground truth (fallback: task `answer`); `released`: released answer; `released_in_options`: recorded released-choice membership; `stratum`, `scorer`, `units`: recorded scoring provenance. |
| `arms` | Map of distinct scored arms. Kit directories `0`, `budget_2048`, `budget_4096` become `full`, `B2048`, `B4096`. Nested `at_4096` remains in raw; it is not a separate budget run. Routed names use row arm, then output arm, then mode; non-default mode/intervention append a canonical JSON suffix. |
| Each arm | `answer`: extracted prediction, never kit's truth-bearing `answer`; `response_text`: final response; `trace`: full `raw_generation` or routed `output.text`, including inline tool responses; `tool_calls`: recorded structured calls, preserving every key; `finish_reason`, `output_tokens`, `prompt_tokens`, `hit_cap`, `parse_failed`, `score`, `scores`: recorded generation/scoring values. Routed token count is token-list length. Routed cap includes forced decoding budget and max-call termination. Missing parser status stays null. |
| Routed arm extras | `identity` preserves row `arm`, `mode`, `intervention`; `output_arm` preserves the serving arm. If no extracted answer was recorded, `answer` and `response_text` use the explicit segment after `</think>`, removing the EOS marker. This is text extraction, not rescoring. Without that segment they stay null. |
| `serving` | Kit models/scope; routed identity, settings and cards; supplied fields override extracted fields. |
| `reader` | `format`, `build`, sorted logical `source_files`. Routed `task_hash_verified` distinguishes an exact native-task hash match from an unambiguous ID join. |
| `job_id`, `date` | Recorded or supplied job identifier and date; no ingestion timestamp is substituted. |
| `raw` | Each arm holds its original parsed row without dropped or changed fields, including token IDs and nested budgets. `input` holds the joined task; `mapping` holds routed binding evidence; `source` preserves each arm's logical file and original directory; `records` holds supplementary kit item/report rows. “Verbatim” means JSON values, not original whitespace/key order. |

Each index entry contains supplied metadata (`purpose`, `reported_by`, `notes`,
`arms` included), `provenance` for metadata precedence (CLI > meta > return > absent),
`status`, `partial`, `partial_reasons`, `item_count`, `arm_stats` (items, scored,
mean_score), family/type counts, `output` (relative path, SHA256, bytes), and
`tool_version` (ingester SHA256). `sources` records every consumed source's SHA256
and bytes, including whole archives and selected member bytes before inner gzip
decoding. `raw_metadata` preserves document fields; streamed item/report arrays
live beside their corresponding items. `unparsed_records` preserves torn JSONL
lines when explicitly archiving a partial return.

Completion requires root markers, kit family markers and all three arm counts,
or routed read/shard counts. False completion flags, failed row statuses and short
counts return exit 2 unless `--archive-partial`. Missing or ambiguous task joins
fail explicitly. Gzip uses level 6, mtime 0 and no filename; canonical JSON lines
sort by `(family, item_id)`. Identical existing bytes print `SAME`; conflicting
bytes return exit 3. Publication uses a lock and atomic rename. Existing index
provenance stays immutable on `SAME`. Scratch databases and abandoned temporary
files remain under `t/` or the chosen output root; no deletion commands run.

`lost --meta FILE` records only reported evidence with status `lost` or
`orchard_only`; it creates no read. `index --out ROOT` rebuilds `INDEX.jsonl`,
sorted by read ID. `corpus_score.py READ --arm B2048 --by question_type` averages
stored non-null scores. Optional `--family`, `--stratum`, `--question-type` filters
match report populations. `--compare FILE --key dotted.path` reports `MATCH` or
`DIFF` at 1e-6 fraction tolerance; `_pct`/`percent` keys and values above 1 scale
by 100. It never silently selects a report's population.

Run `python3 -m unittest` for synthetic tests. After required heavy-I/O approval,
run `CORPUS_REAL_TESTS=1 python3 -m unittest` to include the named real returns,
with each ingestion limited to 1800 MiB of address space. All fixtures and output
stay under `t/`; the real-ingest metrics are saved to `t/real_metrics.json`.
