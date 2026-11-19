VERDICT: DONE All requested review fixes pass regression and package tests; the local scan keeps 47,199,894 of 466,857,790 bytes.

The package replaces `tools/lane_code_filter.py` and `tools/dry_count.py`. It preserves authored kits and all 52 inventoried codex run-record directories, excludes the identified generated outputs, and restricts root-lane protection to node labels. Both scanner paths use the same predicates. DEDUP gzip headers remain deterministic. The preserved input package is `../out_round1/`.

## Review round 1: finding -> fix -> test

| Finding | Fix | Regression test and evidence |
|---|---|---|
| 1: suffix false positives | Exempt word-plus-number endings with one to three digits from the generic suffix rule; keep the explicit tempfile families and 32-hex rule. | `test_finding1_word_number`: kit_parity50, so_reads228 and h_shell400 stay eligible; explicit driver and random mixed suffixes remain excluded. |
| 1: run records | Protect each direct codex_runs child directory, except repository metadata, and mirror that protection in dry_count. | `test_finding1_run_records` and `test_finding6_default_ancestor_gate`: both requested timestamped records survive; generated children remain excluded. |
| 2 and 3: root context | Only labels matching trinity-<n>-<n> protect all root children. Lane, kit, tools and briefs labels receive ordinary root gates. | `test_findings2_3_context`: real fixture scans agree between node and lane contexts, including a 2,002-entry directory; kit output/environment directories are excluded. The original reviewer probe reports hourly=3 and dry_count_view=3 in both modes. |
| 4: Python source files | Remove /lib/python from SUBSTR; add directory-only PATHRE /lib/python[0-9][^/]*/. | `test_finding4_directory_python`: python_compat.py and python3_compat.py survive; Python 2.7/3.12 library directories are excluded. |
| 5: clear by-products | Exclude work/{fcopy,scopy,lcopy,pcopy} and the four observed pytest output names below work/ or out/. | `test_finding5_proven_outputs`: generated copies and pytest trees are excluded; work/base, replay*, pytest_helpers, and source pytest_kit remain eligible. |
| 6: default dry_count mode | Document unconditional ancestor gating in this report and GIT_OWNER.md. | `test_finding6_default_documented` checks both documents; `test_finding6_default_ancestor_gate` exercises an unset environment. |
| 7: existing regex anchor | Keep $ on the pre-existing DIRRE alternatives; new alternatives use \Z. | `test_finding7_old_anchor`: results\n and tmp_x\n remain excluded; the new test_runs alternative does not accept a trailing newline. |

All eight regression methods fail against the preserved package (13 assertion/subtest failures) and pass against the replacement package. The tests adapt the reviewer's context, kit, and fixture probes. Full evidence is in [review-before.txt](measurements/review-before.txt), [review-after.txt](measurements/review-after.txt), and [reviewer-probes.txt](measurements/reviewer-probes.txt). The comparison intentionally retains before/after evidence because the task requires failing regressions before each fix.

Ancestor gates apply even when `LCS_REVIEW2_FIXES` is unset. This changes dry_count's default mode from checking only the selected directory to checking its ancestors too. Its main function remains byte-identical to `in/tools/dry_count.py`. The existing environment flag still controls cross-boundary substring filtering and the deduplication ambiguity guard. Node-wide and per-folder deduplication can yield different counts even when their path gates agree.

`land_kit.py` runs the filter with label `kit`, so its root receives normal name/path/MAXDIR gates. Newly excluded classes include generated test outputs, temporary and 32-hex directories, attic/sandbox/rehearsal/fixtry trees, versioned Python libraries, payload environments, extracted archives, nested lane copies, and generated build work/review/integration directories. Kit landing refuses skipped members unless the owner passes `--allow-skips`; the package includes [GIT_OWNER.md](GIT_OWNER.md) as an accompanying note, not an installed replacement.

## Rule decisions from the inventories

The additional pytest rule names only `pytest_kit`, `pytest_dry`, `pytest_dry_verified`, and `pytest_patched` beneath a `work/` or `out/` ancestor. Their listed descendants are test-case directories containing synthetic packages, generated JSON, and shell stubs. A global pytest-prefix rule could discard source helpers, so other pytest-prefixed names remain eligible. The nested copy rule names only the four requested direct children of work/.

| Rule | Matching file observations | Matching listed bytes |
|---|---|---|
| Named pytest output trees | 290 | 1,296,748 |
| Nested lane copies | 193 | 589,295 |

These evidence counts can overlap other exclusions. [review-recovery.json](measurements/review-recovery.json) records the incremental path decisions for each commit. All nine kit_parity50 trees survive. All 52 codex run-record directories survive, including the six identified by the reviewer. These checks cover inventoried prompt.md, final_message.md and meta.json files.

`work/base` and `replay*` stay eligible as requested. The inventories show source and source-test trees under base; the replay trees are repeated but their names alone do not establish that every member is a generated output. Runtime, vendor, ordinary build directories, and other ambiguous names also stay eligible. [RULES.md](RULES.md) records all accepted and rejected rules and their evidence.

## Measured live scan on trinity-2-28

Both robust scans exited 0 with no manifest argument, stdout redirected to /dev/null, nice -n 10, and timeout 600. The old scan took 11 seconds; the new scan took 2 seconds (wall-clock measurements rounded to whole seconds). Both reported zero timeout, I/O and changed-file skips. The new scan selected 89.89% fewer bytes. These are observations of a changing live tree, which includes the preserved package and review fixtures, not a frozen-snapshot comparison.

```text
STATS trinity-2-28 files=61543 bytes=466857790 dups=122081 skipped_oversize=1270 skipped_bigdirs=6 fb_pack/donor/work/suite_base/ fb_pack/donor/work/suite_new/ fb_pack/patchA/work/test_runs/full_base_v4/ fb_pack/patchA/work/test_runs/full_new/ fb_pack/prior2/work/suite/base/LANE_TEST_OUTPUT/ fb_pack/prior2/work/suite/new/LANE_TEST_OUTPUT/ skipped_changed=0 skipped_io=0 skipped_nonregular=0 skipped_symlink=258 skipped_timeout=0
STATS trinity-2-28 files=5431 bytes=47199894 dups=45873 skipped_oversize=372 skipped_bigdirs=2 fb_pack/donor/work/suite_base/ fb_pack/donor/work/suite_new/ skipped_changed=0 skipped_io=0 skipped_nonregular=0 skipped_symlink=8 skipped_timeout=0
```

The meter forwards the filter's output to /dev/null and stats each selected file. Its totals exactly match STATS; it reports no stat errors or incomplete output records. The table lists up to 20 lanes after global content deduplication.

| Top-level lane | Kept files, measured | Kept bytes, measured |
|---|---|---|
| fb_pack | 3,424 | 29,821,275 |
| reads228 | 484 | 6,939,030 |
| tree_rebuild15_w24l | 891 | 4,146,174 |
| sb_ph2fix | 275 | 2,368,703 |
| tree_rebuild14_w24j | 102 | 1,764,906 |
| sb_ktfix2 | 72 | 841,766 |
| sb_cachk | 40 | 588,233 |
| sm_filter | 59 | 313,503 |
| sm_move | 34 | 226,809 |
| codex_local | 34 | 88,530 |
| sb_mask_phrase | 2 | 39,061 |
| sm_cr_filter | 3 | 31,180 |
| sm_cr_move | 2 | 11,959 |
| b04host3 | 1 | 6,541 |
| sm_ship2 | 4 | 6,490 |
| sm_ship | 2 | 4,277 |
| k1_ops3 | 1 | 1,123 |
| sb_stage228 | 1 | 334 |

The exact commands were the same scan commands as the input package, with fresh output filenames:

```bash
cd /scratch/jjyeung/orch_n30
export CUDA_VISIBLE_DEVICES="" LCS_ROBUST_SYNC=1
nice -n 10 timeout 600 /usr/bin/python3 -I -s -B - trinity-2-28 < /scratch/jjyeung/orch_n30/sm_filter/in/tools/lane_code_filter.py > /dev/null 2> /scratch/jjyeung/orch_n30/sm_filter/work/dry-old-round1.stats
nice -n 10 timeout 600 /usr/bin/python3 -I -s -B /scratch/jjyeung/orch_n30/sm_filter/out/tests/meter_scan.py /scratch/jjyeung/orch_n30/sm_filter/out/tools/lane_code_filter.py trinity-2-28 /scratch/jjyeung/orch_n30/sm_filter/work/dry-new-round1-lanes.json > /dev/null 2> /scratch/jjyeung/orch_n30/sm_filter/work/dry-new-round1.stats
```

The sandbox refused tmux socket access before either scan started; the managed command session ran both scans sequentially. No killed scan was retried.

## Inventory simulation

The before columns sum all listed files in the eight inventories. The after columns are path-only estimates computed exactly from those inventories: size limits, extension gates, MAXDIR, filesystem state and deduplication are not simulated. Historical DEDUP blobs retain their listed sizes. The replay applies root protection according to each label, including tools and briefs. The independent reviewer replay agrees on every commit and label.

| Commit | Before files | Before bytes | After files, estimated | After bytes, estimated |
|---|---|---|---|---|
| 060e5381 | 25,526 | 232,274,485 | 2,920 | 40,630,331 |
| 06764bf4 | 5,570 | 61,754,410 | 1,074 | 22,256,005 |
| 48fedc21 | 4,636 | 47,040,154 | 1,714 | 27,193,564 |
| 5bf67782 | 11,444 | 93,127,354 | 1,501 | 26,936,734 |
| 97a7ae50 | 10,795 | 118,280,963 | 3,468 | 53,219,837 |
| b6c19ff8 | 4,597 | 44,840,515 | 1,798 | 29,606,838 |
| bdaaaad2 | 9,366 | 146,259,122 | 6,645 | 34,039,222 |
| c9a94e65 | 6,888 | 49,618,530 | 3,321 | 23,975,672 |

Six commits keep fewer than 40,000,000 listed bytes. The two larger commits contain the following retained groups. The package preserves their sources, kits and delivery folders; no future deduplication savings are assumed.

Retained groups in `060e5381` (40,630,331 bytes total):

| Directory group | Listed bytes kept |
|---|---|
| trinity-1-18/code_sync/meta | 8,403,549 |
| trinity-3-30/code_sync/meta | 2,155,293 |
| trinity-1-18/fb_pack/patchArev/work/base/student_pilot | 1,758,769 |
| trinity-1-18/tree_rebuild10_w/w24/work/build24k/sequence_native | 1,212,439 |
| trinity-1-18/fb_pack/patchArev/work/base/tests | 1,169,876 |
| trinity-1-18/fb_pack/patchA_out/out | 896,656 |
| trinity-1-18/tree_rebuild10_w/w24/work/build24i | 697,149 |
| trinity-2-28/fb_pack/patchA/out | 688,190 |
| trinity-1-18/tree_rebuild10_w/w24/work/build24k | 666,287 |
| trinity-1-18/so_read/out/patches | 618,276 |
| trinity-2-28/reads228/kit/so_read | 605,373 |
| trinity-1-18/so_read/out_round10/patches | 600,750 |

Retained groups in `97a7ae50` (53,219,837 bytes total):

| Directory group | Listed bytes kept |
|---|---|
| trinity-1-18/code_sync/meta | 8,016,047 |
| trinity-2-28/fb_pack/donor/work/base/tests | 3,828,071 |
| trinity-2-28/fb_pack/donor/work/base/student_pilot | 3,823,495 |
| trinity-2-28/sb_ktfix2/code/vendor/student_pilot | 2,782,997 |
| trinity-3-30/code_sync/meta | 2,134,047 |
| trinity-1-18/fb_pack/route/out/intake | 1,946,026 |
| trinity-1-18/n_review/tree/student_pilot | 1,465,551 |
| trinity-1-18/fb_pack/route/out | 1,272,369 |
| trinity-1-18/n_review/tree/tests | 1,148,337 |
| trinity-2-28/fb_pack/donor/work/base/generator | 1,014,512 |
| trinity-1-18/fb_pack/relcnt/out | 746,343 |
| trinity-1-18/so_read/out/patches | 600,750 |

Per-label counts include zero rows and a repository label for updates outside lane_code/.

| Commit | Label | Before files | Before bytes | After files | After bytes |
|---|---|---|---|---|---|
| 060e5381 | orch_n30/briefs | 3 | 18,439 | 3 | 18,439 |
| 060e5381 | orch_n30/tools | 2 | 228,295 | 2 | 228,295 |
| 060e5381 | repository | 0 | 0 | 0 | 0 |
| 060e5381 | trinity-1-18 | 3,446 | 38,620,261 | 1,572 | 25,195,156 |
| 060e5381 | trinity-2-28 | 21,832 | 189,192,345 | 1,100 | 10,973,296 |
| 060e5381 | trinity-3-30 | 243 | 4,215,145 | 243 | 4,215,145 |
| 06764bf4 | orch_n30/briefs | 0 | 0 | 0 | 0 |
| 06764bf4 | orch_n30/tools | 2 | 195,261 | 2 | 195,261 |
| 06764bf4 | repository | 1 | 2,606 | 1 | 2,606 |
| 06764bf4 | trinity-1-18 | 5,403 | 57,647,133 | 907 | 18,148,728 |
| 06764bf4 | trinity-2-28 | 0 | 0 | 0 | 0 |
| 06764bf4 | trinity-3-30 | 164 | 3,909,410 | 164 | 3,909,410 |
| 48fedc21 | orch_n30/briefs | 0 | 0 | 0 | 0 |
| 48fedc21 | orch_n30/tools | 1 | 186,027 | 1 | 186,027 |
| 48fedc21 | repository | 0 | 0 | 0 | 0 |
| 48fedc21 | trinity-1-18 | 4,622 | 44,636,917 | 1,700 | 24,790,327 |
| 48fedc21 | trinity-2-28 | 0 | 0 | 0 | 0 |
| 48fedc21 | trinity-3-30 | 13 | 2,217,210 | 13 | 2,217,210 |
| 5bf67782 | orch_n30/briefs | 1 | 7,238 | 1 | 7,238 |
| 5bf67782 | orch_n30/tools | 6 | 250,634 | 6 | 250,634 |
| 5bf67782 | repository | 0 | 0 | 0 | 0 |
| 5bf67782 | trinity-1-18 | 11,227 | 89,001,148 | 1,284 | 22,810,528 |
| 5bf67782 | trinity-2-28 | 0 | 0 | 0 | 0 |
| 5bf67782 | trinity-3-30 | 210 | 3,868,334 | 210 | 3,868,334 |
| 97a7ae50 | orch_n30/briefs | 3 | 18,768 | 3 | 18,768 |
| 97a7ae50 | orch_n30/tools | 8 | 269,464 | 8 | 269,464 |
| 97a7ae50 | repository | 5 | 44,282 | 5 | 44,282 |
| 97a7ae50 | trinity-1-18 | 2,138 | 33,859,392 | 1,504 | 29,780,990 |
| 97a7ae50 | trinity-2-28 | 8,305 | 79,555,191 | 1,612 | 18,572,467 |
| 97a7ae50 | trinity-3-30 | 336 | 4,533,866 | 336 | 4,533,866 |
| b6c19ff8 | orch_n30/briefs | 4 | 27,627 | 4 | 27,627 |
| b6c19ff8 | orch_n30/tools | 2 | 220,826 | 2 | 220,826 |
| b6c19ff8 | repository | 0 | 0 | 0 | 0 |
| b6c19ff8 | trinity-1-18 | 4,405 | 41,441,281 | 1,606 | 26,207,604 |
| b6c19ff8 | trinity-2-28 | 0 | 0 | 0 | 0 |
| b6c19ff8 | trinity-3-30 | 186 | 3,150,781 | 186 | 3,150,781 |
| bdaaaad2 | orch_n30/briefs | 2 | 15,604 | 2 | 15,604 |
| bdaaaad2 | orch_n30/tools | 8 | 253,642 | 8 | 253,642 |
| bdaaaad2 | repository | 1 | 3,137 | 1 | 3,137 |
| bdaaaad2 | trinity-1-18 | 8,936 | 141,128,135 | 6,430 | 30,141,086 |
| bdaaaad2 | trinity-2-28 | 0 | 0 | 0 | 0 |
| bdaaaad2 | trinity-3-30 | 419 | 4,858,604 | 204 | 3,625,753 |
| c9a94e65 | orch_n30/briefs | 3 | 27,020 | 3 | 27,020 |
| c9a94e65 | orch_n30/tools | 2 | 214,678 | 2 | 214,678 |
| c9a94e65 | repository | 0 | 0 | 0 | 0 |
| c9a94e65 | trinity-1-18 | 6,701 | 46,164,245 | 3,134 | 20,521,387 |
| c9a94e65 | trinity-2-28 | 0 | 0 | 0 | 0 |
| c9a94e65 | trinity-3-30 | 182 | 3,212,587 | 182 | 3,212,587 |

The largest input commit is `060e5381`. The following top-30 groups use label plus up to five directory components, so rows do not double-count files.

Top 30 kept directory groups:

| Directory group | Listed bytes, path-only |
|---|---|
| trinity-1-18/code_sync/meta | 8,403,549 |
| trinity-3-30/code_sync/meta | 2,155,293 |
| trinity-1-18/fb_pack/patchArev/work/base/student_pilot | 1,758,769 |
| trinity-1-18/tree_rebuild10_w/w24/work/build24k/sequence_native | 1,212,439 |
| trinity-1-18/fb_pack/patchArev/work/base/tests | 1,169,876 |
| trinity-1-18/fb_pack/patchA_out/out | 896,656 |
| trinity-1-18/tree_rebuild10_w/w24/work/build24i | 697,149 |
| trinity-2-28/fb_pack/patchA/out | 688,190 |
| trinity-1-18/tree_rebuild10_w/w24/work/build24k | 666,287 |
| trinity-1-18/so_read/out/patches | 618,276 |
| trinity-2-28/reads228/kit/so_read | 605,373 |
| trinity-1-18/so_read/out_round10/patches | 600,750 |
| trinity-3-30/n_review1/k24i/k | 588,191 |
| trinity-2-28/reads228/kit/checks | 582,680 |
| trinity-1-18/tree_rebuild10_w/w24/out/kit_n_go/k | 570,861 |
| trinity-2-28/reads228/kit | 558,411 |
| trinity-2-28/code_sync/meta | 485,598 |
| trinity-1-18/so_read/out/checks | 457,440 |
| trinity-1-18/so_reads228/out | 452,136 |
| trinity-1-18/so_read/out | 432,871 |
| trinity-1-18/so_read/out_round10 | 419,094 |
| trinity-2-28/fb_pack/donor/out | 419,090 |
| trinity-3-30/swarm_opt/work/res/so_read_r10/so_read | 415,867 |
| trinity-1-18/so_reads228/out/checks/round3 | 406,980 |
| trinity-2-28/reads228/kit/checks/round3 | 406,980 |
| trinity-1-18/so_read/out_round10/checks | 391,477 |
| trinity-2-28/tree_rebuild14_w24j/out | 370,953 |
| trinity-1-18/tree_rebuild10_w/w24/work/build24k/resolver | 346,287 |
| trinity-2-28/fb_pack/donor/work/new/student_pilot | 343,895 |
| trinity-1-18/so_reads228/out/checks/round3/cr3_after | 323,841 |

Top 30 excluded directory groups:

| Directory group | Listed bytes, path-only |
|---|---|
| trinity-2-28/fb_pack/prior2/work/cpu_guarded/final_base | 23,313,695 |
| trinity-2-28/fb_pack/prior2/work/suite/base | 23,219,825 |
| trinity-2-28/fb_pack/prior2/work/suite/new | 23,054,508 |
| trinity-2-28/fb_pack/patchA/work/test_runs/full_safe_base | 19,241,023 |
| trinity-2-28/fb_pack/patchA/work/test_runs/full_final_new | 19,240,328 |
| trinity-2-28/fb_pack/patchA/work/test_runs/full_safe_new | 19,179,325 |
| trinity-1-18/tree_rebuild10_w/w24/work/build24k/review_tests | 5,421,785 |
| trinity-2-28/fb_pack/donor/work/suite_final_new/sam_r10_4vbxxjdg | 4,740,011 |
| trinity-2-28/fb_pack/donor/work/suite_final_new/sam_r10_ljgx_vjf | 3,156,561 |
| trinity-2-28/fb_pack/prior2/work/cpu_guarded/final_new | 2,722,420 |
| trinity-2-28/fb_pack/prior2/work/unit_release/direction_prior_204184670abb4ddc926283c07a2544c6 | 2,411,830 |
| trinity-2-28/fb_pack/prior2/work/unit_new2/direction_prior_830c80af67794ce48312f9fd7ff253e2 | 2,411,728 |
| trinity-2-28/fb_pack/prior2/work/unit_new3/direction_prior_0466c323f92c4bc194ff503545167b44 | 2,411,728 |
| trinity-2-28/fb_pack/donor/work/suite_final_base/parity_command_ew8gp1dt | 2,270,081 |
| trinity-2-28/fb_pack/prior2/work/unit_new/direction_prior_7217c706d03049f4b27fd1617f5650fe | 2,266,570 |
| trinity-1-18/tree_rebuild10_w/w24/work/build24f/rehearsal3 | 2,027,037 |
| trinity-1-18/tree_rebuild10_w/w24/attic/build24i/review_tests_first | 838,931 |
| trinity-2-28/fb_pack/donor/work/suite_final_base/finetune_gate_test_s7jg5eqc | 815,430 |
| trinity-2-28/fb_pack/donor/work/suite_final_new/finetune_gate_test_t_i4pgk2 | 811,830 |
| trinity-1-18/tree_rebuild10_w/w24/work/build24f/rehearsal4 | 683,939 |
| trinity-2-28/fb_pack/donor/work/suite_final_new/parity_command_95piplm_ | 672,884 |
| trinity-2-28/fb_pack/patchA/work/test_runs/alias_focused_base | 663,719 |
| trinity-1-18/tree_rebuild10_w/w24/attic/build24i/resolver600_first | 659,885 |
| trinity-1-18/tree_rebuild10_w/w24/attic/build24i/sequence_first | 640,531 |
| trinity-2-28/fb_pack/donor/work/suite_final_new/sft_warmstart_vh4cuojn | 393,022 |
| trinity-1-18/so_read/work/apply-round10/51ac61e502af4c98b8f65204e06cf2dd/b5 | 386,788 |
| trinity-1-18/so_read/work/gate-probe10-53aca9c518f14cd49ccedb8d4fe91bf0/u0 | 335,234 |
| trinity-1-18/cont_ops21_b/a600/rehearsal/link/fix2 | 312,419 |
| trinity-2-28/fb_pack/donor/work/suite_final_base/fixture_39_htjj2 | 305,464 |
| trinity-2-28/fb_pack/donor/work/suite_final_base/fixture_z4yedmip | 305,271 |

## Tests and reproduction

Run all package tests from the workspace:

```bash
nice -n 10 bash out/tests/run_all.sh
```

Exact output:

```text
PASS exact NUL output: both paths, 62 kept files, 79 excluded path cases; FIFO and symlinks skipped
PASS MAXDIR: ordinary directory excluded; top-level lane and tests preserved
PASS deterministic manifests: repeat runs, different labels/directories, both paths; mtime=0, no FNAME
PASS dry_count root gate: every fixture directory rule, ancestor gates and protected/MAXDIR rules in both review modes
PASS stdin delimiters, syntax and unchanged dry_count main
ALL FILTER TESTS PASSED on Python 3.6.8
test_finding1_run_records (__main__.ReviewRegressions) ... ok
test_finding1_word_number (__main__.ReviewRegressions) ... ok
test_finding4_directory_python (__main__.ReviewRegressions) ... ok
test_finding5_proven_outputs (__main__.ReviewRegressions) ... ok
test_finding6_default_ancestor_gate (__main__.ReviewRegressions) ... ok
test_finding6_default_documented (__main__.ReviewRegressions) ... ok
test_finding7_old_anchor (__main__.ReviewRegressions) ... ok
test_findings2_3_context (__main__.ReviewRegressions) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.688s

OK
PASS install/rollback hostname gate refuses trinity-2-28
PASS install and rollback refuse held lock with exit 3
PASS package checksum and installed PREIMAGE mismatches refuse writes
PASS syntax error leaves both installed files unchanged after staging temporaries
PASS install: verified backup, complete tool replacement, POSTIMAGE, modes; robust mode stays ON
PASS rollback: hostname/manual-edit guards, PREIMAGE restoration under lock; robust mode stays ON
PASS rollback restores a partial two-file installation
ALL INSTALL TESTS PASSED on Python 3.6.8
PASS PREIMAGE matches supplied hashes and input bytes; POSTIMAGE matches replacement bytes
PASS SHA256SUMS: complete coverage and all 36 hashes verify
PASS both unified patches reproduce complete replacements from copied inputs
PASS preserved out_round1 matches every original package checksum
SKIP python3.12: unavailable on PATH
SKIP python3.11: unavailable on PATH
PASS shell syntax
```

The fixture suite checks exact NUL-separated traversal output, shared robust/legacy rules, FIFO and symlink handling, MAXDIR, protected source and delivery directories, deterministic gzip bytes, and unchanged dry_count main. Installer tests exercise hostname/lock/checksum/preimage guards, staged syntax checks, backup verification, rollback and partial-install recovery entirely below work/tmp_*.

The review regression comparison and simulation commands are:

```bash
ROUND1_TARGET=/scratch/jjyeung/orch_n30/sm_filter/out_round1 nice -n 10 /usr/bin/python3 -I -s -B out/tests/test_round1.py
nice -n 10 /usr/bin/python3 -I -s -B out/tests/test_round1.py
nice -n 10 /usr/bin/python3 -I -s -B out/tests/simulate.py in/commits
nice -n 10 /usr/bin/python3 -I -s -B work/tmp_review/review_sim_round1.py
nice -n 10 /usr/bin/python3 -I -s -B work/tmp_review/review_tests.py
```

The first command deliberately exits 1 (eight methods, 13 failures); the second exits 0 (eight methods, OK). Full exact outputs are linked above. The simulation commands emit the JSON in measurements/simulation.json and measurements/reviewer-simulation.json; the reviewer probe output is preserved in measurements/reviewer-probes.txt. Python 3.11 and 3.12 are unavailable on PATH; all executable tests ran on /usr/bin/python3 3.6.8.

## Owner package

Complete replacements are in tools/; unified diffs against in/tools/ are in patches/. PREIMAGE.sha256 contains the two supplied input hashes with tools/ prefixes. POSTIMAGE.sha256 names the same replacements. SHA256SUMS covers every package file except itself. The patches apply to copied inputs and reproduce the replacement bytes. The package and preserved out_round1 checksums verify.

On trinity-3-30, from this package directory:

```bash
B=<orch_n30-dir> S=<sync-state-dir> bash -eu install.sh
# Roll back using the backup path printed by installation:
B=<orch_n30-dir> S=<sync-state-dir> bash -eu rollback.sh <backup-dir>
```

Installation takes the existing nonblocking sync lock (exit 3 if held), verifies package and preimage hashes, saves and verifies a preimage archive, stages and syntax-checks both files, replaces them, and checks POSTIMAGE. The filter is installed before dry_count. Rollback uses the same hostname gate and lock, accepts either image after a partial installation, and refuses unrelated manual edits. Both commands preserve robust mode. The package has not been installed.

## Limits and remaining work

A source directory with another temporary-looking name can still match the generic rules. The word-plus-number exemption also admits some random temporary names. File extensions, size limits, cache rules and deduplication still apply inside protected folders. Generated children and excluded ancestors can suppress a nested deliverable. Protected directories bypass MAXDIR; monitor STATS and scan duration after installation, especially skipped_timeout under the production 144-second scan budget.

Only trinity-2-28 has a fresh live scan. Other nodes have inventory coverage; their runtime remains unmeasured. Deterministic gzip prevents header-only changes, but changing any duplicate pair still changes the large manifest. Future hourly growth and actual manifest savings are unmeasured. The owner still needs to review and install the package; no Git, SSH, production writes, or deletion ran for this task.

The requested review mapping and before/after regression evidence are retained despite the no-archaeology writing rule because the user explicitly requested them. No other superseded measurements are presented as current results.

