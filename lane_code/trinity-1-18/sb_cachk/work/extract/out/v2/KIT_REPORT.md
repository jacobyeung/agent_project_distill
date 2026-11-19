# Mask carry kit (v2, sb_cafix): KIT_REPORT

The kit now carries the nine edits that review sb_carev required. Its CPU dry run passes steps 0 to 3 and the new step 1b, and the reviewer's `reproduce.sh` and contract audit pass against this code. Step 4 ran the real SAM 3 tracker on one whole capture (all 64 frames) but is PARTIAL: three of the four GPU arms finished in 2,291 s on 8 threads, and the measured projection for all four (2,739 s) exceeded the 45-minute limit, so the kit dropped S_GT/A32. No GPU was used. The GPU pass needs one card with at least 24e9 bytes and native bf16 (compute capability 8.0 or higher), so a 24 GB Ampere card fits. Staging totals 14,924,708,860 bytes.

Code is in `kit_v2/`, outputs in `out/v2/`, logs in `work/v2/logs/`. `out/CAFIX_NOTES.md` maps each edit to file:line and its tests.

## Population and bars
- RULING 1056Z (`in/RULING_1056Z.md`) sets the decision population to the 204 captures / 1,012 rows outside the withheld rooms. Every bar, the completeness rule and the A32 per-fold choice read it; the 209 captures / 1,037 rows are reported beside and decide nothing. `POPULATION.json` (id f0ecd8ee…) binds tracking, pricing and the summary, and the pass refuses a resume under another id.
- `BARS_FROZEN.json` keeps its bytes (sha256 edff8724…, frozen 10:34:03Z). `BARS_AMENDMENT.json` (sha256 58f29c15…, 11:43:56Z, before any GPU-priced number) keeps every bar. It replaces two builder resolutions: a positive-score empty mask now carries and counts as an incorrect added member, and the population is the ruling's.
- Phrase folds: `/scratch/jjyeung/orch_n30/sb_mask_phrase/out/PHRASE_FOLDS.json` (sha256 5af09f4b…; `sb_phfix/out/PHRASE_FOLDS.json` does not exist). The producer's arm is W1 (DECISION.json sha256 2dac01fc…, BARS.json sha256 150d16a2…; phrase_worth and phrase_safe PASS). S_PHR is PRESENT: 764 seeds, 20 of which differ from S_A0, all under the single policy `radiator`.

## Dry run (`bash kit_v2/dryrun.sh`; rerun 12:11-12:17Z)
| step | result | output |
|---|---|---|
| 0 precision predicate | PASS: 390/538 = 72.49% at 0.25; the injected path equals `Objects.get` on 2,310/2,310 object-taus | `dry/STEP0_PRECISION.json` |
| seeds | PASS: 13/13 on 5 captures, 770/770 on 209; S_A0 760 (10 refused), S_GT 770, S_PHR 764; raw-phrase parity 770/770 | `seeds/SEEDS.json` |
| 1 seed stub | PASS: `C_best1` = `A0_deployed` on 1,037/1,037 (56.77) and on the 1,012 decision rows (56.93) | `dry/STUB_PARITY.json` |
| 1b empty stub | PASS: `C_best1` = `A0_deployed` on 1,037/1,037; the ladder counts 760 added members (all positive-score empty) and 0 correct | same |
| 2 raster stub | PASS: `C_best1` = `A2_gt_masks` (73.97; 74.39 on 1,012) and `C_fused` = `fused_cf` (78.62; 78.74) on every row | same |
| 3 frame order | PASS: 209 captures, 13,376 frames hashed, 0 failures | `FRAME_SETS.json` |
| 4a predictor on CPU | Fails as recorded (`No CUDA GPUs are available`); the kit builds the model directly | `dry/PREDICTOR_CPU.json` |
| 4 one whole capture | PARTIAL: arkitscenes/41048124, 2 objects, 64 frames. S_A0/D64 909 s, S_GT/D64 925 s, S_A0/A32 444 s (2,291 s in total); embedding 10.6 s per frame, tracking 1.81 s per object-frame; peak RSS 8.37 GiB. S_GT/A32 (about 445 s) and the trailing S_PHR arms were dropped; the three finished arms were priced | `dry/track_cpu_full`, `dry/price_cpu_full`, `DRYRUN.json` |
| tests | 74 passed | `work/v2/logs/tests.log` |

The deployed frame recall is 57.90% (spec 57.9%). The stub report `dry/CARRY_REPORT_STUB.md` shows the decision bars, the beside table, every arm by dataset beside the deployed track's mask numbers, and the frame spacing. On all 209 captures the median anchor gaps are 25, 36 and 269.5 native frames for ARKitScenes, ScanNet and ScanNet++ (spec 25, 35, 272). On the decision population the ScanNet median is 44, because all five withheld captures are ScanNet. The stub numbers test code only; they are not carry results.

## Review reproduction (`review/`, the reviewer's scripts repointed to sb_cafix)
- `reproduce.sh` (with the population step and the empty stub added) passes all nine stub checks. Its population id equals the kit's, and its seed masks are byte-identical on 209/209 captures. `tests_run.py`: 74 passed.
- `contract_audit.py` (verbatim mock) and `contract_audit_4col.py` (4-column nvidia-smi mock) refuse a KILLED ledger with and without `--resume-after-stop` (exit 3, tracker inputs never reached). Both refuse a launch whose second reading shows a busy card. The phrase audit finds 0 of 320 rows mismatched.
- The preflight passes (`work/v2/logs/preflight.log`). A `final` code test on the CPU-priced capture writes every summary output in `work/v2/final_code_test/`.

## GPU need
- Card: one card with at least 24e9 bytes, compute capability 8.0 or higher (native bf16) and at most 1,024 MiB used in two readings taken 300 s apart. It runs under the kit's pinned `vendor/vnice.sh`, on a node other than trinity-0-13, with `timeout` at the remaining budget. The pass also refuses a card without bf16 (exit 6).
- Memory, with a batch of one frame per backbone forward and one object per tracker step: fp32 weights take 3.45 GB. The cache of a 64-frame unit takes 1.46 GB at 22.8 MB per frame (the fp32 1008 px image plus the bf16 backbone levels). The bf16 ViT activation peak takes about 1.5 GB and the CUDA context about 1 GB. The total, about 7.4 GB, fits a 24 GB Ampere card (A10/A10G, A30, A5000, RTX 3090) with a 3.2x margin. The CPU peak RSS of 8.37 GiB, all fp32, agrees.
- Hours: each arm embeds the frames it reads, so a capture is embedded once per arm. At the assumed rates (0.12 s per frame, 25 ms per object-frame, 60 s load), cumulative hours in the registered order are 0.80 (S_A0/D64), 1.59 (S_GT/D64), 1.98 (S_A0/A32), 2.37 (S_GT/A32) and 2.45 (both S_PHR arms). The 2.0 h cumulative stop therefore keeps the first three arms and drops S_GT/A32 and S_PHR. The earlier 1.48 h estimate counted one embedding per capture.
- The rates assume an A6000-class card, and a slower 24 GB card takes longer. The `TIMING_RECEIPT.json` written after the first 10 S_A0/D64 captures replaces the assumed rates, and the pass drops trailing arms to stay under 2.0 h.

## Staging (`out/v2/STAGING.json`, 20 items, 14,924,708,860 bytes; stage at the same absolute paths)
- `/scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt` (3,450,062,241 B), its receipt and the vendor receipt; the SAM 3 source `/scratch/jjyeung/b01ec87a6f29b/d/s` (251 files, 5,812,794 B).
- `/scratch/jjyeung/envs/sam3_capretry_native_v1` (31,270 files, 7,779,340,795 B) and the 13,376 PNGs in `/scratch/jjyeung/k1_frames` listed in `STAGING_FRAMES.txt` (3,677,449,924 B).
- `kit_v2/` (30 files, 194,153 B, including the vnice and terminator pins: sha256 3ab2b542… and 19727987…, copied from `/data3/shared/scripts/vnice/`).
- `out/v2/`: FRAME_SETS.json, seeds/ (211 files), GUARD.json, POPULATION.json, BARS_FROZEN.json, BARS_AMENDMENT.json, KIT_MANIFEST.sha256, STAGING_FRAMES.txt and STAGING.json itself. Also `in/RULING_1056Z.md`, and the phrase folds with their DECISION.json and BARS.json.
- The pass, the launcher and the preflight read nothing on `/home` or `/data*`. The pass writes only `out/v2/track` (its caches included), and vnice writes `/tmp/terminator/$USER-<pid>`.
- To run: stage the files, run `bash kit_v2/launch_gpu.sh` in tmux on the GPU node, then run `bash kit_v2/post_gpu.sh` on CPU.

## Open
- No GPU pass has run, so every bar stays MISSING. `K1_TRACK.json` (sb_kobj4) is absent, so the kit runs the tracker itself.
- If `sb_phfix/out/PHRASE_FOLDS.json` appears, the preflight refuses until `mc_seeds.py all` and `manifest.sh` are rerun.
- Archive: `out/sb_cafix.tar`, with its sha256 in `out/sb_cafix.tar.sha256`.
