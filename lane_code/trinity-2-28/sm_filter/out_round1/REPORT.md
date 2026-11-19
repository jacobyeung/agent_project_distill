VERDICT: DONE The replacement tools and owner package pass validation; the measured local scan falls from 357,375,373 to 38,301,342 bytes.

The package replaces only `tools/lane_code_filter.py` and `tools/dry_count.py`. Both filter paths share name/path pruning and protect top-level lanes, source folders, kits and delivery containers. The new rules remove identified test outputs, temporary trees, copied lane trees, bundled interpreters, extracted archives and generated build tests. The full decisions, measured evidence and rejected names are in [RULES.md](RULES.md).

Both manifest writers use `gzip.GzipFile(filename="", mtime=0)`. Identical duplicate lists produce identical gzip bytes across repeat runs and labels. The fixture verifies the decompressed content, zero timestamp, absent filename header and parity between both scan paths. `dry_count.py` reads the added regex constants by AST and checks every ancestor against the new rules; its remaining code is byte-identical.

**Measured live scan.** Both runs used robust mode, no manifest argument, `nice -n 10`, a 600-second timeout and stdout redirected to `/dev/null` on `trinity-2-28`. Both exited 0. The new filter selected 319,074,031 fewer bytes (89.28%). These are observations of a live tree, not a frozen-snapshot benchmark.

```text
STATS trinity-2-28 files=43722 bytes=357375373 dups=84861 skipped_oversize=1055 skipped_bigdirs=6 fb_pack/donor/work/suite_base/ fb_pack/donor/work/suite_new/ fb_pack/patchA/work/test_runs/full_base_v4/ fb_pack/patchA/work/test_runs/full_new/ fb_pack/prior2/work/suite/base/LANE_TEST_OUTPUT/ fb_pack/prior2/work/suite/new/LANE_TEST_OUTPUT/ skipped_changed=0 skipped_io=0 skipped_nonregular=0 skipped_symlink=215 skipped_timeout=0
STATS trinity-2-28 files=3537 bytes=38301342 dups=41340 skipped_oversize=328 skipped_bigdirs=2 fb_pack/donor/work/suite_base/ fb_pack/donor/work/suite_new/ skipped_changed=0 skipped_io=0 skipped_nonregular=0 skipped_symlink=5 skipped_timeout=0
```

The new-filter meter forwards every output byte to the existing `/dev/null` stdout and counts each selected path with a read-only stat. It found no stat errors; its total file count and byte count exactly equal STATS. Seventeen top-level lanes had kept files, so the requested top 20 table contains all seventeen. Counts reflect the filter’s global content deduplication and are not each lane’s standalone size.

| Top-level lane | Kept files, measured | Kept bytes, measured |
|---|---:|---:|
| `fb_pack` | 2,359 | 24,293,908 |
| `reads228` | 484 | 6,939,030 |
| `sb_ph2fix` | 275 | 2,368,703 |
| `tree_rebuild14_w24j` | 102 | 1,764,906 |
| `tree_rebuild15_w24l` | 105 | 1,019,471 |
| `sb_ktfix2` | 72 | 841,766 |
| `sb_cachk` | 40 | 588,233 |
| `sm_filter` | 42 | 208,786 |
| `sm_move` | 20 | 115,156 |
| `codex_local` | 24 | 81,582 |
| `sb_mask_phrase` | 2 | 39,061 |
| `sm_cr_move` | 2 | 19,747 |
| `sm_ship2` | 5 | 8,718 |
| `b04host3` | 1 | 6,541 |
| `sm_ship` | 2 | 4,277 |
| `k1_ops3` | 1 | 1,123 |
| `sb_stage228` | 1 | 334 |

The exact live-scan commands were:

```bash
cd /scratch/jjyeung/orch_n30
CUDA_VISIBLE_DEVICES="" LCS_ROBUST_SYNC=1 nice -n 10 timeout 600 /usr/bin/python3 -I -s -B - trinity-2-28 < /scratch/jjyeung/orch_n30/sm_filter/in/tools/lane_code_filter.py > /dev/null 2> /scratch/jjyeung/orch_n30/sm_filter/work/dry-old.stats
CUDA_VISIBLE_DEVICES="" LCS_ROBUST_SYNC=1 nice -n 10 timeout 600 /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/sm_filter/out/tests/meter_scan.py /scratch/jjyeung/orch_n30/sm_filter/out/tools/lane_code_filter.py trinity-2-28 /scratch/jjyeung/orch_n30/sm_filter/work/dry-final-lanes.json > /dev/null 2> /scratch/jjyeung/orch_n30/sm_filter/work/dry-final.stats
```

**Commit replay.** The before columns are measured sums of every listed file in `in/commits/sm_<commit>_s.txt.gz`. The after columns are path-only estimates: exact counts and listed bytes for paths that survive the directory and existing filename-substring predicates. File extensions, file-size limits, MAXDIR, filesystem state and content deduplication are not simulated. Historical DEDUP blobs remain counted at their listed sizes; no assumed timestamp or future manifest savings are subtracted. Seven listed updates outside `lane_code/` are retained under the `repository` label. Quoted Git paths are decoded, and labels are removed before matching relative paths.

| Commit | Before files, measured | Before bytes, measured | After files, estimated | After bytes, estimated |
|---|---:|---:|---:|---:|
| `060e5381` | 25,526 | 232,274,485 | 2,763 | 39,733,138 |
| `06764bf4` | 5,570 | 61,754,410 | 1,061 | 22,043,760 |
| `48fedc21` | 4,636 | 47,040,154 | 1,706 | 27,464,469 |
| `5bf67782` | 11,444 | 93,127,354 | 1,551 | 26,797,085 |
| `97a7ae50` | 10,795 | 118,280,963 | 3,455 | 53,079,728 |
| `b6c19ff8` | 4,597 | 44,840,515 | 1,785 | 29,462,329 |
| `bdaaaad2` | 9,366 | 146,259,122 | 6,804 | 35,128,748 |
| `c9a94e65` | 6,888 | 49,618,530 | 3,306 | 23,826,699 |

Seven commits keep less than 40,000,000 bytes. Commit `97a7ae50` keeps 53,079,728 bytes, including three historical DEDUP blobs totaling 10,379,190 bytes. Its largest retained groups are below. The donor work tree contains source tests and student_pilot/generator code; the route output contains the lane’s packaged deliverables; code/vendor contains project source. Blanket bans on work, base, vendor, tests or out would violate the preservation requirement. Generated build review/integration outputs are excluded by their specific paths. The remaining volume is reported without claiming unmeasured deduplication savings.

| Retained group in `97a7ae50` | Bytes, estimated |
|---|---:|
| `trinity-2-28/fb_pack/donor/work` | 10,528,789 |
| `trinity-1-18/code_sync/meta` | 8,016,047 |
| `trinity-1-18/fb_pack/route/out` | 5,883,486 |
| `trinity-2-28/sb_ktfix2/code/vendor` | 3,816,728 |
| `trinity-1-18/tree_rebuild10_w/w24/work` | 2,585,022 |
| `trinity-3-30/code_sync/meta` | 2,134,047 |
| `trinity-1-18/n_review/tree/student_pilot` | 1,758,769 |
| `trinity-1-18/so_reads228/work/round3` | 1,429,789 |
| `trinity-1-18/n_review/tree/tests` | 1,148,337 |
| `trinity-2-28/sb_ph2fix/sb_mask_phrase/out` | 929,286 |
| `trinity-2-28/sb_ph2fix/sb_mask_phrase/work` | 897,446 |
| `trinity-1-18/fb_pack/cam/out` | 823,750 |

The per-label replay includes zero rows so each supplied label appears in every commit. `repository` accounts for the non-lane tool updates.

| Commit | Label | Before files | Before bytes | After files | After bytes |
|---|---|---:|---:|---:|---:|
| `060e5381` | `orch_n30/briefs` | 3 | 18,439 | 3 | 18,439 |
| `060e5381` | `orch_n30/tools` | 2 | 228,295 | 2 | 228,295 |
| `060e5381` | `repository` | 0 | 0 | 0 | 0 |
| `060e5381` | `trinity-1-18` | 3,446 | 38,620,261 | 1,533 | 25,042,241 |
| `060e5381` | `trinity-2-28` | 21,832 | 189,192,345 | 986 | 10,675,149 |
| `060e5381` | `trinity-3-30` | 243 | 4,215,145 | 239 | 3,769,014 |
| `06764bf4` | `orch_n30/briefs` | 0 | 0 | 0 | 0 |
| `06764bf4` | `orch_n30/tools` | 2 | 195,261 | 2 | 195,261 |
| `06764bf4` | `repository` | 1 | 2,606 | 1 | 2,606 |
| `06764bf4` | `trinity-1-18` | 5,403 | 57,647,133 | 901 | 18,053,716 |
| `06764bf4` | `trinity-2-28` | 0 | 0 | 0 | 0 |
| `06764bf4` | `trinity-3-30` | 164 | 3,909,410 | 157 | 3,792,177 |
| `48fedc21` | `orch_n30/briefs` | 0 | 0 | 0 | 0 |
| `48fedc21` | `orch_n30/tools` | 1 | 186,027 | 1 | 186,027 |
| `48fedc21` | `repository` | 0 | 0 | 0 | 0 |
| `48fedc21` | `trinity-1-18` | 4,622 | 44,636,917 | 1,692 | 25,061,232 |
| `48fedc21` | `trinity-2-28` | 0 | 0 | 0 | 0 |
| `48fedc21` | `trinity-3-30` | 13 | 2,217,210 | 13 | 2,217,210 |
| `5bf67782` | `orch_n30/briefs` | 1 | 7,238 | 1 | 7,238 |
| `5bf67782` | `orch_n30/tools` | 6 | 250,634 | 6 | 250,634 |
| `5bf67782` | `repository` | 0 | 0 | 0 | 0 |
| `5bf67782` | `trinity-1-18` | 11,227 | 89,001,148 | 1,336 | 22,697,619 |
| `5bf67782` | `trinity-2-28` | 0 | 0 | 0 | 0 |
| `5bf67782` | `trinity-3-30` | 210 | 3,868,334 | 208 | 3,841,594 |
| `97a7ae50` | `orch_n30/briefs` | 3 | 18,768 | 3 | 18,768 |
| `97a7ae50` | `orch_n30/tools` | 8 | 269,464 | 8 | 269,464 |
| `97a7ae50` | `repository` | 5 | 44,282 | 5 | 44,282 |
| `97a7ae50` | `trinity-1-18` | 2,138 | 33,859,392 | 1,492 | 29,651,509 |
| `97a7ae50` | `trinity-2-28` | 8,305 | 79,555,191 | 1,612 | 18,572,467 |
| `97a7ae50` | `trinity-3-30` | 336 | 4,533,866 | 335 | 4,523,238 |
| `b6c19ff8` | `orch_n30/briefs` | 4 | 27,627 | 4 | 27,627 |
| `b6c19ff8` | `orch_n30/tools` | 2 | 220,826 | 2 | 220,826 |
| `b6c19ff8` | `repository` | 0 | 0 | 0 | 0 |
| `b6c19ff8` | `trinity-1-18` | 4,405 | 41,441,281 | 1,597 | 26,101,729 |
| `b6c19ff8` | `trinity-2-28` | 0 | 0 | 0 | 0 |
| `b6c19ff8` | `trinity-3-30` | 186 | 3,150,781 | 182 | 3,112,147 |
| `bdaaaad2` | `orch_n30/briefs` | 2 | 15,604 | 2 | 15,604 |
| `bdaaaad2` | `orch_n30/tools` | 8 | 253,642 | 8 | 253,642 |
| `bdaaaad2` | `repository` | 1 | 3,137 | 1 | 3,137 |
| `bdaaaad2` | `trinity-1-18` | 8,936 | 141,128,135 | 6,426 | 30,175,088 |
| `bdaaaad2` | `trinity-2-28` | 0 | 0 | 0 | 0 |
| `bdaaaad2` | `trinity-3-30` | 419 | 4,858,604 | 367 | 4,681,277 |
| `c9a94e65` | `orch_n30/briefs` | 3 | 27,020 | 3 | 27,020 |
| `c9a94e65` | `orch_n30/tools` | 2 | 214,678 | 2 | 214,678 |
| `c9a94e65` | `repository` | 0 | 0 | 0 | 0 |
| `c9a94e65` | `trinity-1-18` | 6,701 | 46,164,245 | 3,121 | 20,394,834 |
| `c9a94e65` | `trinity-2-28` | 0 | 0 | 0 | 0 |
| `c9a94e65` | `trinity-3-30` | 182 | 3,212,587 | 180 | 3,190,167 |

The largest input commit is `060e5381`, with 232,274,485 listed bytes. The following tables use nonoverlapping directory buckets: the label plus the first five directory components below it, or the full parent directory if it is shallower. Each file contributes to one bucket in each classification. The complete replay and TSV tables are in [measurements/](measurements/).

**Top 30 kept directory buckets in `060e5381`.** Listed bytes are measured; classification is a path-only estimate.

| Directory bucket | Bytes |
|---|---:|
| `trinity-1-18/code_sync/meta` | 8,403,549 |
| `trinity-3-30/code_sync/meta` | 2,155,293 |
| `trinity-1-18/fb_pack/patchArev/work/base/student_pilot` | 1,758,769 |
| `trinity-1-18/tree_rebuild10_w/w24/work/build24k/sequence_native` | 1,212,439 |
| `trinity-1-18/fb_pack/patchArev/work/base/tests` | 1,169,876 |
| `trinity-1-18/fb_pack/patchA_out/out` | 896,656 |
| `trinity-1-18/tree_rebuild10_w/w24/work/build24i` | 697,149 |
| `trinity-2-28/fb_pack/patchA/out` | 688,190 |
| `trinity-1-18/tree_rebuild10_w/w24/work/build24k` | 666,287 |
| `trinity-1-18/so_read/out/patches` | 618,276 |
| `trinity-2-28/reads228/kit/so_read` | 605,373 |
| `trinity-1-18/so_read/out_round10/patches` | 600,750 |
| `trinity-3-30/n_review1/k24i/k` | 588,191 |
| `trinity-2-28/reads228/kit/checks` | 582,680 |
| `trinity-1-18/tree_rebuild10_w/w24/out/kit_n_go/k` | 570,861 |
| `trinity-2-28/reads228/kit` | 558,411 |
| `trinity-2-28/code_sync/meta` | 485,598 |
| `trinity-1-18/so_read/out/checks` | 457,440 |
| `trinity-1-18/so_reads228/out` | 452,136 |
| `trinity-1-18/so_read/out` | 432,871 |
| `trinity-1-18/so_read/out_round10` | 419,094 |
| `trinity-2-28/fb_pack/donor/out` | 419,090 |
| `trinity-1-18/so_reads228/out/checks/round3` | 406,980 |
| `trinity-2-28/reads228/kit/checks/round3` | 406,980 |
| `trinity-1-18/so_read/out_round10/checks` | 391,477 |
| `trinity-2-28/tree_rebuild14_w24j/out` | 370,953 |
| `trinity-1-18/tree_rebuild10_w/w24/work/build24k/resolver` | 346,287 |
| `trinity-2-28/fb_pack/donor/work/new/student_pilot` | 343,895 |
| `trinity-1-18/so_reads228/out/checks/round3/cr3_after` | 323,841 |
| `trinity-1-18/so_reads228/work/round4/checks/cr3_replay` | 323,841 |

**Top 30 excluded directory buckets in `060e5381`.** Listed bytes are measured; classification is a path-only estimate.

| Directory bucket | Bytes |
|---|---:|
| `trinity-2-28/fb_pack/prior2/work/cpu_guarded/final_base` | 23,313,695 |
| `trinity-2-28/fb_pack/prior2/work/suite/base` | 23,219,825 |
| `trinity-2-28/fb_pack/prior2/work/suite/new` | 23,054,508 |
| `trinity-2-28/fb_pack/patchA/work/test_runs/full_safe_base` | 19,241,023 |
| `trinity-2-28/fb_pack/patchA/work/test_runs/full_final_new` | 19,240,328 |
| `trinity-2-28/fb_pack/patchA/work/test_runs/full_safe_new` | 19,179,325 |
| `trinity-1-18/tree_rebuild10_w/w24/work/build24k/review_tests` | 5,421,785 |
| `trinity-2-28/fb_pack/donor/work/suite_final_new/sam_r10_4vbxxjdg` | 4,740,011 |
| `trinity-2-28/fb_pack/donor/work/suite_final_new/sam_r10_ljgx_vjf` | 3,156,561 |
| `trinity-2-28/fb_pack/prior2/work/cpu_guarded/final_new` | 2,722,420 |
| `trinity-2-28/fb_pack/prior2/work/unit_release/direction_prior_204184670abb4ddc926283c07a2544c6` | 2,411,830 |
| `trinity-2-28/fb_pack/prior2/work/unit_new2/direction_prior_830c80af67794ce48312f9fd7ff253e2` | 2,411,728 |
| `trinity-2-28/fb_pack/prior2/work/unit_new3/direction_prior_0466c323f92c4bc194ff503545167b44` | 2,411,728 |
| `trinity-2-28/fb_pack/donor/work/suite_final_base/parity_command_ew8gp1dt` | 2,270,081 |
| `trinity-2-28/fb_pack/prior2/work/unit_new/direction_prior_7217c706d03049f4b27fd1617f5650fe` | 2,266,570 |
| `trinity-1-18/tree_rebuild10_w/w24/work/build24f/rehearsal3` | 2,027,037 |
| `trinity-1-18/tree_rebuild10_w/w24/attic/build24i/review_tests_first` | 838,931 |
| `trinity-2-28/fb_pack/donor/work/suite_final_base/finetune_gate_test_s7jg5eqc` | 815,430 |
| `trinity-2-28/fb_pack/donor/work/suite_final_new/finetune_gate_test_t_i4pgk2` | 811,830 |
| `trinity-1-18/tree_rebuild10_w/w24/work/build24f/rehearsal4` | 683,939 |
| `trinity-2-28/fb_pack/donor/work/suite_final_new/parity_command_95piplm_` | 672,884 |
| `trinity-2-28/fb_pack/patchA/work/test_runs/alias_focused_base` | 663,719 |
| `trinity-1-18/tree_rebuild10_w/w24/attic/build24i/resolver600_first` | 659,885 |
| `trinity-1-18/tree_rebuild10_w/w24/attic/build24i/sequence_first` | 640,531 |
| `trinity-3-30/swarm_opt/work/res/so_read_r10/so_read` | 415,867 |
| `trinity-2-28/fb_pack/donor/work/suite_final_new/sft_warmstart_vh4cuojn` | 393,022 |
| `trinity-1-18/so_read/work/apply-round10/51ac61e502af4c98b8f65204e06cf2dd/b5` | 386,788 |
| `trinity-1-18/so_read/work/gate-probe10-53aca9c518f14cd49ccedb8d4fe91bf0/u0` | 335,234 |
| `trinity-1-18/cont_ops21_b/a600/rehearsal/link/fix2` | 312,419 |
| `trinity-2-28/fb_pack/donor/work/suite_final_base/fixture_39_htjj2` | 305,464 |

Reproduce the path replay from the workspace with:

```bash
nice -n 10 /usr/bin/python3 -I -s -B out/tests/simulate.py in/commits
```

Its exact JSON result is preserved in [simulation.json](measurements/simulation.json); aggregate and per-label values are also in [totals.tsv](measurements/totals.tsv) and [commits.tsv](measurements/commits.tsv).

**Tests.** Run the complete suite from the workspace with:

```bash
nice -n 10 bash out/tests/run_all.sh
```

The exact output was:

```text
PASS exact NUL output: both paths, 62 kept files, 79 excluded path cases; FIFO and symlinks skipped
PASS MAXDIR: ordinary directory excluded; top-level lane and tests preserved
PASS deterministic manifests: repeat runs, different labels/directories, both paths; mtime=0, no FNAME
PASS dry_count root gate: every fixture directory rule, ancestor gates and protected/MAXDIR rules in both review modes
PASS stdin delimiters, syntax and unchanged dry_count main
ALL FILTER TESTS PASSED on Python 3.6.8
PASS install/rollback hostname gate refuses trinity-2-28
PASS install and rollback refuse held lock with exit 3
PASS package checksum and installed PREIMAGE mismatches refuse writes
PASS syntax error leaves both installed files unchanged after staging temporaries
PASS install: verified backup, complete tool replacement, POSTIMAGE, modes; robust mode stays ON
PASS rollback: hostname/manual-edit guards, PREIMAGE restoration under lock; robust mode stays ON
PASS rollback restores a partial two-file installation
ALL INSTALL TESTS PASSED on Python 3.6.8
SKIP python3.12: unavailable on PATH
SKIP python3.11: unavailable on PATH
PASS shell syntax
```

The suite tests the production stdin invocation, exact traversal order and NUL bytes, all requested keep/exclude families, generic-pattern near misses, tabs/newlines in names, case variants, source-test preservation, MAXDIR protection, FIFO/symlink handling and deterministic manifests. Install tests use a fake hostname only inside throwaway local fixtures under `work/tmp_*`; no installed tools or external directories are modified.

**Owner installation.** Complete replacements are in [tools/](tools/) and unified diffs against the copied inputs are in [patches/](patches/). PREIMAGE contains exactly the two supplied input hashes, with `tools/` prefixes; POSTIMAGE names the same two tools. SHA256SUMS covers every package file except itself. `install_tools.py` trims the supplied installer pattern to the two replacements.

On `trinity-3-30`, run:

```bash
B=<orch_n30-dir> S=<sync-state-dir> bash -eu install.sh
```

The helper takes the existing `.sync.lock` using nonblocking exclusive flock (the same operation as `flock -n`) and exits 3 with a message if it is held. Under that lock it validates package checksums and PREIMAGE, saves and verifies `$S/install-backups/<uuid>/preimage.tar` plus PREIMAGE.sha256, prepares and syntax-checks both temporary files inside `B/tools`, rechecks PREIMAGE, replaces both files and verifies POSTIMAGE. It preserves file modes and leaves robust mode ON. The filter is installed before dry_count to avoid exposing a new root gate to missing constants.

Rollback uses the backup directory printed by installation:

```bash
B=<orch_n30-dir> S=<sync-state-dir> bash -eu rollback.sh <backup-dir>
```

Rollback uses the same hostname guard and lock, verifies the archived bytes, prepares both files before replacement and checks PREIMAGE afterward. It accepts a partial installation in which each file matches either package image, but refuses to overwrite unrelated manual edits. Backups and failed temporary files remain available for inspection; neither script deletes them.

**Limits and detection.** A legitimate directory that matches a required generic temporary-name rule can be excluded. Review missing files against RULES.md and the path fixtures; top-level lanes and protected containers remain traversable. Reports inside an excluded test-run tree are excluded with that tree; authored reports in preserved delivery folders remain eligible. Protected containers bypass MAXDIR, so unusually large source directories may increase traversal cost. Watch runtime and STATS for timeouts, I/O skips or unexpected growth. Existing extension, size, cache and deduplication policies still apply.

The new rules cannot prove that every ordinary-looking directory is a by-product. Review future commit inventories for new generated names rather than excluding all work or source trees. Deterministic gzip removes header-only changes; a changed duplicate list still legitimately produces a new manifest. A crash between the two replacements can leave mixed tool versions; the verified preimage backup supports rollback. Both install scripts leave the production robust-mode flag unchanged.

**Not done.** The package has not been installed or pushed; installation belongs to the owner on trinity-3-30. No real scans were run on other nodes. Python 3.11 and 3.12 tests were not run because neither executable exists on PATH. Future hourly commit sizes and manifest savings have not been measured, and historical Git blobs have not been removed.

All requested local implementation, replay, live-scan, fixture and packaging work is complete.
