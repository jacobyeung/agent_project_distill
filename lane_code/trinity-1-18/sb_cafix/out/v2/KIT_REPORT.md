# Mask carry kit (v2): KIT_REPORT

The v2 kit is built, and its CPU dry run passes steps 0 to 3; step 4 ran the real SAM 3 tracker end to end on one capture with 8 frames. No GPU was used. The GPU pass needs one 48 GB card for about 1.5 h, with a hard stop at 2.0 h. The bars were frozen at 10:34:03Z (`out/v2/BARS_FROZEN.json`, sha256 edff8724…), before any priced number.

The code is in `kit_v2/`, the outputs in `out/v2/` and the logs in `work/v2/logs/`. The session stopped at 10:06Z (pid 562823) kept running and kept writing `kit/` and other `out/` paths against the superseded spec, so none of those files belong to this kit (`NOTICE_TWO_SESSIONS.md`). Where `out/KIT_REPORT.md` or `out/sb_mask_carry.tar` differ from their copies in `out/v2/`, the `out/v2/` copies are authoritative.

## What is built (`kit_v2/`)
- Seeds (`mc_seeds.py`): S_A0 is the A0 track's served mask on its largest frame; S_GT is the raster instance at its largest visible anchor; S_PHR reads fold-specific policies from `PHRASE_FOLDS.json` (`mc_phrase.py`: one phrase, or a pair whose second call runs only when the first leaves the object not seen) through the phrase kit's own pool functions.
- Frame sets (`mc_frames.py`): D64 (64 dense frames) and A32 (the 32 anchors), with the frame-order check.
- Tracker (`mc_tracker.py`, `mc_track_pass.py`): `build_sam3_video_model` with strict loading of the pinned checkpoint and source (both receipts checked), and its `Sam3TrackerPredictor`. Each capture's 64 frames are embedded once, then each seed propagates forward and backward; an anchor carries when the object score is positive. The pass resumes per (seed set, frame set, capture) under a code contract and per-set seed digests, keeps a cumulative budget ledger, writes `TIMING_RECEIPT.json` after the first 10 captures, drops trailing sets in the registered order while the projection exceeds 2.0 h, and records SIGTERM as KILLED, never rerun.
- Pricing (`mc_price.py`): the carried track through `train_pricing.lifted`, `C_best1` and `C_fused` (each fold's `FREEZE.json` rule) through `train_pricing.evaluate`. Member precision comes from the ladder's own `Objects.get` run on the injected carried track and aggregated by `summarize_train.precision`; IoU member precision, mask IoU, frame recall and false presence are reported beside it without a bar.
- Bars and report (`mc_bars.py`, `mc_summary.py`): the spec's bars verbatim; MISSING counts as not passed; the A32 per-fold cross-fit applies only when A32 completes on all 209 captures; S_PHR has its own row. The summary writes `CARRY_REPORT.md`, `CARRY_DECISION.json`, `K1_CARRY.json` and `PER_ITEM.jsonl`; carried masks stay as RLE per capture in `out/v2/track/<set>/`.
- Guard (`mc_guard.py`), staging (`mc_staging.py`, `manifest.sh`), GPU launcher (`launch_gpu.sh`, `gpu_inner.sh`, `mc_preflight.py`), `post_gpu.sh`, `dryrun.sh`, and tests (`kit_v2/tests/test_kit.py`).

## Dry run (CPU: `bash kit_v2/run_cpu.sh <p1cpu|sam3> <script>`; whole sequence `bash kit_v2/dryrun.sh`; outputs under `out/v2/`)
| step | result | command, output |
|---|---|---|
| 0 precision predicate | PASS: 390/538 = 72.49% at 0.25, 426/581 at 0.15, 366/501 at 0.40, every other-four-folds row equal; the injected path equals `Objects.get` on 2,310/2,310 object-taus | `p1cpu mc_step0.py all`, `dry/STEP0_PRECISION.json` |
| seeds vs A0 served masks | PASS: 13/13 objects on 5 captures, then 770/770 on 209; S_A0 760 seeds (10 refused), S_GT 770; the raw-phrase path equals S_A0 on 770/770 | `p1cpu mc_seeds.py 5`, `mc_seeds.py all --phr-parity`, `seeds/SEEDS.json` |
| 1 seed stub | PASS: `C_best1` = `A0_deployed` on 1,037/1,037 (56.77) | `mc_stubs.py seed`, `mc_price.py`, `mc_summary.py dry`, `dry/STUB_PARITY.json` |
| 2 raster stub | PASS: `C_best1` = `A2_gt_masks` on 1,037/1,037 (73.97); `C_fused` = `fused_cf` on 1,037/1,037 (78.62) | `mc_stubs.py raster`, same |
| 3 frame order | PASS: 209 captures, 13,376 frames hashed, 0 failures | `p1cpu mc_frames.py`, `FRAME_SETS.json` |
| 4a predictor on CPU | Fails, as recorded: `build_sam3_video_predictor` and `Sam3VideoPredictor` raise `RuntimeError: No CUDA GPUs are available` (sam3_video_predictor.py:104; position_encoding.py:55 inside build_tracker). The kit builds the same model directly. | `sam3 mc_probe_predictor.py`, `dry/PREDICTOR_CPU.json` |
| 4b real tracker, 1 capture, 8 frames | PASS: arkitscenes/41048124, 4 sets carried and priced in 153 s (load about 14 s, embedding 108 s, tracking 3 to 13 s per set); peak RSS 7.3 GiB | `sam3 mc_track_pass.py --device cpu --max-frames 8 …`, `dry/track_cpu`, `dry/price_cpu` |
| guard | R0, dev-S1, BENCH v2 and K1 held-out: 0 hits; withheld-80: 5 hits (below); k1_split is train on all 209 (teacher_k1: 204 train, 5 refused); folds of 39/39/38/38/38 rooms, disjoint and equal to the ladder's | `p1cpu mc_guard.py`, `GUARD.json` |
| tests | 23 passed: RLE, phrase-policy parser, anchor records, drop plan, seed digests, bars, timing receipt, launcher card and host checks | `python -m pytest -q kit_v2/tests` |

The stub numbers in `dry/CARRY_REPORT_STUB.md` test the pricing and report code only; they are not carry results.

## GPU need
The pass needs one card with at least 48e9 bytes, run under `vnice.sh` on a node other than trinity-0-13. The launcher refuses a card with more than 1,024 MiB used in either of two readings taken 300 s apart; it also checks the kit manifest and the preflight, then runs `timeout` at the remaining budget. The work is 13,376 frames embedded once, plus 48,640 object-frames for S_A0 and 49,280 for S_GT on D64, and half those counts on A32. On an A6000-class card, assuming 0.12 s per frame for the backbone and 25 ms per object-frame for the tracker, the derived estimate is 1.48 GPU-h for all four sets and 0.80 h for the decision arm (embedding plus S_A0/D64); the hard stop is 2.0 h. Measured on CPU with 8 threads, embedding takes 13.6 s per frame and tracking 1.6 s per object-frame. The 10-capture `TIMING_RECEIPT.json` replaces the derived rates. The S_PHR sets run only after `PHRASE_FOLDS.json` exists and the seeds are rebuilt.
To run: stage the paths below, run `bash kit_v2/launch_gpu.sh` in tmux on the GPU node, then run `bash kit_v2/post_gpu.sh` on CPU to price and report.

## Paths the GPU pass reads (stage at the same absolute paths; 14.92 GB in total, listed in `out/v2/STAGING.json`)
- /scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt (3,450,062,241 B) and /scratch/jjyeung/b01ec87a6f29b/d/k/SAM3_RECEIPT.json (1,123 B)
- /scratch/jjyeung/b01ec87a6f29b/d/s (SAM 3 source, 251 files, 5,812,794 B)
- /scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/vendor_sam/vendor/SAM3_RECEIPT.json (1,123 B)
- /scratch/jjyeung/envs/sam3_capretry_native_v1 (interpreter, 31,270 files, 7,779,340,795 B)
- /scratch/jjyeung/orch_n30/sb_mask_carry/kit_v2 (133,893 B)
- /scratch/jjyeung/orch_n30/sb_mask_carry/out/v2: FRAME_SETS.json (6,293,953 B), seeds/ (211 files, 2,285,680 B), GUARD.json, BARS_FROZEN.json, KIT_MANIFEST.sha256, STAGING.json and STAGING_FRAMES.txt (1.4 MB together)
- /scratch/jjyeung/k1_frames: the 13,376 PNGs listed in out/v2/STAGING_FRAMES.txt (3,677,449,924 B)

The pass writes only to out/v2/track; `vnice.sh` is read from /data3/shared/scripts/vnice on the node.

## MISSING and open
- `PHRASE_FOLDS.json` is NOT_YET. S_PHR's reader, seeds and bars row are built and wait for it; when it lands, rerun `mc_seeds.py all` and `manifest.sh`.
- `K1_TRACK.json` (sb_kobj4) is MISSING on this node (its directory is absent), so the kit runs the tracker itself.
- The withheld-80 assertion fails. Five K1-train captures sit in four withheld rooms: scannet scene0201_02, 0478_00, 0478_01, 0614_02 and 0692_03, covering 25 of the 1,037 rows; teacher_k1 marks them refused. Question: should the carry pass drop them? The default in force keeps them, because the kit fits nothing and the ladder it reproduces priced them. The report adds a sensitivity row on the other 1,012 rows, and `launch_gpu.sh --exclude-withheld` drops the five if the orchestrator rules so.
- No GPU pass has run, so `TIMING_RECEIPT.json`, `CARRY_REPORT.md`, `CARRY_DECISION.json`, `K1_CARRY.json` and `PER_ITEM.jsonl` do not exist yet, and every bar stays MISSING until the pass runs.
- Tarball: `out/sb_mask_carry.tar`, with a copy at `out/v2/sb_mask_carry.tar`; each has its sha256 in a `.sha256` file beside it.
