# REVIEW_VERDICT sb_ktrev2: fix build sb_ktfix against review sb_ktrev (read-only, CPU only)
**Verdict: GO AFTER FIXES.** All five required edits and the three optional items are closed. Parts A–C can launch on a card of at least 48 GB once the three inbox files exist. One new defect must be fixed first, because the GO binds the code hash: `heldout_once` consumes the one held-out look before it reads `sb_kbox2/heldout_labels.json`, which does not exist, so the look would be spent and no report written.
Evidence is in `work/` (`tests_rerun.log`, `dryrun_rerun.log`, `mutations.json`, `a0_sample_summary.json`, `trace/trace_{A,B,C}.json`, `stage_list.py`). Nothing was written outside this workspace.
## Required edit (then rerun test_kit.py, dryrun.py and finalize_v3.py, and bind GPU_GO.json to the new code hash)
`code/evaluate_v2.py` line 126: before `consume_heldout()`, insert `p=Path('/scratch/jjyeung/orch_n30/sb_kbox2/heldout_labels.json')` and `if not p.is_file():raise FileNotFoundError('MISSING '+str(p)+'; held-out look not consumed')`. Add a test that this path leaves `out/looks/HELDOUT_once.json` unwritten. Today `labels('heldout')` raises at run_a line 45, outside the per-capture `try`, after `consume_once` has written that receipt. The box kit must also produce the held-out label file, because `sb_kbox2/prepare.py` writes only `train_labels.json`.
## Checks
- Edit 1 CLOSED: `scale_record` returns NO_CONVERT_EXPORT for the two train captures without geometry.npz (evaluate_v2.py:32), and run_a asserts each exported relative error is at most 1e-4 (line 67).
- Edit 2 CLOSED: `update()` drops the MISSING placeholder (line 23); run_b stores added_frame_gain with PASS only when `low>0` (line 118); finalize_v3 writes no placeholder, and `out/tower_frames` holds no stale output.
- Edits 3 and 4 CLOSED: preflight for Part C requires a standalone GO line in `inbox/DA3_GO.txt` (runner.py:18), and `reader_C64_licensed` now equals `context_pays_pose` (metrics.py:70).
- Edit 5 CLOSED: 10 new tests. My probe kills 21 of 21 mutations: my 12 originals (the old suite killed 6) and 9 aimed at the new edits.
- Optional items CLOSED: HALTED is checked before `admit()`, `NOT_ADMITTED_<part>.json` is written, and `kbox_hook.compare` asserts row-set equality. The runner exits 0 when not admitted, so the operator must watch for the receipt rather than the exit code.
- Reruns: 28 of 28 tests pass; the dry run passes (296 captures, 9,472 numbering hashes, 57 s); an A0 sample of 52 of 209 captures matches kbox4 on 197 of 197 rows and 52 of 52 row sets. The delivered tree hashes to code_sha256 53ea9d60…8988, which DRYRUN.json binds.
- GPU_NEED.json `launch_blockers` is true and complete for the GPU passes: GPU_GO.json, SHARED_GPU_RESERVATION.json (its `ledger_path` must exist under /scratch on the run node) and DA3_GO.txt for Part C. The missing held-out labels fall outside its scope.
- Against sb_ktow3, only the listed edits changed (README, evaluate_v2, metrics, runner, kbox_hook, test_kit, finalize_v3), plus relocation (scripts, and path-only changes in the winning-box rule, frame joins and V2 sources).
## Staging (out/STAGE_LIST.tsv, 24,297 rows; each directory row carries the sha256 of a sha256sum manifest in out/manifests/, all 81 verified on disk)
CPU audit-hook traces of each part's load and pricing paths opened nothing on /home or /data* and nothing outside the list. Part C's 3,264 traced dev-S1 frames equal the listed set. Every path is absolute, so stage to the same /scratch/jjyeung paths.
| Part | Bytes | Largest items (GB) |
|---|---|---|
| A | 22.24 GB | Python environment 7.93, G3T 5.63, K1 frames 5.21 (18,944), K1 caches 2.34, GT 1.11 |
| B | 26.01 GB | A's set, plus SAM 3 3.45 and held-out candidates.json 0.31 |
| C | 21.17 GB | Python environment 7.93, DA3 6.76, G3T 5.63, dev-S1 frames 0.82 |
| H | 0.82 GB | held-out caches and GT; also needs A's and B's outputs and the missing label file |
| All | 33.99 GB | union of the rows above |
Only 27 MB of the 7.62 GB capretry overlay is reachable, because geo_bakeoff runtime/site precedes it on sys.path. trin_vl/pyextra holds only a shadowed scipy, so it need not be staged. B's CPU pricing reads A's outputs, so run B after A and copy A's `out/` if they run on different nodes. The code hash does not cover geo_bakeoff, the DA3 and SAM 3 sources or the environments, so verify staged copies against the manifests.
## 24 GB cards
Every part should fit, but the code refuses any card under 48e9 bytes at runner.py:94, and for Part C also at geo_bakeoff backends.py:142, outside the code hash. Edits: lower both checks to 24_000_000_000; vendor geo_bakeoff into `code/vendor` and point gpu_models.py:63 at it so the code hash covers the change; rerun the tests and dry run; rebind the GO. The 40 GB fraction and peak caps clamp harmlessly. bf16 requires an Ampere or newer card.
- A (G3T, 32 frames): fp32 weights 5.63 GB (frozen, so autocast caches no bf16 copies); 43,968 tokens; 4 retained 2,048-channel layers 0.7–1.4 GB; block transients about 1 GB; heads in chunks of 8 add 2–3 GB. Total 9–11 GB. Fits; confidence 95%.
- B (G3T, 64 frames, unmeasured): 87,936 tokens; retained layers 1.4–2.9 GB; block transients about 2 GB with fused attention (a dense-attention fallback would need about 250 GB and fail on 48 GB too); heads 2–4 GB; context about 1 GB. Total 11–15 GB. Fits; 85%. SAM 3 (batch 1, bf16, 1008 px, features offloaded to CPU): 3.45 GB weights plus 2–3 GB, 5–7 GB in total; 90%.
- C: G32 and G64 as above. DA3 at 64 views of 378×504: fp32 weights 6.76 GB plus up to 3.4 GB of autocast bf16 copies (its weights are not frozen); 62,272 tokens × 1,536; 4 retained 3,072-channel layers 1.5 GB; DualDPT in chunks of 8. Total 13–17 GB. Fits; 75%.
Each pass records `max_memory_allocated` per capture, so the first 64-frame capture settles each estimate.
