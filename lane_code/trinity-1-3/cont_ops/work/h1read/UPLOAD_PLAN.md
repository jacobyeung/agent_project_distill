# Operator upload plan

The operator uploads only the two files below through the IO governor. No transfer was performed.
Set `/project/community/jjyeung/okh7/af83c921/` to mode **0700** and both files to **0600**. The job refuses other modes, symlinks or nonregular files before hashing or extraction.

| Local file | Exact Orchard target | Bytes | SHA256 |
|---|---|---:|---|
| `assets/d81f4a26.tar` | `/project/community/jjyeung/okh7/af83c921/d81f4a26.tar` | 797685760 | `2ad8c67c111d5f286aa96ea688efd5c88218e116a8c09ae1a9b4bc71be893a21` |
| `assets/e52a690b.jsonl` | `/project/community/jjyeung/okh7/af83c921/e52a690b.jsonl` | 5728183 | `1d8b29a7f7bb5c4e486f430b1128b9fa249de24ae7a3905b9bb0ccdd778c892b` |

Total upload: **803,413,943 bytes**. Extracted PNGs: **795,282,085 bytes**, 3,136 files.

After upload, the operator sets and checks permissions and verifies the full digests:

```bash
chmod 0700 /project/community/jjyeung/okh7/af83c921
chmod 0600 /project/community/jjyeung/okh7/af83c921/d81f4a26.tar /project/community/jjyeung/okh7/af83c921/e52a690b.jsonl
stat -c '%a %n' /project/community/jjyeung/okh7/af83c921 /project/community/jjyeung/okh7/af83c921/d81f4a26.tar /project/community/jjyeung/okh7/af83c921/e52a690b.jsonl
printf '%s  %s\n' '2ad8c67c111d5f286aa96ea688efd5c88218e116a8c09ae1a9b4bc71be893a21' '/project/community/jjyeung/okh7/af83c921/d81f4a26.tar' | sha256sum -c -
printf '%s  %s\n' '1d8b29a7f7bb5c4e486f430b1128b9fa249de24ae7a3905b9bb0ccdd778c892b' '/project/community/jjyeung/okh7/af83c921/e52a690b.jsonl' | sha256sum -c -
```

`kit/reader/x7.py:stage_assets` checks modes, file sizes and complete SHA256, exact item/type/room membership, frame-reference closure, safe tar members and every PNG digest. Loading checks RGB, dimensions and pixel digests. The trained cell supplies 32 anchors twice (64 input frames).

Keep `evidence/ID_KEY.json`, `evidence/ID_MAP.json`, `evidence/FAMILY_ALIASES.json`, source snapshots, reports and tests on Trinity. None enters the batch, configuration or returns. The key is generated once and reused for deterministic rebuilds.

The retained local frame asset supplies all frame bytes; its full digest is checked before every rebuild. `evidence/ASSET_BUILD.json` preserves the original reserve provenance. Tests reconstruct the deterministic sorted USTAR stream and compare its full digest.
