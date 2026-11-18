# R6 upload plan

The operator uploads **one new file, 2,375,536 bytes**. No transfer has been performed.

| Local file | Orchard destination | Bytes | SHA256 |
|---|---|---:|---|
| `/scratch/jjyeung/orch_n30/cont_ops/work/h1vsti/assets/b62c14e9.jsonl` | `/project/community/jjyeung/okh7/af83c921/b62c14e9.jsonl` | 2,375,536 | `ef9b1c45f3cb3da84c108748b2e2ae7830ceeac5a0114b7cb52c44fab76fd58e` |

The destination directory must have mode **0700**, and the file must have mode **0600**. The reader refuses symlinks, wrong modes, sizes, or SHA256 values. The launcher embeds the small `R6.json` registry and the byte-identical capture implementation under the opaque name `c6.py`; neither requires a separate upload. All new Orchard family, asset, and module names are opaque.

The job reuses a7's existing archive at `/project/community/jjyeung/okh7/af83c921/d81f4a26.tar`: **797,685,760 bytes**, SHA256 `2ad8c67c111d5f286aa96ea688efd5c88218e116a8c09ae1a9b4bc71be893a21`. That file must retain mode 0600. Do not upload it again when the pinned staged copy exists. The job hashes the whole archive, validates every member, and stages its existing 3,136 frames with the same a7 staging code.

R6 uses **2,176 distinct frames, 564,411,344 bytes**, from 68 rooms. Every one of its 28,800 ordered frame references matches an a7 archive member by SHA256. **Missing frames: 0; additional frame bytes: 0; separate frame-list upload: none.** `evidence/FIXV1_ASSETS.json` records the proof, and `tools/build_r6.py` reproduces the question asset without reading or rebuilding the frame archive.

The question asset preserves all 900 questions, labeled options, gold letters, FPS values, frame counts, and ordered f32 indices. It uses the existing opaque physical-room/frame identities and new opaque item IDs. `evidence/R6_ID_MAP.json` stays local. `unpack_return.py` decodes r6 item IDs and rooms locally; the authenticated archive and raw evaluator journals retain their original bytes.

The source pins are:

| Read-only source under `/scratch/jjyeung/orch_n30/rows_r1/out/vsti_rel_dev_r0/` | SHA256 |
|---|---|
| `items.jsonl` | `b5853845aaf815c85e48e32f913efd14e8e7938c00723ff8c4a378375c4bfea3` |
| `R0DEV_VSTI_QUESTIONS.jsonl` | `08551bb2b9bd6ce47623c5efd9cba4f15872c0229bf8191235af5d63d957797d` |
| `capture.py`, packaged byte-identically as `kit/reader/c6.py` | `bbc735c3daf0fe8a7126883cb955097a1e52a2dcc738a19b902cb8e8c120c87b` |

The source item schema identifies rooms through `dataset` and `scene`; it does not contain a `room` key. The adapter writes a consistent physical-room ID to each item's `room` field. Local decoding restores `dataset/scene`. Bootstrap clusters use that field, with no room inference from questions or filenames.
