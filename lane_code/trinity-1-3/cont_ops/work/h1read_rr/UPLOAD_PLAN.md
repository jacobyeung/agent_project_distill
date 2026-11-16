# Operator upload plan

The operator uploads these two files through the IO governor. No transfer was performed. The target directory is `/project/community/jjyeung/okh7/af83c921/`; confirm that it is available before upload. The full job naming blocker in REPORT.md remains unresolved.

| Local file | Exact Orchard target | Bytes | SHA256 |
|---|---|---:|---|
| `assets/d81f4a26.tar` | `/project/community/jjyeung/okh7/af83c921/d81f4a26.tar` | 797685760 | `dfa66c645ea3b47dedebee13ae3206acb00fc5de7f0cc72d1101a67f75d10277` |
| `assets/e52a690b.jsonl` | `/project/community/jjyeung/okh7/af83c921/e52a690b.jsonl` | 5728183 | `b728f8a57179854f36bcce24e28637eece3e61729aee6455beba7bf8f3e904b7` |

Total upload: **803,413,943 bytes**. Extracted PNG payload: **795,282,085 bytes**; 3,136 regular files.

The job reads the two files from that exact read-only mount. `kit/reader/x7.py:stage_assets` verifies each size and complete SHA256 before extraction, checks the pinned member inventory, rejects links/foreign/duplicate members, and verifies every PNG digest. It verifies item/type/room counts and exact frame-reference closure. RGB mode/dimensions and pixel hashes are checked on use. The tar contains no unused rooms or f64-only frames.

Optional operator readback after the governed upload:

```bash
printf '%s  %s\n' 'dfa66c645ea3b47dedebee13ae3206acb00fc5de7f0cc72d1101a67f75d10277' '/project/community/jjyeung/okh7/af83c921/d81f4a26.tar' | sha256sum -c -
printf '%s  %s\n' 'b728f8a57179854f36bcce24e28637eece3e61729aee6455beba7bf8f3e904b7' '/project/community/jjyeung/okh7/af83c921/e52a690b.jsonl' | sha256sum -c -
```

Do not upload `in/`, `readk/`, `evidence/ID_MAP.json`, the reserve archive, reports or fixture directories. The per-job batch embeds its own small pinned runtime wrapper and registry; it is sent by the documented submission command.

Source archive: `/scratch/jjyeung/n30_mirror/b10_reserve/R0_RESERVE_20261116.tar`, **3,801,026,560 bytes**. Reading all source bytes produced SHA256 `2bbae12a984fde1228bdb571f5aee390c1e6a82dc554310aa04c6fd0fe80a116`, matching the supplied prefix. This full digest is now pinned in the builder and final inventory; no independent full source digest beyond the supplied prefix was provided.

The selected tar reproduces byte-for-byte when its members are streamed back through the deterministic writer. The test compares the complete output digest and byte count without creating another full tar.
