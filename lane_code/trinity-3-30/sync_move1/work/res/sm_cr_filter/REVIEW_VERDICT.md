VERDICT: GO AFTER FIXES

Reviewed `/scratch/jjyeung/orch_n30/sm_filter/` (filter, dry_count, patches, tests, install/rollback, hashes) against `in/tools/` and the eight `in/commits/*.gz` inventories. One HIGH and one MEDIUM finding need fixing before install. Everything else checked holds.

## Findings

1. **HIGH: the generic tempfile-suffix rule drops a real kit and run records.**
   Evidence: `out/tools/lane_code_filter.py:19` matches any directory name ending in `_` plus 8 chars with a letter and a digit. Lane-style names fit that shape, for example `kit_parity50`, `so_reads228` and `git_fix4`.
   - `trinity-1-18/so_read/out/kit_parity50/` holds `README.md`, `compare.py`, `host.py`, `run.py`, `test_run.py`, `u5.py`, `config.example.json` and three `*_PINS.json` files. It is dropped there and in `out_round3/` through `out_round10/`, all nine copies, and it is kept nowhere else. That is 836,634 listed bytes, inside the protected `out/` and `out_round<N>/` deliverable folders.
   - 6 of 52 codex run records (`prompt.md`, `final_message.md`, `meta.json`) are dropped: `trinity-1-18/codex_local/agent/scratch/codex_runs/20261119T{114206Z_so_git_fix3,123842Z_so_git_fix4,133030Z_sb_fhalias2,134331Z_sb_fullinv2,134431Z_sb_ph2gate3,152211Z_so_reads228}/`. The other 46 are kept, so the cut depends only on lane-name length.
   - Lower impact, because these are copies whose originals stay kept: `trinity-3-30/swarm_opt/work/res/{so_read_r10,so_reads228,so_cr_syncfix2,so_cr_syncfix3,so_cr_reads228}/` (REVIEW_VERDICT.md, REPORT.md). Possibly a record: `trinity-1-18/cont_ops20_b/hd400/validation/h_shell400/{BUILD.json,DIFF.txt}`.
   - `lane_code_scan.py` never deletes, so these files freeze at their last committed version rather than vanish. New versions and new folders of this shape are never published.
   - `RULES.md:13` and `REPORT.md:252` acknowledge the risk in general terms but did not check it against the data.

   Smallest fix: exempt word-plus-number suffixes from the generic rule only. On line 19, change
   `(?s:.*)_(?=[a-z0-9_]{0,7}[a-z])(?=[a-z0-9_]{0,7}[0-9])[a-z0-9_]{8}`
   to
   `(?s:.*)_(?![a-z_]*[a-z][0-9]{1,3}\Z)(?=[a-z0-9_]{0,7}[a-z])(?=[a-z0-9_]{0,7}[0-9])[a-z0-9_]{8}`.
   - Measured on the inventories: kit_parity50, `swarm_opt/work/res/*`, `h_shell400` and 5 of the 6 codex runs come back. The cost is +100,340 to +897,193 kept bytes per commit; the list is under Verified numbers below.
   - `20261119T134431Z_sb_ph2gate3` stays excluded because its suffix has a digit in the middle. Recovering it would need an explicit `codex_runs` path exemption.
   - Every example named in the prompt is still excluded, because the explicit families (`driver_`, `provisional_`, `sam_r10_`, `finetune_gate_test_`) and the 32-hex rule are untouched.
   - About 4% of random mkdtemp names share this shape and would be kept.
   - Add fixture cases `lane/out/kit_parity50/run.py` (keep) and `lane/agent/codex_runs/20261119T152211Z_so_reads228/prompt.md` (keep).

2. **MEDIUM: dry_count no longer matches the hourly for lane folders.**
   - Cause: `lane_code_filter.py:27` protects every root child (`path.count('/') == 2`). `dry_count.py:73-74` runs the filter with `cwd=<lane>`, so the lane's own children become "root children" and skip DIRRE, the hex and suffix rules, and MAXDIR.
   - The `LCS_REVIEW2_FIXES` post-filter (`dry_count.py:88-89`) re-applies only SUBSTR.
   - `GIT_OWNER.md:87-93` tells the owner to run dry_count on `/scratch/jjyeung/orch_n30/swarm_opt` and to read `hourly_files` as hourly-equivalent.
   - Reproduced in `tmp_review/review_tests.py` (CONTEXT lines). On a lane with `test_runs/`, `sandbox/`, `results/`, `attic/`, a 32-hex dir, `kit_parity50/` and a 2001-entry dir, the old filter's dry view equals the hourly (8 = 8). The new filter's dry view keeps 9 files where the hourly keeps 2, so 7 files are overcounted.
   - The builder's test only checks `root_gate` with a mocked `listdir`, so it cannot catch this.

   Smallest fix: protect root children only for node trees. Add at the top of the filter `ROOT_LANES = re.match(r'trinity-[0-9]+-[0-9]+\Z', sys.argv[1] if len(sys.argv) > 1 else '') is not None`, and use `(ROOT_LANES and path.count('/') == 2)` in `protected_dir`.
   - dry_count passes the lane name as its label, so it regains hourly parity. Its own `root_gate` is relative to the boundary and stays correct.
   - The `orch_n30/tools` and `orch_n30/briefs` roots hold no lanes and keep their old behaviour.
   - Change the root-protection fixture cases in `test_filter.py` to use a `trinity-*` label.

3. **LOW: `land_kit.py` is a second consumer that was not analyzed.**
   - `land_kit.py:245` runs the same filter on an extracted kit (`cwd=raw`, label `kit`), and `land_kit.py:260` refuses on any skip unless `--allow-skips`.
   - Reproduced (KIT lines). Kit-root `results/`, `runs/`, `evidence/`, `artifacts/` and `tmp_*/` are now admitted; the same applies to any `*cache*/`, `env/`, `venv/`, `numpy/` or `torch/` at the kit root.
   - Kit files under `attic/`, `sandbox/`, `lib/python*`, or folders matching the suffix or hex rules are now skipped, so landing refuses. This direction fails safe.
   - Fix: the label gate in finding 2 restores the old behaviour at the kit root. List the new skip classes in REPORT and GIT_OWNER.

4. **LOW: `/lib/python` also prunes ordinary source files.**
   - SUBSTR is applied to file paths too (`lane_code_filter.py:151`, `:286`), so `src/lib/python_compat.py` is dropped (KIT test).
   - None of the eight inventories has such a file.
   - Fix: drop `'/lib/python'` from SUBSTR and add `/lib/python[0-9][^/]*/` to PATHRE, which applies to directories only. Update `dry_count.py`'s gate by AST as it already does.

5. **LOW: some by-products are still kept** (path-only, summed over the 8 commits, about 20 MB):
   - Nested lane copies: `trinity-1-18/sb_ph2chk/work/{fcopy,scopy,lcopy}/sb_mask_phrase/…` and `sb_ph2rev/work/{pcopy,lcopy}`.
   - Five near-identical trees of about 300 KB each: `trinity-2-28/fb_pack/prior2/work/replay{,_final,_release,_verified,_delivery}/`.
   - pytest outputs: `trinity-3-30/cont_ops19/work/ownarm/out/fix400/pytest_{kit,dry,dry_verified}/` (about 1.1 MB) and `sb_cachk/work/pytest_patched/`.
   - Plant runtime outputs under `*/runtime/`.
   - In `97a7ae50`, which keeps 53.1 MB against the 40 MB target: copies of the project tree `fb_pack/donor/work/base/` (10.5 MB) and `fb_pack/patchArev/work/base/` (3.8 MB).
   - The decision to keep `work/base` is recorded and defensible. Treat the rest as a follow-up rule set, not a blocker.

6. **LOW: dry_count's default mode changed.**
   - With `LCS_REVIEW2_FIXES` unset, `root_gate` now also gates ancestors (`dry_count.py:27-30`).
   - `GIT_OWNER.md:17` says round-1 behaviour stays active when the variable is unset.
   - The change is an improvement, but it goes beyond "otherwise byte-identical". Record it in REPORT and GIT_OWNER.

7. **INFO: the anchor of the pre-existing rules changed.**
   - DIRRE's anchor went from `$` to `\Z` (`lane_code_filter.py:19`).
   - Old rules no longer match names ending in a newline: `results\n` and `tmp_x\n` used to be excluded and are now kept.
   - Harmless, but `RULES.md:48` says the existing predicates are preserved.

8. **INFO: residual risks.**
   - The DEDUP manifest is now byte-stable. It is still recommitted (8.0–8.4 MB for trinity-1-18) whenever any duplicate pair changes, and it stays the largest kept item per commit.
   - Root protection is required: `sb_stage228` on trinity-2-28 matches the suffix rule and is only kept because it is a root lane. No root lane on trinity-2-28 is newly traversed because of the MAXDIR bypass.
   - Other nodes are unchecked, and scan runtime against `LCS_SCAN_SECONDS=144` was not reported. Watch STATS and `skipped_timeout` after install.

## Checks that passed
- **(2) By-product classes:** all named classes are excluded on the inventories. My replay attributes exclusions to test_runs, test-artifacts, LANE/B2_TEST_OUTPUT, TMPDIR, R2_PROOFS, the 32-hex and suffix rules, the tempfile families, `/orch_n30/` (fb_pack/ro, 44.9 MB), `/scratch/jjyeung/` (payload/files, so_in), `/payload/environment/`, `conda-meta`, `/work/extract/`, attic, rehearsal, fixtry and `work/build*/{review_tests,integration*}`. `work/build*/work`, sandbox and patch_validation have no direct hits beyond overlaps and are covered by fixtures.
- **(3) Rule parity:** robust_scan and the legacy loop call the same `excluded_dir`/`protected_dir` (lines 125/138 and 271/276). The diff changes only those predicates and the gzip line inside robust_scan; `safe_walk`, the O_NOFOLLOW/O_NONBLOCK opens, the deadlines and the regular-file/ino/mtime checks are untouched. My FIFO (in `out/` and at root), symlinked-lane and symlinked-kit fixture gives legacy == robust (skipped_nonregular=2, skipped_symlink=2).
- **(4) Heredoc and stdlib:** the filter is a single ASCII stdlib file with no `LCS_FILTER_EOF` or `PYEOF`. Sending it through real `<<'LCS_FILTER_EOF'` and `<<'PYEOF'` heredocs gives output identical to a direct run. The builder suite passes on /usr/bin/python3 3.6.8; I ran it from a copy under `tmp_review/ws/`. python3.11 and python3.12 are absent.
- **(5) Manifest:** gzip mtime is 0 with no FNAME in both paths. Repeat runs are byte-identical, and robust and legacy bytes are equal. The decompressed content and the stdout list, with the manifest path printed last, are identical to the old filter, including a non-UTF-8 name. `gzip -t` passes, and `land_kit.py:249` reads only the content.
- **(6) dry_count:** apart from findings 2 and 6, the AST reader picks up PATHRE and KEEPDIRRE, the gate mirrors `excluded_dir` plus MAXDIR at every ancestor, and code from `def main` onward is byte-identical.
- **(7) Packaging:** PREIMAGE equals the `in/TOOLS.sha256` entries, and POSTIMAGE matches `out/tools`. `SHA256SUMS -c` passes for all 27 files, and the patches applied to `in/tools` reproduce `out/tools` exactly.
  - install.sh: hostname gate (`install_tools.py:159`), then `flock` LOCK_NB on `$S/.sync.lock` with exit 3 if held (`:162-167`), then the SHA256SUMS and PREIMAGE checks under the lock.
  - It then writes a verified `preimage.tar` plus `PREIMAGE.sha256` to `install-backups/<uuid>`. Temporaries are written with O_EXCL|O_NOFOLLOW, mode preserved and fsync, then compile-checked. PREIMAGE is rechecked, both files are replaced with `os.replace`, filter first, and POSTIMAGE is checked last.
  - Rollback uses the same lock, refuses manual edits and restores in reverse order. Neither script refuses because robust mode is ON.

## Verified numbers
Path-only replay (`tmp_review/review_sim.py`, independent of `simulate.py`) reproduces the report exactly. Before is all listed bytes; after is bytes kept by the path rules. Size limits, MAXDIR and dedup are not simulated.

| Commit | Before bytes | After bytes (as built) | After bytes with fix 1 |
|---|---:|---:|---:|
| 060e5381 | 232,274,485 | 39,733,138 | 40,630,331 |
| 06764bf4 | 61,754,410 | 22,043,760 | 22,256,005 |
| 48fedc21 | 47,040,154 | 27,464,469 | 27,564,809 |
| 5bf67782 | 93,127,354 | 26,797,085 | 27,027,267 |
| 97a7ae50 | 118,280,963 | 53,079,728 | 53,219,837 |
| b6c19ff8 | 44,840,515 | 29,462,329 | 29,606,838 |
| bdaaaad2 | 146,259,122 | 35,128,748 | 35,314,093 |
| c9a94e65 | 49,618,530 | 23,826,699 | 23,975,672 |

I did not re-run the live trinity-2-28 scan, because that would mean a recursive walk of /scratch. Its STATS (357,375,373 bytes old, 38,301,342 bytes new) come from `out/measurements/dry-*.stats`, produced by the real filter via `runpy`.
