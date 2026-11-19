VERDICT: DONE All round-two fixes are implemented and tested on Python 3.6.8 and 3.12.13; production installation, calibration, and activation remain owner actions on trinity-3-30.

The package contains replacement tools, four patches with tests, saved owner scripts, and checksums. Robust mode defaults to OFF. Work started on trinity-1-18 at 2026-11-19T17:09:41Z; the deadline is 18:09:41Z. The delivery preserved before this work is `../out_round2/`.

## Numbers and evidence

| Measured fixture result | Python 3.6.8 | Python 3.12.13 |
|---|---:|---:|
| Complete functional suite | 72 passed, 0 skipped | 72 passed, 0 skipped |
| Suite duration | 74.537 s | 63.940 s |
| Large manifest lines | 750,000 | 750,000 |
| Large manifest raw / gzip bytes | 127,500,000 / 58,724,873 | 127,500,000 / 58,724,873 |
| Large manifest test duration | 11.976 s | 9.839 s |
| Held-writer node duration, limit 0.55 s plus 0.15 s grace | 0.759 s | 0.739 s |
| Held-writer complete driver duration | 2.452 s | 2.102 s |
| Five slots, first / fourth attempt, logical bytes | 164,362 / 164,362 | 164,392 / 164,392 |
| Failed source's incoming / accepted archive bytes | 10,240 / 10,240 | 10,240 / 10,240 |

These are local synthetic-fixture measurements, not production calibration. The manifest test injects duplicate records at the real manifest-writing boundary; it does not traverse 750,000 files. It uses the default file budget of 3 seconds and scan budget of 120 seconds. The held-writer test confirms that the holder remains alive and the sync lock is free. Scheduling and subprocess startup explain the measured overhead above the configured timeout plus grace.

The slot test keeps one incoming and one accepted tar pathname per label, retains the accepted hash after failure, and never scans a failed attempt. [Exact slot measurements](evidence/slot_bytes.json). The fixed manifest pending pathname also remains bounded at one per label after repeated failures.

The calibration test supplies **synthetic log intervals** of stage=10, accept=100, and copy=300 seconds. The helper derives COPY=630 seconds, exceeding twice the longest acceptance/copy interval. Those supplied intervals are test inputs, not measured production durations. All provisional ceilings and the 5% pre-enable threshold below are configuration choices.

## Review round 2: finding -> fix -> test

| Finding | Delivered fix | Regression |
|---|---|---|
| HIGH 1: scanner install order can silently stop publication | Both scanner copies use the installed scheme-bounded, uncapped URL pattern. PREIMAGE line 4 is `f9460a5e3e23e5f2765e454824645d8970b333817518d626847a5e0cba46fabb`. The installer exercises acceptance and copy before replacing any installed tool. | `test_installed_scanfix_is_preimage_and_pattern_in_both_paths`; `test_installer_refuses_old_layout_even_with_matching_postimage`. The latter substitutes an old-layout scanner and regenerates its postimage checksum; installation still refuses and preserves every installed tool. |
| MEDIUM 2: capped credentials lose detections | Only the scheme uses `{0,32}`; user and password lengths remain uncapped, exactly as installed. | The hash/pattern regression and the symlink-parent queue test cover a 1,150-character synthetic password. Both scanner paths share the same PATS list. |
| MEDIUM 3: dry calibration omits acceptance and copy | One robust `--stage-only` run copies into the clone and performs no commit or push. The helper requires stage, accept, and copy intervals for every successful source and all four required sources. | `test_stage_accept_copy_measured_and_budget_at_least_double`; `test_missing_accept_or_copy_measurement_refused`; saved-script tests verify actual copying, one invocation, no Git call, and no enable flag. |
| LOW 4: robust environment changes queue scanning | Both robust scanner entry points require `LCS_COPY_TMP` as well as `LCS_ROBUST_SYNC=1`. The stage helper sets the marker only for acceptance/copy commands. | `test_queue_scan_through_symlinked_parent_is_legacy_identical` compares exit status, stdout, stderr, and flag bytes through a symlinked parent. The queue block itself is byte-identical to the input. |
| LOW 5: pasted errexit can close the shell; calibration can overlap the hourly run | Install and calibration are saved scripts invoked with `bash -eu`. The calibration script checks the latest hourly END immediately before starting and refuses unless its age is 0–600 seconds. | `test_saved_scripts_and_window_guard` covers 600 seconds, stale/future/missing END, queue-only END, and a newer START. `test_stale_window_refuses_before_start_and_parent_shell_survives` executes the saved script and verifies the parent shell continues. |
| LOW 6: whole-source rejection may starve trinity-1-18 | The pre-enable script prints the count of `trinity-1-18 stage rc=4` lines, hourly run count, percentage, and threshold. Above 5%, it prints STAY LEGACY and exits 2. | `test_pre_enable_counts_failures_against_hourly_runs`: 1/20 passes at 5%; 2/20 refuses at 10%; dry and queue-only starts do not inflate the denominator. |
| INFO 7: manifest leftovers accumulate | One `.dedup-<label>.pending` name is opened with `O_NOFOLLOW|O_NONBLOCK`, checked with `fstat` for a regular file with one link, then truncated with `ftruncate`. Success renames it over the final manifest. | Repeated-failure, regular-slot recovery, and FIFO/symlink/hardlink tests verify bounded leftovers and preservation of linked targets and the final manifest. |
| INFO 8: unordered budgets fail every source | `robust_config` requires `SCAN < LEG < REMOTE < NODE` before starting any source. | `test_unordered_budgets_refused_before_starting_sources` tests all three ordering boundaries and verifies no fake SSH starts. |
| INFO 9: fixtures reach the hourly scanner | Every new fixture root and generated fixture directory uses `tmp_*`; the runner's default is `tmp_test-work`. Existing fixtures were not renamed. | `test_default_fixture_root_is_pruned`; the unchanged filter pruning expression accepts `tmp.*`. |

All 12 round-two regression methods fail against `out_round2/` on both interpreters and pass in the delivered suite. Subcases produce 16 failed assertions before the fixes. [Before, Python 3.6](logs/round2_before_py36.txt), [before, Python 3.12](logs/round2_before_py312.txt).

## Review round 1: retained behavior and tests

The suite retains the 750,000-line manifest test without a per-file deadline around compression; source-slot reuse and failed-attempt isolation; missing-root and optional-host SKIP handling; BLOCKER events for initialization failures; archive rejection and atomic clean-file copying; both environment and regular-file activation switches; and consistent file-budget bounds. Tar exit 1 deliberately rejects the whole source because the stream does not identify a trustworthy subset. Other sources still publish. Existing tests verify one fake commit and two fake pushes after required-source failure.

## Cause and local evidence

The supplied pre-hotfix filter can block on a FIFO named like an allowed JSON file. The robust filter rejects nonregular entries before opening and checks the opened descriptor against replacement races. Its read deadlines apply per file; the scan timeout bounds manifest compression.

The legacy driver's command substitution waits for EOF. A surviving process with its output descriptor can therefore hold that wait after the passenger client exits. `/usr/share/doc/openssh/PROTOCOL.mux:24–29,84–86,99–111`, verified locally, describes stdio descriptor passing from passengers to the master and the passenger's wait for session completion. [Protocol evidence](evidence/PROTOCOL.mux.txt). `man ssh_config`, also verified locally, says ControlPersist expires after the master is “idle (with no client connections)”; it is not a remote-command deadline. [Current man-page excerpt](evidence/ssh_config_round2.txt).

That mechanism fits the reported held-pipe incident. The particular surviving historical descriptor remains an inference because no incident fd trace was supplied. The regression directly reproduces the held-writer failure. Robust staging gives SSH regular descriptors, closes the inherited sync-lock descriptor, and waits on its own `setsid --wait timeout` child. The logger caps each regular log at 65,536 bytes, including detached late writers. These are Linux helpers; the tests cover both Python implementations. No Torch or other framework is imported or relied upon.

[Default-path byte audit](evidence/default_path_audit.txt) confirms that the queue block, scanner's legacy body and all patterns, and filter's legacy body match the installed inputs.

## Patches and exact test outputs

| Patch | Contents |
|---|---|
| [01_filter.diff](patches/01_filter.diff) | Robust filter, filter tests, and installed reference inputs. |
| [02_stage_driver.diff](patches/02_stage_driver.diff) | Driver, staging/logger helpers, fake-service harness, driver/review/log tests, and delivery/replay checks. |
| [03_tssh.diff](patches/03_tssh.diff) | Caller-owned robust timeout and wrapper tests. |
| [04_atomic_scan.diff](patches/04_atomic_scan.diff) | Rebased scanner, archive tests, round-two regressions, owner scripts and integration tests, installer, calibration, and image manifests. |
| [INSTALL_TOOLS.diff](INSTALL_TOOLS.diff) | Tools-only patch against the installed scanfix preimage. |

Run on local scratch with either interpreter. Fixtures are retained; all SSH and Git commands in the tests are fakes.

```bash
L=/scratch/jjyeung/orch_n30/so_syncfix
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
nice -n 10 env LCS_TEST_WORK="$L/work/tmp_reproduce36" /usr/bin/python3 -I -s -B "$L/out/tests/run_tests.py"
nice -n 10 env LCS_TEST_WORK="$L/work/tmp_reproduce312" /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$L/out/tests/run_tests.py"
```

Exact final summaries, in interpreter order:

```text
Ran 72 tests in 74.537s

OK
```

```text
Ran 72 tests in 63.940s

OK
```

Full exact outputs: [Python 3.6.8](logs/py36_final.txt), [Python 3.12.13](logs/py312_final.txt). These runs used the working delivery copy, whose tools, helpers, and tests are byte-identical to `out/`.

Exact before-comparison commands:

```bash
cd "$L"
nice -n 10 env LCS_TOOLS="$L/out_round2/tools" LCS_ROUND2_PACKAGE="$L/out_round2" LCS_TEST_WORK="$L/work/tmp_before36" /usr/bin/python3 -I -s -B -c 'import sys,unittest; sys.path.insert(0,"out/tests"); r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName("test_round2")); sys.exit(not r.wasSuccessful())'
nice -n 10 env LCS_TOOLS="$L/out_round2/tools" LCS_ROUND2_PACKAGE="$L/out_round2" LCS_TEST_WORK="$L/work/tmp_before312" /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c 'import sys,unittest; sys.path.insert(0,"out/tests"); r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName("test_round2")); sys.exit(not r.wasSuccessful())'
```

Both commands intentionally exit 1 before the fixes. Omit the two override variables to check the delivered code.

Replay and archive checks, with either interpreter:

```bash
nice -n 10 env LCS_PATCH_WORK="$L/work/tmp_patchcheck36" /usr/bin/python3 -I -s -B "$L/out/tests/check_patches.py"
nice -n 10 /usr/bin/python3 -I -s -B "$L/out/tests/check_delivery.py"
nice -n 10 env LCS_PATCH_WORK="$L/work/tmp_patchcheck312" /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$L/out/tests/check_patches.py"
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$L/out/tests/check_delivery.py"
```

[Exact replay output, Python 3.6](logs/patch_py36.txt), [Python 3.12](logs/patch_py312.txt); [delivery audit, Python 3.6](logs/delivery_py36.txt), [Python 3.12](logs/delivery_py312.txt). The replay checks apply both patch forms with zero fuzz and zero offsets, compare all delivered bytes, and validate shell syntax and Python compilation.

## Owner sequence: install OFF, pre-enable check, calibration, flag, first real run

**Precondition: scanfix installed.** Before installation, the live `tools/lane_code_scan.py` must have SHA256 `f9460a5e3e23e5f2765e454824645d8970b333817518d626847a5e0cba46fabb`. Both `out/inputs/lane_code_scan.py` and the scanner's pattern line match that installed preimage. The installer verifies every preimage and postimage.

never copy an old-layout lane_code_scan.py over the new one.

Perform these steps on **trinity-3-30**, using the delivered archive and checksum already placed on local scratch through approved transport. The archive contains a single `so_syncfix/` top-level directory. From its containing directory:

```bash
nice -n 10 sha256sum -c so_syncfix_bundle.tar.gz.sha256 && nice -n 10 tar xzf so_syncfix_bundle.tar.gz
export PKG="$PWD/so_syncfix"
export B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
export S=/scratch/jjyeung/distill_sync
```

Run each saved script with `bash -eu`; a refusal exits that child shell. Do not paste a top-level errexit setting into the interactive shell.

1. **Install with robust OFF:** `nice -n 10 bash -eu "$PKG/install.sh"`. The script verifies `SHA256SUMS` and `PREIMAGE.sha256`. The installer takes `.sync.lock` without waiting, checks the scanner protocol, validates bounded logging, saves `$S/install-backups/<id>/preimage.tar` and its manifest, stages complete files, and replaces them with `os.replace`, driver last. It verifies `POSTIMAGE.sha256` afterward. Busy lock returns 3; preimage/protocol mismatch refuses before changing tools. Initial installation requires both new helper paths absent. Keep `$S/LCS_ROBUST_SYNC` absent and the environment switch unset.
2. **Run the pre-enable check:** `nice -n 10 bash -eu "$PKG/pre_enable.sh"`. It counts `trinity-1-18 stage rc=4` lines against `START dry=0 queue_only=0` runs across the entire supplied `sync.log`. Above **5%**, stay legacy. A log with no hourly runs refuses. This threshold is a conservative policy choice, not a measured production failure rate.
3. **Calibrate once:** immediately after an hourly `END`, run `nice -n 10 bash -eu "$PKG/calibrate.sh"`. The script independently refuses if the latest hourly run lacks END, its END is future-dated or older than 600 seconds, or a newer START appears. It verifies the installed postimages and canonical `$S` path, repeats the pre-enable check, then runs exactly one robust `--stage-only` invocation. That invocation copies clean files into the clone but makes no commit or push. It writes `$S/robust_calibration.log`; `calibrate_budgets.py` prints measured intervals and proposed budgets, refuses missing/failed measurements, and installs `$S/LCS_ROBUST_BUDGETS` only on success. It never creates the activation flag.
4. **Create the flag after reviewing successful calibration:** `nice -n 10 bash -eu "$PKG/enable.sh"`. This script checks the installed postimages, failure-rate check, complete calibration log, and exact agreement with the saved budgets under `.sync.lock`, then atomically creates the regular file **`$S/LCS_ROBUST_SYNC`**. No loop restart is needed.
5. **Check the first real robust hourly run:** inspect its START and ROBUST budget lines; STAGED and COPIED with rc=0 for trinity-1-18, trinity-3-30, orch_n30/tools, and orch_n30/briefs; either successful staging/copy or explicit SKIP for optional trinity-2-28; `committed` or `no changes`; `verified GitHub lane-code = <hash>`; no home-push FAIL; and `END ok`. Confirm the lock is free with `flock -n "$S/.sync.lock" true`, check the five stable slot paths, and compare accept-to-STAGED and copy-to-COPIED intervals with the configured COPY budget. Inspect once after completion; do not start another run to obtain these checks.

The existing hourly loop is tmux session **`lane_sync`** on trinity-3-30:

```bash
while true; do bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/lane_code_sync.sh >> /scratch/jjyeung/distill_sync/sync.log 2>&1; sleep 3600; done
```

It reads the regular, non-symlink flag at each invocation. The explicit environment value `LCS_ROBUST_SYNC=1` also enables robust mode. Flag changes do not affect a run already in progress.

Calibration's provisional ceilings are file=3, scan=1800, copy=1800, leg=1900, remote=2000, node=2200, kill=5 seconds. They are estimates, not measurements. For measured maximum stage interval `d` and maximum of all acceptance/copy intervals `c`, the helper derives scan=`max(120, 2*d+30)`, copy=`max(120, 2*c+30)`, leg=`max(150, scan+125)`, remote=`max(160, leg+30)`, and node=`max(210, remote+125)`. File and kill remain 3 and 5. Thus COPY is at least twice every measured acceptance and copy interval. The margins cover one-second timestamp resolution and rate-gate waits; budgets above 3600 refuse. Runtime additionally enforces `SCAN < LEG < REMOTE < NODE`.

The budget file accepts numeric assignments only and is never sourced. Environment values take precedence. Default budgets remain file=3, scan=120, copy=120, leg=150, remote=160, node=210, kill=5; these defaults are not production calibration.

## Risks, detection, and work not done

- No live installation, production calibration, production failure-rate count, real SSH, real Git, push, or GPU use occurred. The owner must complete the sequence above. Tests use only the standard library and fake services.
- Calibration starts only in the required window, but generous provisional ceilings do not guarantee completion before the next hourly wakeup. If it still holds the lock, that hourly invocation returns 3. Inspect the calibration log and sync health; do not retry a killed run or restart the loop automatically.
- A changed source can cause tar exit 1 and whole-source rejection. The pre-enable ratio, FAIL line, and BLOCKER expose this risk. Healthy sources still publish.
- A copy timeout may publish complete clean files processed before the timeout, but never a truncated current file. The fixed pending file remains outside Git-add paths. This is per-file atomicity, not a whole-clone transaction.
- Fixed manifest names assume the sync lock serializes scans of a label. Nonregular or multiply linked slots refuse without truncating their targets. Timeouts can leave the one prelogged pending file; the next successful scan reuses it.
- These checks assume trusted private clone/slot directories. They do not make changing source trees atomic or create a hostile-writer sandbox. The calibration script refuses a symlinked `$S`; queue scans through symlinked parents preserve legacy behavior.
- Existing fixtures and saved deliveries remain in place. No deletion command was used. Development fixtures are under `tmp_*` roots and are pruned by the hourly filter.

The review mappings and before/after comparisons are retained because the dispatch explicitly requests that acceptance record. The remaining prose describes the delivered behavior and its evidence.
