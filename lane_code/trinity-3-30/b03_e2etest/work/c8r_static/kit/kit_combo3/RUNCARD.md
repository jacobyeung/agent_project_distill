Run one variant at a time on one allocated compute-node GPU. The kit needs local staged PNGs, baseline candidates and journals, SAM3 source/checkpoint, tower exports, and aligned GT. It downloads nothing. This lane ran CPU work only.

| Variant | Change | Estimated GPU minutes | Candidate disk estimate |
|---|---|---:|---:|
| baseline | Reuse the existing cache | 0 | 0 additional; 23.7 MB referenced |
| dense | Joint floor 0.05, cap 30; linker floor 0.3 | 26.9 | 95 MB |
| dense_link05 | Same dense candidates; linker floor 0.05 | 0 additional | 95 MB materialized |
| aliases | Add frozen synonyms/coarser phrases; retain baseline P0 | 16.5 | 71 MB |
| tiles | Four overlapping 60%-size crops on up to four baseline-empty frames per phrase | 22.9 | 119 MB |
| student_tiles | Same tile search, triggered by student P(yes)>0.5 on empty frames | ≤77.5 including presence | 119 MB plus presence rows |

SAM estimates scale the measured 22.4-minute, 152-capture baseline using 75% prompt-frame work and 25% image-encoding work. Dense adds 20% for retaining more masks. These weights are assumptions, not measured profiling. Student presence adds 54.6 minutes at the earlier measured 8 calls/s; its tile cost is an upper workload because the gate can remove requests. Model loading is additional. Allow roughly 0.7–1.5 times the SAM estimates and inspect the first capture before extrapolating. Each candidate run has a two-hour admission cap, a 500 MB candidate cap, and requires a 100 GiB free-space reserve. CPU pricing and recall auditing take additional time and use one process per stage.

The sealed kit lives in `out/kit`. `out/mask_recall_kit.tar.gz` contains that directory. Verify the archive’s adjacent checksum, then run `seal.py` on the extracted kit. Source inputs, models and environments are not bundled. Keep the experiment output root separate from the sealed kit and from this CPU lane.

```bash
KIT=/scratch/jjyeung/mask_recall_run/kit
RUN_ROOT=/scratch/jjyeung/mask_recall_run/results
FRAMES=/scratch/jjyeung/devs1_mask_frames
BASE=/scratch/jjyeung/devs1_baseline/candidates
BASE_PROGRAM=/scratch/jjyeung/devs1_baseline/predicted_price/PER_ITEM.jsonl
EXPORTS=/scratch/jjyeung/devs1_exports
GT_CAPTURES=/scratch/jjyeung/devs1_gt/CAPTURES.jsonl
SAM3_SOURCE=/scratch/jjyeung/mdg_next_sam3/sam3src
SAM3_CHECKPOINT=/scratch/jjyeung/mdg_next_sam3/sam3.pt
GPU_PY=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python
CPU_PY=/scratch/jjyeung/envs/p1cpu/bin/python
STUDENT_PY=/scratch/jjyeung/envs/student_hf/bin/python
STUDENT_CHECKPOINT=/scratch/jjyeung/student_checkpoint
export CUDA_VISIBLE_DEVICES=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
COMMON=(--out "$RUN_ROOT" --baseline-cache "$BASE" --baseline-program "$BASE_PROGRAM" --exports "$EXPORTS" --gt-captures "$GT_CAPTURES" --frames "$FRAMES" --checkpoint "$SAM3_CHECKPOINT" --source "$SAM3_SOURCE" --gpu-python "$GPU_PY" --cpu-python "$CPU_PY")
"$CPU_PY" -I -s "$KIT/work/seal.py" "$KIT"
```

Set these paths to existing local inputs. `GT_CAPTURES` must point to a manifest whose `pricing_gt` paths resolve to local GT files; frame IDs must match the original manifest. Preserve the G3T and V-C export directory names in HEADS.json. PNG filenames and hashes appear in FRAMES_TAR.txt. The SAM receipt pins the same source revision and checkpoint as the baseline. The student checkpoint and its compatible existing environment are separate inputs; the kit neither assumes the current answering checkpoint reproduces the earlier presence result nor substitutes missing presence scores.

One command per variant follows. Use a persistent operator session. Run dense before dense_link05. The baseline command reruns CPU pricing against the reused cache; the already repaired baseline in this delivery can be inspected without running it.

```bash
"$CPU_PY" -I -s "$KIT/work/experiment.py" --variant baseline --stage all "${COMMON[@]}"
"$GPU_PY" -I -s "$KIT/work/experiment.py" --variant dense --stage all "${COMMON[@]}"
"$CPU_PY" -I -s "$KIT/work/experiment.py" --variant dense_link05 --stage all "${COMMON[@]}"
"$GPU_PY" -I -s "$KIT/work/experiment.py" --variant aliases --stage all "${COMMON[@]}"
"$GPU_PY" -I -s "$KIT/work/experiment.py" --variant tiles --stage all "${COMMON[@]}"
"$GPU_PY" -I -s "$KIT/work/experiment.py" --variant student_tiles --stage all "${COMMON[@]}" --student-python "$STUDENT_PY" --student-checkpoint "$STUDENT_CHECKPOINT"
```

Use `--stage gpu` when the GPU node lacks the CPU inputs. After the operator returns the results, the same command with `--stage cpu` runs selection, pricing and comparison. Use `--stage plan` for a CPU-only dry run that writes the manifest and work estimate without loading either model. The `COMMON` paths must still identify the baseline cache for its content hashes. For student_tiles, an existing bound presence file can be supplied with `--presence`; otherwise the command produces PRESENCE.jsonl first, then seals its hash into the variant manifest. Its delivered MANIFEST.template.json documents the planned settings; a real presence hash is required before inference.

Every variant has MANIFEST.json, ESTIMATE.json, a binding receipt, per-capture append-only journals and completion receipts. Candidate resume verifies the manifest, all existing capture content, and the journal’s final hash. CPU pricing now writes per-capture receipts and resumes only hash-matched capture outputs. Dense_link05 validates and reuses the dense cache with a separate selector contract. Baseline records remain unchanged for prompt/tile variants except that merged records add source provenance and unique local query IDs. Every proposal retains its original conditional score, source presence and joint score. Duplicate masks with IoU>0.95 are suppressed, preferring existing baseline masks.

Dense inference checks that its `(joint>=0.2, cap=10)` subset reproduces baseline query IDs, scores within 0.001, and mask IoU≥0.99. A parity failure stops the run. This prevents a changed model or source revision from masquerading as a density gain.

A STOP file in a variant’s `candidates/` or `presence/` directory stops at the next work boundary. Write `RESUME` into the same file and repeat the command after a clean cap/STOP exit. Exit 4 is a clean cap stop. A failure or 900-second stall writes HALTED.json and never restarts automatically. Unexpected kills must be reported and reviewed under the cluster rules. `--review-halt` is available only after that review; it is not a retry policy. A torn or corrupt capture is preserved and requires a fresh output root. The watchdog only supervises its own child process group.

Each CPU comparison writes:

- `priced/PER_ITEM.jsonl`, selected masks, MASK_DIAGNOSTICS.jsonl, capture receipts and COMPLETE.json.
- `comparison/ROUTE.json` and ROUTE.md, using the original released labels, direct answers, physical-room pairing and 10,000-draw intervals.
- `comparison/COMPARISON.md`, with baseline and variant program scores beside their paired difference interval and the variant-versus-direct interval.
- `comparison/RECALL_PRECISION.json` and PER_INSTANCE.jsonl, with baseline/variant recall and annotation-relative precision by dataset.

The primary decision is the paired program-score difference against baseline. A recall gain alone does not pass. Inspect false accepts and counting merges when precision falls; retain the old route unless the paired interval against direct is strictly above zero. These held-out development results guide the next experiment; they are not a new independent test-set claim.

The shipped CPU tests use synthetic masks and the real inference adapters. They never load a GPU checkpoint. Run them separately with the permitted CPU interpreter:

```bash
"$CPU_PY" -I -s "$KIT/work/test_kit.py"
"$CPU_PY" -I -s "$KIT/work/test_variants.py"
```
