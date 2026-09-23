The full-pool builder carries OUT0's training and heldout records byte-for-byte and adds strict-accepted teacher rows. It uses the bare-answer transform from `answer_only_full.py` at `9e782a8`, so new training targets match OUT0. `--target-format native-block` is available only for an explicitly requested tagged-answer variant.

Run the module from the repository root:

```bash
python -B -m student.compact_targets.answer_fullpool build \
  --output-mix /absolute/new/mix --output-layout /absolute/new/trainer \
  --out /absolute/audit
python -B -m student.compact_targets.answer_fullpool verify \
  --output-mix /absolute/new/mix --output-layout /absolute/new/trainer \
  --out /absolute/audit --native-loader
```

Use the lane's `out/BUILD_COMMAND.sh` for production. It sets the approved Python interpreter, disables CUDA and bytecode, applies idle I/O priority and nice level 19, and records build and verification logs. It requires a clean, committed lane branch. The builder refuses existing output directories and never deletes files.

`--limit 200` bounds each source root and each OUT0 split side. It produces a dry-run package, not a full OUT0 superset. Full builds omit this option and verification requires more training rows than OUT0. Dry runs still inherit every published scene assignment.

Root A uses its pinned v2 membership and ground truth. Root B uses its pinned v3 membership and ground truth. Both roots use the existing strict census grade: exact options and integer counts, and at most 5% numeric error. Root B freezes the terminal filenames at one timestamp and reads only those attempts through one serialized reader. It records every selected decision, trace pin, and terminal pin. The light census requires the archive journal and artifact-reference files to exist; it does not audit their full contents.

For staged Root A records, the builder authenticates the row hash, accepted trace pin, membership, native answer archive, and recorded frames. Rows without a usable staged record use the trace authentication and RGB extraction functions copied from `compact_v25_ingest.py` at `5411443`. Root B uses that same ingestion path with its run root passed explicitly. Both roots preserve the original 32-frame sampling. Every retained frame is hashed; missing or corrupt new-row frames cause a recorded exclusion. A missing OUT0 frame fails the build because carrying OUT0 is mandatory.

New room-size rows must match the fixed `room_labels.py` parser's exact same-scan full-room area, converted to the requested unit. The builder drops missing, conflicting, unequal, or unverifiably rounded labels. It does not synthesize a different teacher answer. Heldout room labels may validate heldout rows but cannot change split membership or enter training.

The pinned `b084aaf` trainer computes inherited splits. Existing physical groups keep their side; only unseen groups use its `student-scene-split-v1` hash with seed 17 and fraction 0.1. The builder also excludes benchmark qids and physical groups using OUT0's three benchmark authorities.

Each output manifest lists every output file except itself. `BUILD_SUMMARY.json` stores both manifest hashes externally. Audit files include unique dropped-qid records with all source occurrences, the frozen Root B census, a seed-20260923 sample, and per-root and per-type counts. Heldout routing is counted separately from dropped rows. Verification checks these hashes, inherited split stability, benchmark and holdout exclusion, OUT0 mix and trainer byte identity, and sampled frame hashes. `--native-loader` additionally runs the pinned trainer's CPU candidate loader, which hashes all retained frames.

Run only the new builder tests with `COMPACT_TEST_OUTPUT` and `TMPDIR` set to the lane temporary directory:

```bash
python -B -m unittest student.compact_targets.tests.test_answer_fullpool
```

Fixtures remain in that directory for inspection. The tests do not call paid APIs, train a model, or use a GPU.
