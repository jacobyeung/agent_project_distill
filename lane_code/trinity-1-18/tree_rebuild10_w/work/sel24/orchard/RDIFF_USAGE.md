The discovery wrapper runs this command after mode `r` has successfully built both databases. Run on the same node before its temporary directory is removed. `D` is the wrapper's absolute output root containing `dr/`; `B` is the directory containing this delivered script. Choose a fresh opaque output directory.

```bash
nice -n 10 python3 -I -s -B "$B/rdiff.py" \
  "$D/dr/p/q/selection/rows.sqlite" \
  "$D/dr/p/q/base/rows.sqlite" \
  --tree "$D/dr/p/s" \
  --removal-manifest "$D/dr/p/q/n.json" \
  --base "$D/dr/p/q" \
  --out "$D/rd0"
```

`n.json` is the decoded, staged N config, not a capsule: the script reads its `remove_files` array and preserves list order, SHA256 pins, and `defects`. The mode-r planner writes it to `q/n.json` (`b/pl.py`, `copy_entry('n.json',...)`). Absolute localized paths are used unchanged; `--base` resolves any relative paths. If task A uses another outer directory, change only `D`. Do not point this command at the downloaded metadata directory: the production databases remain on the node.

P's reconstruction is `dr/p/q/base/rows.sqlite`: `b/rb.py` calls the producer with `root/'base'`; job 173567's `db_bytes.json` records this relative path. That failed job recorded hash `8516f395…`, not the required `4e8e6c04…`. This script refuses that file by default. The corrected reconstruction must match the full expected hash `4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84`.

N's mode-r database is `dr/p/q/selection/rows.sqlite`: `b/a.py` passes `root/'q'` to `begin_host`, `rg.regenerate(cfg,directory)` calls `s1_routing.build(cfg, root/'selection',...)`, and that builder writes `output/'rows.sqlite'`. The staged C tree is `dr/p/s`. These paths follow the supplied 24m4e kit; if 24m4h changes its mode-r layout, task A must use the resulting receipt's database path. No 24m4h production result is asserted here.

The script also accepts `--remove-files FILE ...` plus `--defects SHA256=identity,absent,merged`, or a JSON manifest containing the pin array. Prefer the staged config so no list or restriction is lost. The native tree reader handles JSONL records and the special `d1454a44…` JSON object with 109 `rows[].qid` entries. Arbitrary JSON arrays are deliberately not reinterpreted: unsupported formats fail exactly as the native reader does. Importing `student_pilot.row_removals.Removals` and `row_keys` from `--tree` preserves nested pointing/grounding/provenance keys, label aliases, overlap, list order, and defect restrictions.

The comparison covers every training row from `SELECT * FROM rows ORDER BY i`. Tree C's `s1_routing.py:248–253` creates `candidates`, `membership`, and the `rows(i,row,target)` view. `carrier_c1_routing.py:974` writes the corresponding three-column table. Unselected candidate rows and the `pool_qids` deduplication index are not training rows. The key is the JSON tuple `[dataset, scene, qid, s1_source.name]`; duplicate keys refuse. Legacy rows have a null source name.

Content SHA256 covers **all three columns**, including `i`, and the complete stored `row` and `target` TEXT. It uses an injective versioned encoding: `rdiff-v1` plus a zero byte, then a type byte, an unsigned 8-byte big-endian byte length, and each value's bytes. Integer values use ASCII decimal; TEXT uses UTF-8 without JSON parsing/re-serialization. SQLite page layout and unrelated database metadata are not row content. A changed index, JSON whitespace, frame path, target, or other stored field fails equality. The script does not relax this criterion to make removal-induced renumbering pass.

`rdiff.json.gz` is one JSON object with `N` and `P_absent` arrays and `U_Faithful` counts. Each N entry has its key/hash and matching P key/hash or null. Each absent P entry names the first matching removal-list SHA256, every overlapping list, or `none`. `listed` counts P U_Faithful rows matched by at least one active removal rule, not the number of keys or duplicate list matches.

`rdiff_summary.json` records the requested counts, script hash, input hashes, imported reader hash, and exact removal pins. Exit 0 means zero mismatches, zero absent-and-unlisted P rows, and zero listed N rows. Exit 1 means a completed failed comparison. Exit 2 means an invalid input, duplicate key, wrong P database hash, or other refusal; do not treat a partial gzip file as evidence. Existing output filenames refuse rather than overwrite. No training, network, GPU, temporary SQL file, or deletion is used.

Validation: `../tests/RESULTS.json` records 14 passing tests using SQL extracted from the actual tree writers. Tests cover identical rows, listed/unlisted omissions, aliases, content/index/target/whitespace changes, extra N rows, defect restrictions, the real 109-key JSON list, wrong P hash, duplicate keys, and retained listed rows. Tests override the P hash only for their synthetic databases; the wrapper command above does not.
