The relocation code and fixture tests are complete. All changes are PATH/ENV; `DIFF.md` lists each change. The complete staged-path audit and exact full-root byte total remain pending: `root/STAGING.json` is 25,092,513 bytes, above the requested 4 MiB file limit. A single metadata-only read was requested; no exception has been received. No large payload was rehashed.

Set `TRIN_AREA` to the existing absolute lane directory. The runner rejects relative, missing, file and symlink-component values, as well as parent traversal. The unset default remains `/scratch/jjyeung/orch_n30/trin_read`. The area contains `root/`, this build, `kit_src/` and `work/`. `DEFAULT_ROOT`, the kit fallback, staging download default, writable work directory, cache paths, bind sources and worker environment follow that area. The llguidance overlay comes from this build's pinned stub files. With `TRIN_AREA` set, initial staging reads the accepted bundle from `kit_src/build/pb59bef09f3`; its CONFIG bytes match the existing external reference. The unset reference default is unchanged.

```sh
export TRIN_AREA=/dev/shm/jjyeung/trin_read
/usr/bin/python3 -B "$TRIN_AREA/build_t6p/trinity_read.py" selfcheck
```

Run this after the lane has been placed at that path. This session performed no transfer or production proof. The original 200 GiB free-space floor still applies to the filesystem containing the root, including tmpfs. Relocation does not bypass it.

The active wrapper installs its modules under `root/trinity_runner_t6p/` when `stage` or `need` runs, and binds that directory to `/trinity-build`. An existing legacy bundle remains intact. Selfcheck checks its manifest and the relocated bundle's manifest when both exist; neither can hide an integrity failure in the other. `proof` calls `need` before generation, so it installs the relocated bundle without restaging the model or runtime payload. Start commands from this build, not from the old staged entry point.

The bounded audit is in `../build_p/PATH_AUDIT_P.json`; rerun its generator with `python3 -B ../build_p/audit_relocation.py`. It covers 89 files and records 545 absolute-string occurrences, including 292 references to the original lane. Test-source coverage means the top-level test modules; copied test-output trees are inert evidence and are not recursively collected. Packet receipts are inspected directly, and additional CONFIG paths come from the existing selfcheck report. The oversized STAGING file is explicitly listed as skipped.

| Location or path class | Classification | Handling |
|---|---|---|
| Active runner's original-area default; default-path test assertion | follows TRIN_AREA | Keep the default literal; the environment selects the area. |
| `DEFAULT_ROOT`, kit fallback, reference bundle, stub, writable destinations and bind sources | follows TRIN_AREA / active build | Generate paths from the selected area and executable build. |
| `root/trinity_runner/trinity_read.py:31` | blocks relocation if invoked | This is the original wrapper snapshot with hard-coded AREA, not the pinned scientific reader. Keep it and its MANIFEST unchanged; execute this build and use its separate namespace bundle. |
| Original-area references in INPUT, COMMAND, EXIT, NEED, PROBE and SANDBOX receipts | blocks replay at the new location | These are retained execution records, not inputs to a fresh proof. Preserve bytes; create fresh runs and receipts. Do not replay their argv or run CONFIG. |
| `root/bootstrap/CONFIG.json` | namespace-absolute (unaffected) | It contains no original-lane literal. Its logical model, interpreter and package paths use the existing root binds; authenticated inactive transport evidence remains unchanged. |
| Worker `/scratch/jjyeung/orch_cd/...`, SJ, FSW, AP, UV, STORE and `/trinity-build` | namespace-absolute (unaffected) | Preserve these logical targets. The corresponding bind sources move with the root. |
| `/usr`, `/dev`, `/proc`, `/tmp`, `/home`, `/trinity-kit`, bwrap and vnice | namespace/system-absolute (unaffected) | The destination still needs the host tools and system mounts. The kit uses the area fallback when `/trinity-kit` is absent. |
| External paths in inherited integration tests | blocks running those tests on an otherwise isolated destination | The full suites use existing evalx27/cont_ops reference fixtures. The new miniature relocation test supplies its own area and does not require those fixtures. |

`namespace_worker.py` and `compare_tokens.py` remain byte-identical to their source builds. The unchanged proof payload still supplies selection, inference, scoring and exact-token comparison. The staged runner files still match `root/trinity_runner/MANIFEST.json`. No production root, source build, dl or kit file was edited.

The pinned base manifest is `root/m/ap/90da7ac2/m/base_manifest.json` (SHA256 `ae9247f7c316e7661bfbe4301c28d75b6871db7427d675b8e1cc4c0c41b4b252`). The artifact is `root/fsw/ap/8865619b/runs/469ddece/m544/artifact.json` (SHA256 `1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef`); it pins `full_weights/full_weights.json` (SHA256 `211ae87b0bb03bb0c3d43c1c1412e0f346591ab4ddc75b4d754de2740da0a302`). Only these small metadata files were hashed for space accounting.

| Quantity | Exact bytes |
|---|---:|
| Base files copied per run | 19,329,302,904 |
| Export shards copied per run | 18,819,721,016 |
| Model copies per run | 38,149,023,920 |
| DEV20 frame estimate from `NEED20_t3.txt.json` | 530,841,600 |
| Per-run reserve: models + twice frame estimate + 2 GiB | 41,358,190,768 |
| Unchanged free-space floor | 214,748,364,800 |
| Required free bytes before each run | 256,106,555,568 |

Let R be the complete staged root's byte total, which remains unmeasured under the file-size limit. `--repeat 1` retains R + 38,149,023,920 model-copy bytes; `--repeat 2` retains R + 76,298,047,840 model-copy bytes. The model files already in the root plus those copies total 76,298,047,840 and 114,447,071,760 bytes respectively. Those two numbers exclude the root's runtime, frames and other files; they are not full-root totals.

Budgeting the full per-run reserve and the floor gives R + 256,106,555,568 bytes for repeat 1 and R + 297,464,746,336 for repeat 2. The runner checks the reserve before each sequential run; it does not reserve twice up front. These are exact formula values, not an exact prediction of caches, PNG sizes, logs or filesystem allocation. `SPACE_P.json` records the values and the missing R explicitly. Neither model-copy behavior nor reserve calculation changed.

The full suite passed **262 tests in 40.64 seconds** using the fresh basetemp `build_t6p/tests/p_full_final`. `TESTS_P_FINAL.log` records the result. Command:

```sh
PYTHONDONTWRITEBYTECODE=1 kit_src/.venv/bin/python -B -m pytest -q -p no:cacheprovider \
  --basetemp="$PWD/build_t6p/tests/p_full_final" build_t6p/tests/test_*.py
```

Choose a new, nonexistent basetemp for another run.

The relocation fixture copies small modules into a fresh `/tmp/trin-relocation-*` area. It exercises actual staging, need receipts, path auditing and selfcheck, including import of the installed runner with its inherited TRIN_AREA. It rejects invalid areas, escaped writes, changed legacy and relocated bundles, and, for t6p, linked milestone inputs outside the admitted path rules. Its bwrap executable simulates namespace execution; it does not establish that a real namespace or GPU proof passes on another node. The original root was not subjected to a new 103,157-file selfcheck scan. Existing `work/selfcheck_13_t3b.json` records passing piece/runner/hash/CPU-namespace checks and host-side interpreter-symlink portability failures; those findings are not suppressed here.

No GPU, SSH, network, Git or deletion command was used. The miniature areas and fresh test basetemps retain their evidence. The no-archaeology review retained no borderline historical prose.

`milestone.completed_local` accepts completed regular files under TRIN_AREA as well as /scratch. Partial names, symlink components and non-files remain refused. The existing root has no `trinity_runner_t6` bundle; the first t6p `need` installs `trinity_runner_t6p`, which t6p selfcheck then verifies. `items_export.py` retains its separate cont_ops scorer dependency; exporting ITEMS is outside the relocated proof/milestone-reader path.
