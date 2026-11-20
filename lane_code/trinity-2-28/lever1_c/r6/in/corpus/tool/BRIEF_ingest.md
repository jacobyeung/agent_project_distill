# Build `ingest_read.py`, `corpus_score.py`, `SCHEMA.md` and tests (workspace: /scratch/jjyeung/orch_n30/corpus/tool)

## Goal
A durable corpus of every read (evaluation run) of our student VLM. A "read" returns, per item: the question, the truth, the answer per scored arm, the full generated trace with its tool calls and tool responses. Today they sit in scattered return folders. `ingest_read.py` turns ONE read return into ONE file `reads/<read_id>.jsonl.gz` (one JSON line per item, fixed schema) plus one index line. It must lose nothing: every original record is kept verbatim in a `raw` object beside the normalised fields.

## Hard rules
- Write only inside /scratch/jjyeung/orch_n30/corpus/tool (code, tests, test output under tool/t/). Read sources in place, never modify them. No network, no ssh, no git, no deletion outside tool/t/, no GPU. Python 3 standard library only (python3 on this node; also must run under Python 3.6+: no walrus, no dataclasses, no `list[int]` hints). Keep RAM under 2 GB: stream files line by line; read tar members with `tarfile` streaming, never extract outside tool/t/.
- No recursive search outside the source folders named below; never touch /home or /data*.

## CLI
```
ingest_read.py ingest --source <return dir or result.tar.gz> --read-id <id> --out <corpus root> [--format auto|kit|routed]
                [--meta meta.json] [--set S] [--vehicle V] [--official] [--purpose TEXT] [--reported-by TEXT] [--job-id N]
                [--inputs <dir/tgz holding the task rows, for formats whose items lack question text>] [--archive-partial]
ingest_read.py lost --read-id <id> --out <root> --meta meta.json      # INDEX-only entry: status lost / orchard_only, with the numbers records report
ingest_read.py index --out <root>                                     # rebuild <root>/INDEX.jsonl from <root>/index/*.json (sorted by read_id)
corpus_score.py <reads/X.jsonl.gz> [--arm A] [--by question_type|family|set] [--compare <summary.json> --key <dotted.path>]
```
`--meta` JSON may carry any of: read_id, set, vehicle, official, export {run, step, artifact_id, artifact_sha256}, arms, serving {arm, selector, tower versions...}, reader_build, job_id, date, purpose, reported_by, notes. CLI flags override meta; values auto-extracted from the return (below) fill the rest; record which source each top-level value came from in `provenance`.

## Behaviour
- Deterministic output: items sorted by (family, item_id); `json.dumps(sort_keys=True, separators=(',',':'), ensure_ascii=False)`; gzip with mtime=0 and level 6, so the same source gives byte-identical output.
- Idempotent: if `reads/<id>.jsonl.gz` exists with the same sha256 -> print SAME, exit 0. Different -> refuse, exit 3 (never overwrite). Write to a temp name then rename.
- Refuses a partial return (exit 2) unless `--archive-partial`, which writes it with `partial: true` and index status `partial`. Partial means: missing completion markers, `complete` false, completed != expected, any row whose status is not complete, or row counts below the summary's expected counts.
- Records sha256 + bytes of every source file it read (`sources` list in the index line) and the output's sha256/bytes, item count, per-arm item counts and mean score, families, question-type counts, tool version (sha256 of ingest_read.py itself).
- Index line written to `<out>/index/<read_id>.json`; `index` subcommand concatenates them into INDEX.jsonl.

## Per-item line (schema `corpus-v1`; document every field in SCHEMA.md, one page)
```
schema, read_id, official, partial, export{run,step,artifact_id,artifact_sha256,generation}, vehicle, set, family,
item_id, question_type, question, options, room, scene,
truth{scored, released, released_in_options, stratum, scorer, units?},
arms{<arm>: {answer, response_text, trace, tool_calls[{call,name,args,response,served,at_token,...all fields kept}],
             finish_reason, output_tokens, prompt_tokens, hit_cap, parse_failed, score, scores{...}}},
serving{...}, reader{format, build, source_files}, job_id, date, raw{<arm>: original row verbatim, input: joined task row}
```
Null when a value does not exist. `trace` is the full generated text (it already contains the tool responses inline in the routed format); `tool_calls` the structured list when the reader records one.

## Formats to support now (inspect the real examples; do not guess field names)
1. `kit` (direct reads). Example: /scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/kit/build/a8102c3207b/fetched/ (FETCH.json with job id, result.tar.gz, unpacked x/). In x/: SPEC.json (export binding, families), SUMMARY.json, COMPLETE.json, metadata/EXPORT_ARTIFACT.json, metadata/ORCHARD_LAUNCHER.json, and per family (main, a7, away, forward, r6...) `<fam>/COMPLETE.json`, `<fam>/a0/results/<arm>/[0/]items_a0.jsonl` where arm dirs are `0` (full generation, max_tokens 16384; rows also hold a nested `at_4096` block), `budget_2048`, `budget_4096`; `<fam>/report/B2048.json` etc. Map arms to names `full`, `B2048`, `B4096` (keep the original dir name in raw). Other examples with different layouts: .../h1read/kit/build/a5d2d909067/fetched/x (results/budget_2048/0/items_a0.jsonl), .../h1face/kit/build/a2e46c0504e/fetched/x (families away/forward), .../h1vsti/kit/build/acb2faedd41/fetched/x (family r6), .../h1read/readk/kit/build/a4cadd8934b/fetched/x. Accept either the x/ dir or the result.tar.gz (read members from the tar without extracting; prefer the tar when both exist and record its sha256).
2. `routed` (the model calls heads as tools inside its chain of thought). Example: /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/ret/ : SUMMARY.json, COMPLETE.json, metadata/{EXPORT_PIN,IDENTITY,INPUTS,CARDS,RETURN_ID}.json, metadata/reads/<r>/SUMMARY.json (complete, completed/expected per shard), metadata/reads/<r>/metadata/journals/<type>/<shard>/items.jsonl (row: id, type, arm, mode, intervention, output{text, tokens, finish, calls{records[...]}, scores{answer, released_answer}, question_type, stratum, decode_budget...}) and item_mapping.json. Rows lack the question text and truth: find them in the package inputs (A4/package/0.tgz, A4/src, or the paths metadata/INPUTS.json names; the journal's task_sha256 helps) and join; pass with `--inputs`. Other examples: .../r1route/out3/B5/ret, .../r1route/out3/bases/b1/work/ret (two reads 0 and 1: each read under one return becomes its own read_id suffix `.r<r>` unless `--read-index` selects one), .../r1route/out3/bases/b2/work/ret, and gz journals in /scratch/jjyeung/orch_n30/cont_ops18/ebuild/evidence/step544_return/ (items.jsonl.gz). Arm names come from the row (`arm`, `output.arm`, mode/intervention); keep all.
Design the code as a small adapter registry so later formats (offline official reads, native paired reads, K1) add one adapter each.

## corpus_score.py
Mean of `arms[A].score` (as stored) over items, overall and grouped; prints JSON. `--compare` reads a summary file and a dotted key path (e.g. `own_gt_by_stratum.missing_released.overall.score_pct`) and prints both numbers and MATCH/DIFF (tolerance 1e-6 after scaling percent vs fraction).

## Tests (tool/tests/, run with `python3 -m unittest`, under 2 GB RAM)
Ingest a8102c3207b (kit, from tar and from x/: identical output sha), a2e46c0504e, acb2faedd41, and A4/ret (routed) into tool/t/out; check idempotency (SAME on rerun, refuse on changed bytes), partial refusal on a synthetic truncated copy under tool/t/, and that corpus_score reproduces main/report/B2048.json's overall per-type numbers for a8102c3207b and A4's reported routed score (find it in A4/ret SUMMARY or the scoring outputs at .../r1route/out3s/scoresA*). Report each ingest's item count, bytes, sha256 and seconds.

## Deliver
tool/ingest_read.py, tool/corpus_score.py, tool/SCHEMA.md, tool/tests/, and a final message: what each format adapter reads, which fields stayed null and why, test results with numbers, and anything doubtful.
