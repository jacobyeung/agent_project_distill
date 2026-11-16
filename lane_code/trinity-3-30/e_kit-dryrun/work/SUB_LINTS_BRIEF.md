# Sub-build: lint_config.py and rowschema.py (for lane e_kit-dryrun)

You build two standard-library Python modules and their tests inside an existing local clone. Another agent (the lane) builds `dryrun.py` in the same folder at the same time; touch only the files listed under "Files you write".

## Rules (win over everything else)
- Host trinity-3-30. Run `hostname -s` first; if it prints `trinity`, stop and say so.
- No Git command of any kind. No ssh, no network, no package install, no GPU.
- Never delete or overwrite a file outside the list below; never use `rm`, `unlink`, `os.remove`, `shutil.rmtree` in code or shell. Create files with the Write tool.
- Never read, list or search `/home` or `/data*`. Everything you need is named below, on `/scratch`.
- Python 3.6-safe: standard library only; no dataclasses, no walrus, no f-string `=` specifier, no `subprocess.run(capture_output=, text=)`, no `Path.is_relative_to`, no `from __future__ import annotations`. f-strings are fine (3.6). Use `typing` only in comments.
- Import shared helpers from `tools/orchkit/util.py` (`sha256_file`, `canonical_json`, `read_json`, `write_json`, ...). Do not edit `util.py` or `__init__.py`, and do not write your own sha or JSON-canonical helper.
- Opacity: no project, benchmark, dataset or model word in code beyond what the rules below require (the D0 row field names are fine).

## Paths
CLONE = `/scratch/jjyeung/orch_n30/e_kit-dryrun/clone`; package `CLONE/tools/orchkit/`; tests `CLONE/tools/orchkit/tests/`; fixtures `CLONE/tools/orchkit/tests/fixtures/dryrun/`. Scratch temp: `/scratch/jjyeung/orch_n30/e_kit-dryrun/tmp` (use as TMPDIR).

## Files you write
`tools/orchkit/lint_config.py`, `tools/orchkit/rowschema.py`, `tools/orchkit/tests/test_lint_config.py`, `tools/orchkit/tests/test_rowschema.py`, and new files under `tools/orchkit/tests/fixtures/dryrun/lint/` and `tools/orchkit/tests/fixtures/dryrun/rows/`.

## Shared config format (orchkit-config-v1)
```json
{"schema": "orchkit-config-v1", "kit_pins_sha256": "<64 hex>",
 "job": {"partition": "general|advanced", "gpus": 1, "cpus": 8, "mem_gb": 64, "time_limit_s": 10800, "signal_s": 600, "nice": 0},
 "entry": ["<argv of the batch entry>"], "n_items": 300,
 "budgets": {"<name>": {"max_bytes": 0, "per_item_bytes": 0}, "time": {"per_item_s": 0, "fixed_s": 0}},
 "records": [{"logical_path": "<pin entry with role record>", "sha256": "<64 hex>"}],
 "spec": {"<family-specific fields>": null}}
```
Older kits' configs do not follow this header; the lint must still run on them (schema checks only when `--schema` is given; header-dependent budget checks only when the fields exist).

## lint_config.py
CLI: `python lint_config.py CONFIG.json [--schema FAMILY.schema.json] [--pins PINS.json] [--json OUT.json]`. Prints one line per finding (`<rule> <json.path>: <message>`), exits 1 on any finding, 0 when clean, 2 on unreadable input. Also expose `lint(config, schema=None, pins=None) -> list of dict(rule, path, message)` for import by dryrun.py. Rules:
1. `schema`: JSON-schema subset with the standard library: type (string, integer, number, boolean, object, array, null, and a list of types), required, enum, pattern (re.search with anchors as written), properties, additionalProperties (bool or schema), items, minimum. Booleans are not integers.
2. `prose`: any string value under a key matching (case-insensitive regex search) `sha|digest|members|inventory|path|uri|object|generation|pin`, including every string inside lists or dicts under such a key, and dict KEYS under `members`/`inventory` keys, must be one of: a 64-hex digest; a clean path (absolute or relative, no whitespace, no `..` component, no `//`, no `<` `>`); a `gs://bucket/object` URI with no whitespace; a decimal integer string. Separately, any such string holding a space, `<`, `>`, `...`, `TODO` or the word `plus` fails. A `members`/`inventory` value that is a string at all (rather than an object or list) fails: the K1 failure was `anchors.members: "xx/<sha>.png plus ANCHORS_MANIFEST.json"`. Port the field rules of the K1 auditor too: `generation` is a positive integer or digit string; `md5` and `crc32c` are base64 of 16 and 4 bytes; `sha256`/`*_sha256`/`digest` are 64 hex; a `members` dict maps a relative clean path to either a 64-hex string or `{"bytes": int>=0, "sha256": 64hex}`. Source of those rules: `/scratch/jjyeung/orch_n30/e_kit-dryrun/ref/k1_partb/build/audit_config.py` (read it).
3. `budget`: for every `budgets.<name>` other than `time`: fail if `per_item_bytes` is missing or not a positive integer ("a budget with no per_item figure fails, because a constant default caused the tower_sam stop"), or if `max_bytes < n_items * per_item_bytes`. For `budgets.time`: fail if `per_item_s` missing, or `job.time_limit_s < n_items * per_item_s + fixed_s`. If the config has `budgets` but no `n_items`, fail.
4. `host_path`: any string anywhere containing `/scratch/jjyeung/`, `/home/`, a path starting `/data` (`/data/`, `/data2/`, `/data3/`, `/data4/`), or a Trinity host name (`trinity`, `trinity-1-3` etc., regex `\btrinity(-[0-9]+-[0-9]+)?\b`, and `.vision.cs.cmu.edu`) fails, because the config is bound for the batch host. Also refuse the opacity words listed in an optional `--opacity-words FILE` (one per line, case-insensitive substring) for every string.
5. `pins` (only with `--pins`, an `orchkit-pins-v1` manifest `{"schema","entries":[{"role","logical_path","bytes","sha256","source":{"kind","uri","generation"},"standin"?}]}`): `kit_pins_sha256` in the config must equal `util.canonical_sha256(manifest)`; every `records[].logical_path` must be a pin with role `record` and equal sha256; entries sorted by logical_path, unique.

## rowschema.py
CLI: `python rowschema.py check --rows FILE.jsonl[.gz] --profile PROFILE.json [--config CONFIG.json] [--max-print 20] [--json OUT.json]`. Streams rows once (gzip by `.gz` suffix or magic), never loads the whole file. Prints a summary per family (family = value of the profile's `family_field`, dotted path, default `"family"`; missing -> `"<none>"`): rows, violations per rule, first examples (row number, id from profile `id_field`). Exit 1 on any violation, 0 clean, 2 unreadable. Expose `check(rows_iter, profile, config) -> dict` for import by dryrun.py. Profile format (`orchkit-rowprofile-v1`, document it in the module docstring):
- `required`: list of dotted paths that must be present and non-null in every row.
- `when`: list of `{"config": {"<dotted key in CONFIG>": <value>}, "positive_int": [dotted paths], "required": [...], "enum": {"<path>": [values]}}`; a clause applies only when every config key equals its value (a missing key never matches). Booleans are not integers.
- `vocab`: `{"<dotted path>": [allowed values]}` (the answer-unit vocabulary); a missing field is not a vocab violation unless also required.
- `forbid_substrings`: strings no serialized row may contain (lane paths such as `/scratch/jjyeung/`, host names such as `trinity-`, opacity words), case-insensitive; report the first dotted path holding it.
- `forbid_values`: `{"<dotted path>": [values]}` (for example withheld scene ids); also `forbid_values_files`: `{"<dotted path>": "<file with one value per line>"}` relative to the profile.
- `groups`: list of `{"key": "<dotted path>", "size": N}`: rows sharing a key must number exactly N (pairs kept whole); needs one pass with a dict of counts, which is fine.
- `unique`: list of dotted paths whose values must be unique across rows.
Dotted paths go through dicts only; a list index may appear as a numeric component (`frames.0`).
Write `tests/fixtures/dryrun/rows/d0_rows.profile.json` that encodes the D0 rules: `required` `qid`, `student_input`; `when` `{"config": {"frame_layout": "duplicate"}, "positive_int": ["student_input.fps", "student_input.total_num_frames"]}`; `forbid_substrings` `/scratch/jjyeung/`, `/home/`, `/data2/`, `/data3/`, `trinity-`, `orch_n30`; `unique` `qid`. The records it encodes (read each once, they are small): `/data2/jjyeung/agent_project_data/distill_design/D0_V5_NULL_FRAME_COUNT_20261116.md` and `/data2/jjyeung/agent_project_data/distill_design/D0_ROWS_ADMISSION_20261115.md` — that is the only /data* read allowed, one bounded `head -c 12000` each. At the end of your reply, list every rule those two records state that you could not make mechanical, with the reason.

## Tests (unittest.TestCase, files above)
lint_config: (a) the K1 regression: a config with `"anchors": {"members": "xx/<sha>.png plus ANCHORS_MANIFEST.json"}` fails rule `prose`; (b) `budgets.out.max_bytes` 1500000000 with `n_items` 300 and `per_item_bytes` 10000000 fails `budget`; a budget with no `per_item_bytes` fails; a time budget below need fails; (c) a clean orchkit-config-v1 config passes with a small family schema fixture (`fixtures/dryrun/lint/toy.schema.json`) and fails on a type error, an enum error, a missing required key, an extra key under additionalProperties false; (d) `/scratch/jjyeung/x` in any string fails `host_path`; (e) pins: kit_pins_sha256 mismatch fails; (f) the CLI exit codes via subprocess with `sys.executable`.
rowschema: (a) `total_num_frames: null` under config `frame_layout: duplicate` fails, and passes under `spread`; (b) a row whose `metadata.source` holds `/scratch/jjyeung/orch_n30/x` fails; (c) vocab, groups (a half pair fails), unique, forbid_values_files each fail once and pass once; (d) a `.jsonl.gz` input works; (e) CLI exit codes via subprocess.
Write temporary files only under `tempfile.mkdtemp()` (TMPDIR is set to the lane tmp).

## Must pass, both (run them yourself and paste the tail of each output in your reply)
```
cd /scratch/jjyeung/orch_n30/e_kit-dryrun/clone/tools/orchkit && TMPDIR=/scratch/jjyeung/orch_n30/e_kit-dryrun/tmp /usr/bin/python3 -m unittest discover -s tests -p 'test_lint_config.py' -t . -v ; TMPDIR=... /usr/bin/python3 -m unittest discover -s tests -p 'test_rowschema.py' -v
W=/scratch/jjyeung/orch_n30/e_kit-dryrun; cd $W/clone/tools/orchkit && bwrap --ro-bind / / --bind $W $W --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /tmp --dev /dev --proc /proc env HOME=/tmp TMPDIR=$W/tmp /scratch/jjyeung/envs/p1cpu/bin/python -s -m pytest -q -p no:cacheprovider tests/test_lint_config.py tests/test_rowschema.py
```
Tests must import the modules the way unittest discovery from `tools/orchkit` sees them: put `sys.path.insert(0, <tools/orchkit dir computed from __file__>)` at the top of each test and `import lint_config`, `import rowschema`; the modules themselves import util with a fallback: `try: from . import util` / `except ImportError: import util` after inserting their own directory into sys.path. Check how `tests/test_util.py` imports util and match it.

Reply with: files written, both test outputs' tails, and the list of non-mechanical rules. Keep the reply under 40 lines.
