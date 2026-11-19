VERDICT: DONE The review fixes are implemented and tested on Python 3.6.8 and 3.12.13; the owner must install, calibrate, and enable them on trinity-3-30.

The delivery contains replacement tools, four patches with tests, an atomic installer, a calibration helper, and checksums. `SHA256SUMS` covers the archive payload; the separate `.tar.gz.sha256` file covers the archive. Robust mode defaults to OFF. The preserved delivery is `../out_round1/`. Work began on trinity-1-18 at 2026-11-19T15:56:56Z; the deadline is 2026-11-19T17:11:56Z.

## Measured results

| Check (measured) | Python 3.6.8 | Python 3.12.13 |
| --- | ---: | ---: |
| Complete functional suite | 55 passed, 0 skipped | 55 passed, 0 skipped |
| Suite duration | 61.821 s | 54.502 s |
| Large manifest lines | 750000 | 750000 |
| Large manifest uncompressed bytes | 127500000 | 127500000 |
| Large manifest gzip bytes | 58724873 | 58724873 |
| Large manifest test duration | 10.333 s | 9.629 s |
| Held-writer node duration (0.35 s + 0.15 s grace) | 0.595 s | 0.536 s |
| Complete held-writer driver duration | 2.055 s | 1.797 s |
| Partial source failure | 1 fake commit; 2 fake pushes; prior files preserved | 1 fake commit; 2 fake pushes; prior files preserved |

The large test injects **750,000 synthetic duplicate lines** at the production manifest-writing boundary. It uses the default `LCS_FILE_SECONDS=3` and outer scan timeout of 120 seconds. It exercises the real join, encoding, gzip write, and rename. Its elapsed time includes fixture generation and validation startup; it does **not** measure a 750,000-file traversal. The synthetic payload has more entropy than the reviewer's real manifest, so these timings are not production calibration.

| Source slot | Accepted archive bytes (3.12 fixture) | Total slot bytes (3.6 fixture) | Total slot bytes (3.12 fixture) |
| --- | ---: | ---: | ---: |
| trinity-1-18 | 10240 | 25002 | 25008 |
| trinity-2-28 | 10240 | 25002 | 25008 |
| trinity-3-30 | 10240 | 24876 | 24882 |
| orch_n30/tools | 51200 | 65767 | 65773 |
| orch_n30/briefs | 10240 | 24811 | 24817 |

The failed trinity-1-18 attempt retained `incoming=10240` and `accepted=10240` bytes on both interpreters. The two archive slots therefore held 20480 bytes in that failure fixture.

Filesystem allocation in the Python 3.12 fixture measured 36,864 bytes for each node slot and the briefs slot, and 77,824 bytes for the tools slot, including each slot directory. [Exact per-slot measurements](evidence/slot_bytes.json)

Slot bytes in the table are measured logical file sizes, including metadata, on the generated fixture. They are not measurements of production disk use. `incoming` and `accepted` are **tar files**, not directories. During a failed transfer, the fixture holds two archives; after success, rename leaves only `accepted`. A source can therefore hold at most its current incoming archive and its preceding accepted archive. Source removal does not accumulate files in either archive. The clone remains additive, as before.

## Review round 1: finding -> fix -> test

| Finding | Fix or decision | Regression evidence |
|---|---|---|
| HIGH 1: manifest exceeds the file deadline | Only the enclosing scan timeout bounds manifest construction. A same-directory temporary file is logged with `MANIFEST_PENDING` **before** creation, then renamed atomically. Exceptions also log `MANIFEST_LEFTOVER`; a process kill still leaves the prelogged name. | `test_750000_duplicate_manifest_default_budgets` fails with `ReadDeadline` against the preserved tools and passes with 750,000 lines. Exception and scan-timeout tests verify every leftover name is logged and the final manifest survives failure. |
| MEDIUM 2: per-run copies grow forever | Reuse `$S/stage-robust/<label>/{incoming,accepted}`. The receiver locks `incoming.lock`; acceptance validates the complete tar before rename. Only labels accepted **in this invocation** enter the copy scan. `program.sh`, `run.log`, and `copy.flags` are overwritten. The aggregate flag list is `$S/flagged/flagged_robust.txt`. | Four-run slot test: stable paths/bytes, accepted hash preserved on failure, no failed-source scan, and no failure-only file leaked by a later success. Receiver-lock and large-log tests pass. |
| MEDIUM 3: missing roots and optional host raise incidents | `rc=66` plus the exact SKIP line becomes `SKIP <label> (no source root)`, with exit 0 when other sources succeed. An unreachable/silent trinity-2-28 is SKIP; an unreachable trinity-1-18 remains FAIL + BLOCKER. | Missing-root and optional-unreachable tests fail before and pass after. The existing required-host failure test still verifies one commit, two pushes, retained clone files, and one BLOCKER. |
| LOW 4: initialization exits omit BLOCKER | Missing/broken helper, invalid budget/configuration, or slot-root creation failure writes the same sync-failed BLOCKER text and exits 2. There is no fallback: enabling robust mode must not silently restore the unbounded path. | Initialization tests inject a missing helper, invalid budget, and failing mkdir. Each produces the BLOCKER. |
| LOW 5: timed-out copy can publish a prefix | Robust copy writes the **already secret-scanned bytes** through `$R/.lcs-copy.pending`, outside every Git-add path, then uses atomic rename. It never opens the destination for truncating writes. Archive acceptance also rejects special entries before any copy scan. Default-off scanner code and behavior remain unchanged. | The timeout regression leaves `truncated` in the old implementation, but preserves the complete prior destination after the fix. Archive tests reject FIFO, symlink, hardlink, device, traversal, and truncated payloads without changing `accepted`. Default-off scanner bytes/stdout/flags match the input. |
| LOW 6: root-cause explanation omits mux fd passing | The explanation below cites the installed protocol, local man page, and local SSH configuration. | The delivery audit fails against the preserved report and passes after correction; local evidence excerpts are included. |
| LOW 7: owner cannot enable the running loop precisely | Enable when `LCS_ROBUST_SYNC=1` **or** `$S/LCS_ROBUST_SYNC` is a regular non-symlink file. A numeric budget file lets the existing tmux loop adopt calibration without restart. The header documents both. The archive has one `so_syncfix/` top-level directory. | Environment-only, file-only, env=0 plus file, default-off, and directory/FIFO/symlink flag tests pass. Installer and calibration tests pass; the archive/header/report audit fails before and passes after. |
| INFO 9: tar exit 1 discards other files from that node | **Keep whole-source rejection.** Tar's “file changed as we read it” does not identify a trustworthy subset of the stream; accepting it could publish changed or incomplete bytes and contradict the failed-attempt isolation requirement. Other sources still publish. | The tar-exit-1 test sees `PIPE 0 1 0`, preserves that source, publishes healthy sources, and records the reason and BLOCKER. |
| INFO 10: file-deadline ranges disagree | Both driver and filter accept only `0 < LCS_FILE_SECONDS <= 30`. Other budgets accept `0 < seconds <= 3600`; zero never disables a timeout. | `30.1` fails during initialization before fake SSH starts. A budget-file value of 30 succeeds. |

Each label has one reused `run.log`, bounded at **65,536 bytes even during the command and after a detached writer survives**. `lane_code_log.py` gives the command a Linux anonymous regular file whose size is sealed by the kernel, waits only for the foreground timeout, and saves a finite snapshot into `run.log`. Later writes cannot alter that saved log or increase the anonymous file's size. Data/manifest writes have no log-size limit. Python 3.6 uses the libc `memfd_create` entry point; Python 3.12 uses `os.memfd_create`. Tests verify regular-file type, the hard byte cap, payload writes larger than the cap, append/reuse, and a detached late writer. The helper requires Linux 3.17+ and, for the Python 3.6 fallback, glibc 2.27+; both tested interpreters use it successfully on this node. [memfd_create(2)](https://man7.org/linux/man-pages/man2/memfd_create.2.html), [F_ADD_SEALS(2)](https://man7.org/linux/man-pages/man2/F_ADD_SEALS.2const.html)

## Cause and verified local evidence

The supplied pre-hotfix filter can block in `open()` on a FIFO named like an allowed JSON file. The regression reproduces that block under a test timeout. The supplied hotfix skips the static FIFO; robust mode also checks the opened file descriptor, rejects replacement races, and bounds each file read.

The legacy driver captures the SSH pipeline with `out=$(... 2>&1)`. A process holding a write descriptor for that pipe can keep command substitution waiting for EOF after the passenger client exits. The held-writer regression demonstrates the failure and verifies that the robust driver returns while the writer remains alive and the sync lock is free.

I verified `/usr/share/doc/openssh/PROTOCOL.mux` on this node: lines 24–29 describe passenger sessions and stdio descriptor passing; lines 84–86 specify that stdin, stdout, and stderr are passed through Unix-domain control messages; lines 99–111 describe the passenger waiting for session completion and handling signals. The master therefore receives the actual session descriptors, including a command-substitution pipe. This is descriptor passing, not merely descriptor inheritance. [Installed protocol excerpt](evidence/PROTOCOL.mux.txt)

I also ran `man ssh_config` locally. Its ControlPersist section says the timed master exits after remaining “idle (with no client connections)” for the configured interval. ControlPersist is not a remote-command deadline. `/home/jjyeung/.ssh/config:27–30` sets `ControlMaster auto` and `ControlPersist 12h` for `trinity-*`; both trinity-1-18 and trinity-3-30.ib match. When a master exists, those legs use the passenger mechanism. [Local man-page excerpt](evidence/ssh_config.man.txt), [local configuration excerpt](evidence/local_ssh_config.txt)

This mechanism fits the reported 45+ minute pipe wait while the remote scanner blocked on the FIFO. The docs establish fd ownership and session lifetime; they do not specify exactly which descriptors close when a passenger is killed. Attribution of the historical surviving descriptor to a particular master remains an inference because no historical fd trace was supplied. The robust driver avoids that dependency: SSH receives regular input/output/error files, the driver waits on its own `setsid --wait timeout --kill-after` process, and child fd 8 is closed.

The local config's `Match exec` at line 21 invokes the rate gate. Its source admits fewer than two new connections per 62-second window; a live master passes immediately. The wrapper also has its own 35-second gate. Those waits consume node/leg budgets, so calibration margins must include them. The provided calibration helper includes explicit estimated margins. [Rate-gate excerpt, lines 2–4 and 13](evidence/ssh_rate_gate.txt)

## Patches and exact test outputs

All changes are against the installed-copy input tree named in the dispatch. `lane_code_scan.py` is now a modified tool and remains covered by both image manifests. `sync_health.py` stays unchanged.

| Patch | Contents |
|---|---|
| [01_filter.diff](patches/01_filter.diff) | Robust filter and filter regressions/reference inputs. |
| [02_stage_driver.diff](patches/02_stage_driver.diff) | Driver, staging and bounded-log helpers, fake-service harness, review regressions, driver tests, delivery audit. |
| [03_tssh.diff](patches/03_tssh.diff) | Caller-owned timeout in robust mode and wrapper regressions. |
| [04_atomic_scan.diff](patches/04_atomic_scan.diff) | Atomic scanner, archive/slot tests, installer/calibration helpers and tests, image manifests. |
| [INSTALL_TOOLS.diff](INSTALL_TOOLS.diff) | Tools-only patch; full replacements are under `tools/`. |

The numbered patches replay into a fresh scratch tree with `--fuzz=0`. Every resulting tool, test, input, installer, and manifest matches the delivery bytes. The tools-only patch also replays exactly; shell syntax and Python compilation pass. [Exact replay output](logs/package_check.txt)

Run the complete suite with either interpreter; tests use only the standard library and import no Torch or other framework. Fake SSH/Git helpers and the robust production Python calls use `-I -s -B`. No real SSH, Git, GPU, or paid API runs in these tests.

```bash
cd /scratch/jjyeung/orch_n30/so_syncfix
CHECK=$(< work/round1_patchcheck_path.txt)
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
nice -n 10 env LCS_TEST_WORK="$PWD/work/reproduce_py36" /usr/bin/python3 -I -s -B "$CHECK/tests/run_tests.py"
nice -n 10 env LCS_TEST_WORK="$PWD/work/reproduce_py312" /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$CHECK/tests/run_tests.py"
```

Python 3.6.8:

```text
Ran 55 tests in 61.821s

OK
```

Python 3.12.13:

```text
Ran 55 tests in 54.502s

OK
```

The complete, exact outputs are [Python 3.6.8](logs/py36_final.txt) and [Python 3.12.13](logs/py312_final.txt). After unpacking elsewhere, use `$PKG/tests/run_tests.py` and choose a fixture directory under `/scratch`.

For before/after checks, run `test_review` with `LCS_TOOLS` set to the preserved tools; omit that variable to test the delivery:

```bash
nice -n 10 env LCS_TOOLS="$PWD/out_round1/tools" LCS_TEST_WORK="$PWD/work/reproduce_before36" \
  /usr/bin/python3 -I -s -B -c 'import sys,unittest; sys.path.insert(0,"out/tests"); r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName("test_review")); sys.exit(not r.wasSuccessful())'
```

The same command with `/scratch/jjyeung/envs/p1cpu/bin/python` runs Python 3.12.13. Both before runs intentionally return 1: 12 test methods run, the default-off control passes, and 13 assertion failures cover the other 11 methods plus initialization subcases. [Exact before output, Python 3.6.8](logs/before_py36.txt), [Python 3.12.13](logs/before_py312.txt)

Run the artifact audit after packaging:

```bash
nice -n 10 /usr/bin/python3 -I -s -B "$PKG/tests/check_delivery.py"
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B "$PKG/tests/check_delivery.py"
```

Its three checks cover protocol citations, header/install/calibration instructions, and the archive's top-level directory plus every embedded checksum. All three fail on the preserved delivery. [Before, Python 3.6.8](logs/delivery_before_py36.txt), [before, Python 3.12.13](logs/delivery_before_py312.txt). The final audit outputs are [Python 3.6.8](logs/delivery_py36.txt) and [Python 3.12.13](logs/delivery_py312.txt).

## Exact owner installation steps

These steps run **on trinity-3-30**. They do not restart tmux or stop an active sync. Stage the archive through the owner's existing approved transport, then unpack it on `/scratch`. The archive contains a `so_syncfix/` directory.

```bash
set -eu
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
export B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
export S=/scratch/jjyeung/distill_sync
# Run in the scratch directory containing the delivered archive and its checksum.
sha256sum -c so_syncfix_bundle.tar.gz.sha256
DELIVERY=/scratch/jjyeung/lcs_syncfix_delivery
mkdir -p "$DELIVERY"
nice -n 10 tar xzf so_syncfix_bundle.tar.gz -C "$DELIVERY"
export PKG="$DELIVERY/so_syncfix"
(cd "$PKG" && sha256sum -c SHA256SUMS)
(cd "$B" && sha256sum -c "$PKG/PREIMAGE.sha256")
nice -n 10 /usr/bin/python3 -I -s -B "$PKG/install_tools.py" "$PKG" "$B" "$S"
(cd "$B" && sha256sum -c "$PKG/POSTIMAGE.sha256")
```

The installer takes `$S/.sync.lock` without waiting; a busy lock returns **3** and makes no installation changes. It requires robust mode OFF and the new helper path absent, checks all five preimages and seven package postimages, and stores **backup copies** in `$S/install-backups/<id>/preimage.tar` plus `PREIMAGE.sha256`. It verifies the bounded-log helper on the destination node before changing any installed file. It writes complete, fsynced temporary files beside the installed tools, validates syntax, repeats the preimage check, and uses `os.replace` (temp + atomic mv semantics) for each file, with the driver last. It then verifies all seven postimages. A failure reports every temporary/backup pathname; it performs no cleanup or deletion. Preimage mismatch means stop and reconcile the live edits.

Measured preimage hashes:

```text
6ccfa27cf92af3fa20b6311e43be720d9140f43cbc7deed8f917355eae85c5d1  tools/lane_code_filter.py
1096b99487c006ce2e2eb1ae5bb46aabce08ef27a0f1fea92c5c455d48c70ce7  tools/lane_code_sync.sh
6bb3905a3280257e4463d86b1d5dff392dc4763daeda6aaa768880fb46472603  tools/tssh.sh
3fa1b6aa702bd26144bd2d1edbb5ed2551001ac54dcb7aa7e7a2557f991cca4b  tools/lane_code_scan.py
f4b0cc8328e1044b9f3d26721891ce683fc9636a240e8a9d077ac26d5bcd4f54  tools/sync_health.py
```

The runtime helpers `$B/tools/lane_code_stage.sh` and `$B/tools/lane_code_log.py` must be absent before this initial install, including as a dangling symlink. The installer enforces that condition. The new scanner's default-off path is byte-compatible with the supplied scanner, so installing with the flag absent preserves the existing loop's behavior.

## Calibrate once before enabling the running loop

The hourly job is tmux session **`lane_sync` on trinity-3-30**, running this existing command:

```bash
while true; do bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/lane_code_sync.sh >> /scratch/jjyeung/distill_sync/sync.log 2>&1; sleep 3600; done
```

Keep that loop running. Its next invocation reads the flag file; a flag change does not alter an invocation already in progress. Before creating the flag, perform **one** robust `--dry` run with generous provisional ceilings. These ceilings are configuration choices, not measured production durations. Dry mode scans and writes the duplicate manifests, but does not transfer archives, copy into the clone, commit, or push.

```bash
set -eu
# B, S, PKG and the resource environment are set by the installation block.
# Leave $S/LCS_ROBUST_SYNC absent throughout calibration.
nice -n 10 env LCS_ROBUST_SYNC=1 LCS_FILE_SECONDS=3 \
  LCS_SCAN_SECONDS=1800 LCS_COPY_SECONDS=1800 LCS_LEG_SECONDS=1900 \
  LCS_REMOTE_SECONDS=2000 LCS_NODE_SECONDS=2200 LCS_KILL_SECONDS=5 \
  bash "$B/tools/lane_code_sync.sh" --dry > "$S/robust_calibration.log" 2>&1
nice -n 10 /usr/bin/python3 -I -s -B "$PKG/calibrate_budgets.py" \
  "$S/robust_calibration.log" > "$S/LCS_ROBUST_BUDGETS.next"
# The helper prints measured per-source durations and labels the budget estimates.
cat "$S/LCS_ROBUST_BUDGETS.next"
mv "$S/LCS_ROBUST_BUDGETS.next" "$S/LCS_ROBUST_BUDGETS"
# Only after successful calibration and budget installation:
: > "$S/LCS_ROBUST_SYNC.next"
mv "$S/LCS_ROBUST_SYNC.next" "$S/LCS_ROBUST_SYNC"
```

The calibrator pairs each `ROBUST stage <label>` timestamp with its `STAGED <label> rc=0` timestamp and requires all four required sources plus `DRY done`. It accepts the optional host's SKIP. It refuses any FAIL or incomplete log, because legacy-compatible dry mode can otherwise return 0 after a stage failure. `set -e` prevents flag creation if the helper refuses. A cluster-killed run is not retried; stop and report it.

The helper sets scan to `max(120, 2*d + 30)`, copy to `max(120, 3*d + 60)`, leg to `max(150, scan + 125)`, remote to `max(160, leg + 30)`, and node to `max(210, remote + 125)`, where `d` is the longest observed dry stage in seconds, with a one-second minimum for timestamp resolution. File and kill budgets remain 3 and 5. It refuses any derived budget above 3600. These are **estimates derived from measured dry durations**; the margins include rate-gate waits. Dry mode cannot measure transfer, archive validation, or copy, so compare the estimates with existing successful hourly durations and inspect the first scheduled robust run's `ROBUST accept`, `STAGED`, `ROBUST copy`, and `COPIED` timestamps before treating them as calibrated transfer/copy limits.

`$S/LCS_ROBUST_BUDGETS` accepts only numeric `LCS_*_SECONDS=value` lines for the seven documented budgets. It is parsed, never sourced. Environment values take precedence. Without that file or environment overrides, defaults are file=3, scan=120, copy=120, leg=150, remote=160, node=210, kill=5 seconds. The file limit is at most 30 seconds; other limits are at most 3600.

For the first scheduled robust run, verify the recorded budgets, required-source STAGED/COPIED lines, `committed` or `no changes`, the existing GitHub hash verification, and absence of a home-push failure. A failed required source still permits healthy-source publication and creates the normal BLOCKER; a missing root or silent optional host does not. Check the lock is released and the slots are reused. Do not immediately rerun a failed production sync.

To disable file-enabled robust mode without deleting anything or restarting the loop:

```bash
mv "$S/LCS_ROBUST_SYNC" "$S/LCS_ROBUST_SYNC.disabled_$(date -u +%Y%m%dT%H%M%SZ)"
```

This disables future invocations of the supplied loop, which does not set `LCS_ROBUST_SYNC=1` in its environment. An explicit environment value of 1 still enables robust mode.

## Limits and work not performed

- Production installation, calibration, actual SSH/mux behavior, real commits/pushes, and production slot sizes were not exercised. This dispatch permits local development only. No claim here substitutes fixture timing for production measurements.
- Tar exit 1 intentionally rejects that whole source. Frequent source mutation can therefore delay its publication; `PIPE 0 1 0`, FAIL, and the BLOCKER identify that case. Healthy sources continue.
- Timeouts depend on scheduling and interruptible kernel operations. They are not hard real-time guarantees. Detached processes may survive, but their descriptors cannot keep the driver's output substitution or sync lock open. A surviving receiver lock prevents overlapping writes to its slot.
- A copy timeout can publish complete clean files processed before the timeout; it cannot publish a partial current file. The named pending file stays outside the committed paths and is overwritten by the next copy attempt. This is per-file atomicity, not a whole-clone transaction.
- Manifest failures can leave one named, prelogged temporary file per failed attempt on the source. The delivery issues no deletion commands. Old stage-run directories from any earlier deployment and the preserved development fixtures are not automatically reclaimed.
- Archive validation rejects unsafe paths and special entries. The private clone and slot directories remain trusted; these changes do not create a hostile-writer sandbox or an atomic snapshot of a changing source tree.
- Existing commit, push, queue, GitHub verification, locking, and normal BLOCKER logic remain intact. Existing Git/queue operations do not acquire a new whole-run deadline.

The review mapping is retained as the user's requested acceptance record. The report describes the delivered behavior and its evidence; interim development outputs remain under `work/`.
