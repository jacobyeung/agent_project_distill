VERDICT: GO AFTER FIXES

## Answer

Yes, after one fix and the passing GPU gate. Patches 01–05 are sound: OFF is byte-identical, the guard and its run failure hold, the operator path is really tested with ON payloads, and round-4 findings 3, 4 and 7 are closed. The step-600 build (`u0/a19.py`) is executable and keeps the reviewed export binding, which closes previous MEDIUM 1. However, it builds from the step-200 A4 package and so drops the batch wrapper that cont_ops' current routed builds add for steps 400/600 (finding 1). The operations after the build are only partly written out (finding 3).

## Checks

- **Step-600 route.** `a19.py` resolves and runs under `-I -s -B`, and the CPU test artifact shows a full build. 9.json `export_binding` equals the supplied binding (`a19.py:124-130`). Job and unpack admission are unchanged (`A4/src/orchard_h10/export_pins.py:62-82`). The fill helper's `REVIEWED_*` constants are resealed, and nothing else in it changes (`a19.py:146-150`, `A4/package/a/4.py:11-13,146-160`). The old route is refused (`a12.py:106`). Every file run by Python 3.6 compiles under `/usr/bin/python3` 3.6.8. cont_ops' binding format (`cont_ops17/work/bind400_partial.json`, `gen400b.py:12`) is a superset of `a19.py:61-62`, and admission ignores the extra keys.
- **(1) OFF is byte-identical.** Patches 01–03 add 33 files under `u0` only, and they rebuild `work/src/u0` and the MANIFEST after-hashes exactly. The A4 base pin (`813fe4c5…`, 927 files) matches MANIFEST and `kit_parity50/BASE_PIN.json`. Patches 04–05 reproduce the delivered operator files from the A4 originals. `operator/0.py` equals the A4 bootstrap, and round-3 reader files a0–a18 (except a12) are unchanged.
- **(2) The guard.** It is unchanged since round 3 (`a0.py:348-397`). An in-memory probe on torch 2.11.0+cpu caught every tested mutation:
  - Per call: `add_` (also under `inference_mode`), `detach().add_`, `_foreach_add_`, `load_state_dict`, `.data` reassignment and `.to(bf16)`.
  - At boundaries: `.data.add_`, an untyped-storage copy and a numpy write.
  - Install: an inference-built model is refused.

  Measured cost is 17 ms per call at 256 tensors and 103 ms at 1,400. The cited torch behaviour matches the installed source (`TensorImpl.h:291-305,413-418,2046-2056`, `optim/sgd.py:378-380`, `autograd/graph.py:242-258`, `InferenceMode.h:30-50`). `ModelMutationError` is a `BaseException`, and nothing in `u0` catches it. `WEIGHTS.json` is written false first and set true only after the final boundary (`a4.py:174-190`). The processor-only switch installs no vision or SAM guard (`a1.py:240`, `a3.py:191-193`).
- **(3) Operator path.** `test_round4.test_f2` runs the real `a/5.py` in node mode, then the real `0.py`, `job.main`, actions 0/1 and the real authenticated unpack. It covers 636 items, five verified journals and a refused unverified partial return. The memory bound adds `cache_bytes(settings)` (`tower_sequence.py`, patch 04), and the arithmetic checks out (12 GiB, with `fits=true` against an 82 GB host budget). The sharding statement is true: `a19.py:126` disables shards, and the operator refuses more than one card.
- **(4) Findings 3, 4 and 7.** Finding 3 is fixed (`unpack_return.py:8-11,60`), and its test fails before the fix (`checks/round4_before.txt`). Findings 4 and 7 were INFO items and are now documented in the NOTE/README. The earlier before-reproductions still fail as recorded (`checks/run_checks4.txt`). `FINAL_INTEGRITY.json` matches its 4 documents, 60 checks, 5 patches, the MANIFEST and the NOTE.
- **(5) Gate and adoption steps.** The 50-item kit is executable as written: seal and stage-kit match `a11.py`, and the extension pins match 33/33. The adoption steps are not fully executable as written (finding 3), and the gate does not pin the adopted read profile (finding 4).

## Findings

1. **MEDIUM: the step-600 package drops cont_ops' batch wrapper.**
   - Evidence: `a19.py:163-164` writes BATCH.sh with the plain `a12.batch` header (`a12.py:64-89`). cont_ops' current routed build for steps 400/600 is `build_r10.py`, which is build_r8 plus `wrap_batch` (`cont_ops17/work/build_r10.py:73-84`; `cont_ops18/STATUS.md:18`; `gen400b.py:10` accepts `step in (400, 600)`).
   - The wrapper adds `#SBATCH --exclude=orchard-community-2` (ORCH 0318Z item 3). It also adds an EXIT trap that copies the node line, exit code and last 60 log lines to `$P/a/x<job>` (item 2), and it forwards USR1 to the reader.
   - Effect: an ON step-600 job could land on the excluded node, and a failure would leave no readable log, unlike the OFF step-400 route.
   - Smallest fix: apply `build_r10.wrap_batch` to the BATCH.sh text in `a19.py:164`. Add a test that the built BATCH.sh contains the exclude line and the trap and still passes `a/5.py`'s bundle guard, which reads only the `b=` line.
2. **LOW: `a19` authenticates neither its base nor its patched inputs.**
   - Evidence: `a19.py:95-107` checks only that the A4 base is self-consistent. It never pins the reviewed A4 payload (`4498fca72a8e…`).
   - It copies `a/5.py`, `tower_sequence.py` and `unpack_return.py` without checking the patched pins in the MANIFEST `operator_files` (`a19.py:139,143`).
   - It overlays every file under `source/u0` without comparing them to `EXTENSION_PINS` (`a19.py:117-122`). It then replaces A4's `orchard_h10/{entry,job,runner,prepare}.py` with aliases derived from that specific A4 (`a19.py:123-124`).
   - Effect: if patch 05 is skipped, the CPU proof lacks `read_cache_bytes` and `0.py` still admits it (`0.py:36-42`). ON unpack would also accept unverified journals. A different A4 base would get its four orchard_h10 files silently replaced.
   - Smallest fix: refuse unless the base payload, the three operator files and the u0 inventory match the MANIFEST and `EXTENSION_PINS`, and the four replaced A4 members equal the bytes the aliases came from.
3. **LOW: the NOTE/README steps after the build are not executable as written.** Each gap fails closed except the dropped pool check, which can waste a GPU read.
   - The README gives a field list for `STEP600_BINDING` but no derivation. cont_ops' format is `bind400_partial.json` filled as in `gen400b.py:1-12`.
   - It says to set `PREP_*` "from the reviewed target binding" (`README.md:51`), but the binding holds hashes; the paths are in `prep_paths`.
   - It gives no step for placing the package at `$P`. `a19` produces no delivery archive or SHA, and A4's place script asserts step 200 (`make_operations.py:27`).
   - It gives no fetch step for the export parts `E/0..3,5`.
   - It gives no allocation command for the `a/5.py` CPU proof, which requires a Slurm job (`make_operations.py:109`).
   - Its bare `3.py submit` (`README.md:67`) drops A4's submit gates. Those gates are the CPU-receipt pass check, an empty general queue, and a return pool of at most 75 MB (`make_operations.py:119-133,173`). It also drops cont_ops' dry checks (`dryres2.py`, `dry2.py`).
   - It gives no unpack command.
   - Smallest fix: make `a19` an ON mode of the build_r10/gen400b route, so that route's existing `o_build`, `o_place_pull_fill` and `o_sub` scripts drive it. Otherwise, list those commands in the README.
4. **LOW: the GPU gate does not pin the adopted read profile.**
   - Evidence: the kit seals whatever `PRIVATE_SETTINGS.json` holds (`README.md:73-78`). The step-600 package always runs `candidates_argmax` with perception memo on, `g3t`, empty `verify_ids` and `save_own_depth=False` (`a19.py:108-113`). The comparator drops `perception_memo` telemetry (`compare.py:11`).
   - The example config sets the 12 GiB, all-cache profile. The processor-only profile (slot 0, 4 GiB) is never gated unless chosen.
   - Smallest fix: in the README, require sealing the step-600 package's prepared settings (A4 `prepare` output with the operator's per-read overrides), and set `enable_caches` and `read_cache_bytes` to the profile being adopted.
5. **INFO: the forecast describes a read this route does not build.** The NOTE's 580-item, 3 h 50 min forecast (`NOTE_FOR_CONT_OPS.md:5`) is the package-D distance read. Package D is a B5 fork at walltime 03:30 (`cont_ops18/STATUS.md:21-26`). `a19` builds only A4's 636-item schedule (`NOTE_FOR_CONT_OPS.md:24`), so D has no ON route. Say so beside the forecast.
6. **INFO: whole-archive identity is enforced only at fill time.** The binding's `archive_bytes`/`archive_sha256` are checked only by the fill helper's sealed constants (`A4/package/a/4.py:146-160`). Job and unpack admission compare the export against `inputs.archives[0]`, not against the binding (`export_pins.py:73-74`). This is A4's reviewed design, not a regression.
7. **INFO: a refused unpack leaves its tree behind.** `unpack_return.py:42-48` extracts into `--out` before `validate_journals` refuses at line 60. A refused, unverified return therefore stays on disk. A4's other refusals behave the same way. Scorers must act only on unpack's success output, or unpack should extract to a sibling directory and rename only after validation.
8. **INFO: carried-over limits, still documented.**
   - The guard misses raw writes that are restored between boundaries, private attributes and non-tensor state.
   - SAM is built eagerly outside inference mode.
   - A hard kill leaves `verified=false`, so the read needs fresh journals.
   - `0.py` does not require `read_cache_bytes`.
   - The `8.py` default of `--gpus 4` fails closed after staging.
