# Shared formats for the eight efficiency builds (2026-11-16)

Every build codes against these formats, so the branches merge without rework. Lane eff_orchkit_core owns this file's formats after the first merge; until then a builder who needs a change asks in a QUESTION event and continues on the format as written.

## Package layout (repository paths)

| Path | Owner brief | Runs where |
|---|---|---|
| `tools/orchkit/__init__.py`, `util.py`, `tests/test_util.py` | skeleton, copied byte for byte; orchkit-core owns later changes | Trinity and batch host (3.6-safe) |
| `tools/orchkit/pins.py`, `ledger.py`, `anon.py`, `launch.py`, `pack.py`, `stage.py`, `ret.py`, `templates/`, `schema/` | orchkit-core | `stage.py`, `ret.py`, `util.py` on the batch host; the rest on Trinity |
| `tools/orchkit/dryrun.py`, `lint_config.py`, `rowschema.py`, `shims/` | kit-dryrun | Trinity, CPU |
| `tools/orchkit/fixcheck.py`, `cite.py`; `docs/REVIEW_CHECKLIST.md`; `agent/templates/GO.md`, `REVIEW_BRIEF.md` | review-gate | Trinity, CPU |
| `tools/orchkit/reader/` | reader-harness | batch host inside the model environment |
| `tools/orchkit/watch.py`, `lease.py`; `agent/scripts/orch/` | orch-watch | Trinity |
| `tools/orchkit/govstream.py`, `mirror.py`; `docs/STREAM_PRIORITIES.md` | govstream | Trinity |
| `tools/treegit/`, `trainer/`, `tools/lane_code_sync.sh`, `tools/test_cpu.sh`, `.gitignore` | code-in-git | Trinity |
| `tools/docs/`, `agent/templates/briefs/`, `docs/README.md` | state-entrypoint | Trinity |

No build writes a file that another build owns. Tests live in `tools/orchkit/tests/test_<module>.py` (or the test folder a brief names), one file per module, so test files never collide either.

## Skeleton (copy byte for byte from `/scratch/jjyeung/orch_n30/eff_audit/briefs/skeleton/tools/orchkit/`)

| File | sha256 |
|---|---|
| `__init__.py` | `10e50fc5e273284050cdfc7747b7889411a9b46f5c28b6dc6c3b0580c36e8d62` |
| `util.py` | `0da3aaf18545b466b3075f623373453826b83e55426328d84e1e5ec1d3d01925` |
| `tests/test_util.py` | `e25aaf36593b885d7717addc6a71588177d5ebb6581def8c01e695f752c35be6` |

`util.py` provides `sha256_bytes(data)`, `sha256_file(path) -> (hex, bytes)`, `canonical_json(obj) -> bytes`, `canonical_sha256(obj)`, `atomic_write(path, data)`, `write_json(path, obj)`, `read_json(path)`, `utc_stamp()`, `utc_iso()`, `proc_identity(pid) -> {pid, comm, state, starttime} | None`, `append_jsonl_locked(path, row, max_bytes=1024)`. The ten tests pass on `/usr/bin/python3` 3.6.8 and on p1cpu 3.12 with `/home` and `/data*` hidden.

## Pin manifest, `orchkit-pins-v1`

One manifest per kit, generated only from files, and the only place in a kit that records a per-file hash.

```json
{"schema": "orchkit-pins-v1", "created_utc": "2026-11-16T12:00:00Z", "commit": "<repository sha or null>",
 "source_seal": "<trainer seal digest or null>",
 "entries": [{"role": "code|config|input|weights|env|record", "logical_path": "<path as the job sees it>",
              "bytes": 123, "sha256": "<64 hex>",
              "source": {"kind": "file|gcs|orchard", "uri": "<where the bytes come from>", "generation": "<GCS generation or null>"},
              "standin": "<optional: path of a small stand-in a dry run may use for an input or weights entry>"}]}
```

Entries are sorted by `logical_path`, and a repeated `logical_path` is refused. The kit identity is `kit_pins_sha256 = util.canonical_sha256(manifest)`. CONFIG, batch script, receipts, ledger rows, dry-run reports and verdicts carry `kit_pins_sha256` and never a per-file hash. A registered design record that a kit obeys (a stop rule, an init rule) is an entry with role `record`.

## Kit config header, `orchkit-config-v1`

```json
{"schema": "orchkit-config-v1", "kit_pins_sha256": "<64 hex>",
 "job": {"partition": "general|advanced", "gpus": 1, "cpus": 8, "mem_gb": 64, "time_limit_s": 10800, "signal_s": 600, "nice": 0},
 "entry": ["<argv of the batch entry>"], "n_items": 300,
 "budgets": {"<name>": {"max_bytes": 0, "per_item_bytes": 0}, "time": {"per_item_s": 0, "fixed_s": 0}},
 "records": [{"logical_path": "<pin entry with role record>", "sha256": "<64 hex>"}],
 "spec": {"<family-specific fields, each typed by the family's JSON schema>": null}}
```

Every constant that differs between two runs of one kit family lives in `spec`, never in code. The identity of a config is `config_sha256` = sha256 of the file bytes.

## Ledger row, `orchkit-ledger-v1` (one line under 1 KB, appended with `util.append_jsonl_locked`)

`{"schema", "utc", "event": "minted|submitted|ended", "token", "job_name", "job_id", "lane", "meaning", "kit_pins_sha256", "config_sha256", "partition", "gpus", "time_limit_s", "pool", "gcs", "state"}`. The job name is `a15_cot_ap` plus `secrets.token_hex(8)` and matches `^a15_cot_ap[0-9a-f]{16}$`. The production ledger is `B/ORCHARD_LEDGER.jsonl` on Trinity, never on the batch host; tests write to a temporary path given by `--ledger` or `ORCHKIT_LEDGER`.

## Dry-run report, `orchkit-dryrun-v1`

`{"schema", "utc", "kit_pins_sha256", "config_sha256", "entry", "stages": [{"name", "rc", "seconds"}], "items_total", "items_prepared", "standins": ["logical_path"], "shim_calls": 0, "coverage": {"files": 0, "lines_never_run": [{"file", "start", "end", "class": "unit_test|gpu_only|error_path|unclassified"}]}, "not_proven": ["text"], "verdict": "PASS|FAIL", "fail_reason": null}`. `launch.py prepare` refuses a kit without a PASS report whose two hashes equal the kit's.

## Review verdict, `orchkit-verdict-v1`

`{"schema", "utc", "reviewer_lane", "kit_pins_sha256", "verdict": "GO|GO_AFTER_FIXES|NO_GO", "scope_files": ["path"], "repro_suite": [["argv"]], "findings": [{"id", "severity": "blocker|fix|note", "class": "admission|legality|scoring|plumbing|docs", "file", "line_start", "line_end", "text", "repro": ["argv"], "expect": "pass|fail_before_pass_after"}]}`. For a kit built before the pin manifest exists, `kit_pins_sha256` holds the sha256 of the kit tar.

## Read config, `orchkit-read-v1` (the `spec` of a read)

`{"export": {"logical_path", "step"}, "items": {"logical_path"}, "frames": {"layout": "spread|duplicate", "count": 32, "layout_override_reason": null}, "scorers": ["direct|native|paired|official"], "compare_to": {"logical_path"}, "rule": {"record_logical_path", "name": "stop|init"}}`. A read plan is a list of read configs that one job runs in order.

## Environment variables for tests (production defaults in parentheses)

`ORCHKIT_LEDGER` (`B/ORCHARD_LEDGER.jsonl`), `ORCHKIT_OSSH` (`B/tools/ossh.sh`), `ORCHKIT_GOV_HELPERS` (`/scratch/jjyeung/io_governor`), `ORCHKIT_GOV_STREAMS` (`/data3/jjyeung/orch_n13_20261026/io_governor/streams`), `ORCHKIT_EVENTS` (`B/events`). A test that leaves any of them at its production default is a defect.
