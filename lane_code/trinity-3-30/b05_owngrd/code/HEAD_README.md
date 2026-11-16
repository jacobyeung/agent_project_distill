# Own-encoder grounding head: T-1 training kit

The head has **50,521,678 trainable parameters**: presence 2,134,786; OGD decoder 45,461,451; selector 2,925,441. The Qwen ViT and name embedding rows stay frozen. Existing teacher and label modules retain their behavior.

- `vit.py` strictly loads local Qwen weights, verifies `SHA256SUMS`, hashes the loaded state, captures blocks 9/17/25/27, and pins normalized names' embedding rows. It never loads the LM. The requested 1,152-channel merged maps average 2×2 final-tap features; Qwen's native learned merger produces 4,096 channels.
- `head.py` contains `Config`, `GroundingHead`, frame shortlisting, cross-frame clustering, and the selector. Default OGD width is 640, with four blocks, 16 instance queries, one presence token, and 128-dimensional identity embeddings. `Config.tiny()` exercises the same pipeline with a small convolutional stem.
- `data.py` verifies the eligibility receipt and label/teacher/GT/frame hashes. Training manifests must contain only K1 `train` captures. A stable hash reserves approximately 10% of rooms for `train_val`; `inspect` permits admitted captures for tests only. Items contain one capture/name and all manifest frames.
- `losses.py` implements Hungarian matching, sampled focal/dice masks, match/presence/clip supervision, boxes, IoU regression, identity, selection, and teacher score distillation. MISS uses `labels.MISS_WEIGHT` (0.25). Selection skips ambiguous names and logs the reason.
- `train.py` implements AdamW, warmup/cosine, CUDA-only bf16 autocast, gradient clipping, validation, stop rules, and exact CPU resume. `predict_clip` uses the presence head to shortlist frames at inference. Validation also uses that shortlist.
- `export.py` writes safetensors and metadata and verifies them on load. Artifacts include config, labels, gate, ViT, tokenizer, and name-row hashes.

The model accepts four tap maps `[F,H/16,W/16,1152]`, all-clip merged maps `[T,h,w,1152]`, decoder RGB `[F,3,H,W]` in `[0,1]`, padded name embeddings `[N,P,4096]`, their boolean mask, and decoder frame indices. It returns stride-4 masks, normalized `cxcywh` boxes, IoU estimates, unit identity embeddings, presence/match logits, scores, clusters, and candidate-plus-none logits. Names in one forward belong to the same capture.

Presence examines every clip frame at 160×224 by default. Re-read defaults to 480×640; portraits transpose both resolutions. The two sizes are configurable multiples of 32. Frame counts, including 32 and 64, come from the manifest. No feature cache is enabled.

Run the tests from this directory. Use a new `--basetemp` path each time so pytest does not remove an existing directory. The real ViT test requires the Trinity heavy-I/O approval and writes no real-size checkpoint.

```bash
PY=/scratch/jjyeung/envs/allospatial_1111_v1/bin/python
OUT=/scratch/jjyeung/orch_n30/b05_owngrd/tmp_codex
OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1 \
  "$PY" -m pytest -q -p no:cacheprovider --basetemp="$OUT/tests_NEW" tests
OWNGRD_REAL_VIT=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1 \
  "$PY" -m pytest -q -s -p no:cacheprovider --basetemp="$OUT/real_NEW" \
  tests/test_head_kit.py::test_real_vit_first_batch
```

Pilot command template, for an authorized compute run with real teacher labels:

```bash
"$PY" -m owngrd.train --manifest TRAIN_ONLY_MANIFEST.json \
  --labels REAL_LABEL_ROOT --teacher-root REAL_TEACHER_ROOT \
  --out "$OUT/pilot" --device cuda --hours 7.5 --accelerator-hour-cap 60 \
  --steps 10000 --validate-every 200 --checkpoint-every 200
# Resume with identical arguments plus: --resume "$OUT/pilot/resume.pt"
```

This trainer runs on one device; the accelerator-hour cap therefore counts one accelerator. It checks caps between training and validation items. Supply JSON overrides with `--config`; loss weights live in `Config.weights`. Resume rejects changed run settings, label sets, ViT, name rows, tokenizer, or gate. Checkpoints also store optimizer/scheduler state, Python/NumPy/Torch RNG states, epoch/item cursor, stopper history, and elapsed time. CPU equality requires the same runtime and thread count.

`train.jsonl` logs each loss separately, total loss, learning rate, gradient norm, step/epoch/item, elapsed seconds, and selection skip counts. Validation adds candidate recall@5, matched-POS mask IoU, on-target share at 85% coverage, false presence on ABSENT pairs at that coverage, denominators, and stop decisions. Coverage ranks pairs by the best candidate's sigmoid margin over none. False presence divides accepted ABSENT predictions by all ABSENT pairs; on-target share excludes ambiguous names. Recall counts every GT instance, including instances absent from the four shortlisted frames.

`tmp_codex/BUILD_REPORT.json` records test evidence, real-ViT timing/RSS when approved, parameter counts, file hashes, and the implementation choices not fixed by the brief. Stub tests validate mechanics; their losses and masks do not measure teacher quality or training performance.
