# Own-encoder grounding head: T-1 training kit

The head has **50,663,758 trainable parameters**: presence 2,276,866; OGD decoder 45,461,451; selector 2,925,441. The Qwen ViT and name embedding rows stay frozen.

- `vit.py` strictly loads local Qwen weights, verifies `SHA256SUMS`, hashes the loaded state, captures blocks 9/17/25/27, and pins normalized names' embedding rows. It never loads the LM. The requested 1,152-channel merged maps average 2×2 final-tap features; Qwen's native learned merger produces 4,096 channels.
- `head.py` contains `Config`, `GroundingHead`, frame shortlisting, cross-frame clustering, and the selector. Default OGD width is 640, with four blocks, 16 instance queries, one presence token, and 128-dimensional identity embeddings. `Config.tiny()` exercises the same pipeline with a small convolutional stem.
- `data.py` verifies the eligibility receipt and label/teacher/GT/frame hashes. Training manifests must contain only K1 `train` captures. A stable hash reserves approximately 10% of rooms for `train_val`; `inspect` permits admitted captures for tests only. Items contain one capture/name and all manifest frames.
- `losses.py` implements Hungarian matching, sampled focal/dice masks, match/presence/clip supervision, boxes, IoU regression, identity, selection, and teacher score distillation. MISS uses `labels.MISS_WEIGHT` (0.25). Selection skips ambiguous names and logs the reason.
- `train.py` implements AdamW, warmup/cosine, CUDA-only bf16 autocast, gradient clipping, validation, stop rules, and exact CPU resume. `predict_clip` uses the presence head to shortlist frames at inference. Validation also uses that shortlist.
- `export.py` writes safetensors and metadata and verifies them on load. Artifacts include config, labels, gate, ViT, tokenizer, and name-row hashes.

The model accepts four tap maps `[F,H/16,W/16,1152]`, all-clip merged maps `[T,h,w,1152]`, decoder RGB `[F,3,H,W]` in `[0,1]`, padded name embeddings `[N,P,4096]`, their boolean mask, and decoder frame indices. It returns stride-4 masks, normalized `cxcywh` boxes, IoU estimates, unit identity embeddings, presence/match logits, scores, clusters, and candidate-plus-none logits. Names in one forward belong to the same capture.

Presence examines every clip frame at 320×416 by default. Re-read defaults to 480×640; portraits transpose both resolutions. The two sizes are configurable multiples of 32. Frame counts, including 32 and 64, come from the manifest. Validation reuses the current capture's frozen all-frame features across names, then releases them at the end of the pass. It does not persist a feature cache to disk.

Losses run with autocast disabled and floating inputs converted to fp32. Joint-score distillation uses the sum of log-sigmoids and a clamped log-complement. Presence and joint-score distillation apply only to `uncertain_absent`, `not_annotatable`, and `absent` rows with a confuser/absent role. `disputed_absent`, `miss`, `sliver`, and `invalid_frame` rows receive no frame-presence supervision or distillation. DISPUTED proposals remain in targets but do not enter teacher selection candidates. Queries with mask IoU greater than 0.5 against DISPUTED or selection-only confuser proposals receive zero match weight. Confuser selection retains its quarter weight.

Each teacher candidate's IoU feature averages the decoder IoU estimates of the best-overlapping query in each member frame. Its coherence uses those queries' identity embeddings. The forward overwrites the target-only placeholders before the selector sees them; review test F4 checks the forward features.

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
"$PY" -m owngrd.split_manifest --in TEACHER_K1.json --split train \
  --out TRAIN_ONLY_MANIFEST.json
"$PY" -m owngrd.train --manifest TRAIN_ONLY_MANIFEST.json \
  --labels REAL_LABEL_ROOT --teacher-root REAL_TEACHER_ROOT \
  --out "$OUT/pilot" --device cuda --hours 4 --accelerator-hour-cap 4 \
  --steps 10000 --validate-every 200 --checkpoint-every 200
# Resume with identical arguments plus: --resume "$OUT/pilot/resume.pt"
```

`build_manifest --split train|heldout|all` defaults to `all`. `split_manifest` filters an existing manifest by K1 split, reruns `Gate.admit`, and records fresh counts, a receipt, and the source manifest SHA256. Training still rejects manifests containing heldout captures.

This trainer runs on one device; the accelerator-hour cap therefore counts one accelerator. It checks caps between training and validation items. Supply JSON overrides with `--config`; loss weights live in `Config.weights`. Resume rejects changed run settings, label sets, ViT, name rows, tokenizer, gate, or package source files. `RUN.json` records individual source hashes and their aggregate. Checkpoints store optimizer/scheduler state, Python/NumPy/Torch RNG states, a seeded per-epoch item permutation and cursor, stopper history, and elapsed time. CPU equality requires the same runtime and thread count. Resume preserves the interrupted log as `train.jsonl.before_resume.*` and rewrites `train.jsonl` through the checkpoint step before appending.

`train.jsonl` logs each loss separately, total loss, learning rate, gradient norm, step/epoch/item, capture/name, elapsed seconds, and selection skip counts. Validation adds candidate recall@5, matched-POS mask IoU, on-target share at 85% coverage, false presence on ABSENT pairs at that coverage, denominators, and stop decisions. Coverage ranks all pairs by the best candidate's sigmoid margin over none. False presence requires an accepted ABSENT pair whose candidate logit beats none, divided by all ABSENT pairs. On-target share uses only accepted, present pairs with exactly one GT instance; selecting none is not an on-target prediction.

Primary `candidate_recall_at5` measures names with exactly one GT instance in the label inventory. A top-five candidate must overlap that instance at mask IoU ≥0.5 in a decoded frame. `candidate_recall_at5_all_instances` reports the all-instance diagnostic. Both denominators include eligible instances without a GT-visible frame. Before step 1, `RUN.json` and a single `recall_ceilings` log event record the label-only visibility ceilings and the step-600 recall bar, `0.70 × unambiguous ceiling`. The diagnostic ceiling is the share of instances with at least one GT-visible frame; it does not solve joint frame/candidate packing for ambiguous names. The primary ceiling needs only one visible frame and one candidate per name, within the oracle budget of four frames and five candidates. The matched-POS IoU bar remains 0.44.

`--val-items N` selects a deterministic, seeded subset of `train_val`; its default, 0, uses all items. `RUN.json` records the selected indices. Ceilings and the recall bar use the same validation subset as the reported metrics. Validation preserves the training RNG state.

`tmp_codex/BUILD_REPORT.json` records test evidence, real-ViT smoke results, parameter counts, file hashes, and implementation choices. Stub tests validate mechanics; their losses and masks do not measure teacher quality or training performance.

The CPU regression gate reports **57 passed, 1 skipped**; the skip is the opt-in standalone real-ViT test. The real-label, real-ViT CPU smoke completes three training steps and all 16 validation items in about 607 seconds through validation. Training total losses are 3.3196, 1.1436, and 3.0779; validation total loss is 1.4660. Both recall metrics are 0, matched-POS IoU is 0.00858, and on-target share and false presence are 0. These three-step results verify execution, not grounding quality. The logged unambiguous/all-instance ceilings are 1.0000/0.9048, with a step-600 recall bar of 0.7000. The build report contains every loss component and the full metric denominators.
