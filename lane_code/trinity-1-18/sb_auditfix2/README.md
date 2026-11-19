# Store room audit

`store_room_audit.py` compares every store row’s resolved physical room with five pinned lists: R0, withheld-80, BENCH v2, dev-S1, and K1. It loads `Rooms` from `--tree`, normalizes every list entry through `Rooms.room`, and preserves every row’s scene and room.

Use Python 3.8 or newer and the standard library. The Trinity system Python 3.6 is too old. No network, GPU, third-party packages, or sockets are needed.

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -s store_room_audit.py \
  --store /path/to/rows.sqlite \
  --tree /path/to/tree_r1 \
  --lists inputs/lists \
  --out out/new-store
```

`--out` must be empty or absent. The store must be an offline snapshot. Supported stores are SQLite with table `rows(i, row)` containing JSON rows, JSONL, and JSON arrays or objects with a `rows` array. SQLite and JSONL stream rows; JSON arrays load into memory. Each row uses `dataset`, `scene`, optional `canonical` fields at the row root or under `provenance`, `ground_record`, and `gt_authority`, `qid`, `pool` (stream), and `question_type` (family).

## Inputs

`--tree` must contain `student_pilot/r1_rooms.py`, `p3_provenance.py`, `r1_persisted.py`, and `carrier_c1_routing.py`. The CLI executes the selected tree’s full `Rooms` class and its constructor’s authority checks. It loads only the three room modules, without package startup code or an installed package fallback. It extracts `alias_of`, `ALIAS`, and `NATIVE` from that tree’s carrier source. Treat the selected Python tree as trusted executable code.

`--lists` contains `manifest.json` with schema `store-room-audit-inputs-v1`. The included manifest demonstrates the format. Paths resolve relative to its directory; absolute paths also work.

- `authority` supplies the exact `path` and `sha256` pins required by the selected `Rooms` constructor: split, visits, aliases, reserve, and build.
- `lists` supplies exactly the five named lists. Each entry has `path`, `sha256`, and `field`. Supported fields are `text`, `rooms`, `physical_groups`, and `heldout_captures`. K1 selects captures whose `k1_split` is `heldout`.
- Optional `alias_map` supplies `path` and `sha256` for a reviewed tiered map with `aliases[token] = {canonical, tier}` and optional `quarantined_tokens`. Tiers are A, B, and C. The included map retains the source evidence from the reviewed audit.
- `inputs` records the hashes used to stage the included manifest. Copied `.raw` authorities retain their exact source bytes.

For another store, supply its row file and the intended tree and list manifest. Reuse an alias map only when its token convention and evidence apply. New native scenes and explicit canonical witnesses can resolve directly; unknown hashed tokens require a supplied mapping or a matching explicit witness. The CLI does not invent scenes or search other directories for candidates.

The CLI verifies the bytes of every direct input and records their SHA256 in `audit.json` and the SQLite metadata. It checks mapped hashed tokens with the selected `alias_of` function. Imported A/B/C proof tiers remain claims of the pinned map; the CLI does not reopen all original witness files or archives. Direct row witnesses use tier A, native dataset/scene resolution uses `native`, and constructor aliases without a supplied proof tier use `authority`.

ARKit physical `venue…` labels pass through a capture found in the pinned visit table before `Rooms.room` runs. A missing capture fails explicitly. `capture…` labels must round-trip through the same method. ScanNet rescans share a room. Both ScanNet++ spellings share a room. Pinned list labels retain their literal identifiers, including nonstandard labels; native ScanNet row identifiers must match `scene[0-9]{4}_[0-9]{2}`, and every ARKit capture id must appear exactly in the pinned visits table. The CLI refuses padded, truncated, or absent ids without guessing a correction. These checks also apply to explicit canonical witnesses and alias targets. A row that fails these checks stays unresolved.

## Outputs and exit codes

`audit.json` reports hits per list, tier, stream, family, and their joint combinations. It includes input hashes, the command, list sizes, coverage, unresolved tokens, and the hash of `rows.sqlite`.

`rows.sqlite` contains one record for every source row, keyed by `row_index`. Columns include the source `scene_token`, resolved `scene`, physical `room`, proof `tier`, stream, family, matched lists, and an unresolved reason. Unresolved rows retain NULL scene and room values. Its `metadata` table contains the audit and input hashes.

| Exit | Meaning |
|---|---|
| 0 | Complete audit, or explicitly allowed incomplete audit. |
| 2 | Unresolved tokens refused, or invalid CLI/output-directory use. |
| 1 | Missing, changed, malformed, or incompatible input. |

The CLI prints both distinct unresolved-token and unresolved-row counts. With `--allow-unresolved`, it writes `status: INCOMPLETE`, `complete: false`, and marks hit counts as lower bounds. The flag cannot bypass hash mismatches, missing inputs, or list failures. The CLI collects all four canonical witness fields, normalizes dataset synonyms, and refuses any disagreement, including two captures from the same physical room. Conflicting row witnesses and quarantined tokens remain unresolved. A nonempty output directory is refused to prevent stale results from appearing current.

Callers must read `audit.json` and check its `status` and `complete` fields; an exit code alone does not certify a complete audit. `PASS` means all rows resolved, `REFUSED` means unresolved rows were rejected, `INCOMPLETE` means unresolved rows were explicitly allowed, and `MISSING` or `ERROR` means an input failed. CLI misuse can exit 2 without creating a new report. Use a fresh output directory and accept only a report from the current invocation.

The audit checks scene identity. It does not verify that frame contents belong to the claimed scene. A complete audit may contain list hits; a zero exit code means resolution completed, not that the store is free of listed rooms.

## Reproduce the checks

Run from this workspace. The synthetic runner creates a fresh directory under `out/` and reports its location.

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -s tests/test_store_room_audit.py
/scratch/jjyeung/envs/p1cpu/bin/python -s store_room_audit.py \
  --store /scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite \
  --tree inputs/tree_r1 \
  --lists inputs/lists --out out/v7-replay
/scratch/jjyeung/envs/p1cpu/bin/python -s tests/check_v7.py \
  --audit out/v7-replay/audit.json --out out/V7_REPLAY_CHECK.json
```

The 16 synthetic tests include the eight existing tests, all five reviewer examples from findings 3 and 4, every pair of canonical witness locations, agreeing dataset synonyms, and invalid ids hidden behind witnesses. They plant both ScanNet++ spellings in a real BENCH v2 room and rows in every other list. They also check rescans, ARKit visits, unknown-token refusal, explicit incomplete output, witness conflicts, selected-tree execution, altered hashes, missing paths, persisted rows, count consistency, and stale-output refusal.

The v7 checker requires 204,413 resolved rows, no unresolved rows, hits 0/0/0/0/4,959 in the list order above, and K1 tiers A=110, B=4,770, C=79. It recomputes every persisted room and every count from the row records using the selected tree. `tests/compare_alias2.py` independently checks every source row against the pinned sb_alias2 map, derives rooms from the pinned visits table, recounts list membership, and compares all exported counts with sb_alias2.

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -s -B tests/compare_alias2.py \
  --audit out/v7-replay/audit.json --out out/ALIAS2_REPLAY_CHECK.json
```

The archive includes a minimal copy of the exact w18 source under `inputs/tree_r1`, the pinned lists and alias map, scripts, successful tests, and persisted v7 results. It excludes the 1.7 GB input store; the command above names its required location. On another machine, use the included `inputs/tree_r1` as `--tree` and provide the store separately. `stage_inputs.py` records how the bundled inputs were copied from local sources. Files under `reference/` preserve the source audit and helpers for review and are not CLI dependencies.

## Delivered results

`out/AUDITFIX2_REPORT.md` identifies the current regression and store results. `out/sb_auditfix2.tar` and its SHA256 sidecar contain the current deliverable; `out/PACKAGE_MANIFEST.json` hashes every packaged input.

The copied earlier failing run, `out/regression-t0kpto4o`, records 8 tests, 0 failures, and 1 error with test-file SHA256 `be075c88ffaddeb9e6cc95d5661bb7142a8b492d83c12ffb94713e78ea71deeb`. It is retained as historical evidence and is not a passing result for this tool. Its `TEST_RESULTS.json` is included in the archive. Other copied sb_auditfix outputs retain their original provenance and are not current validation. No files were deleted.
