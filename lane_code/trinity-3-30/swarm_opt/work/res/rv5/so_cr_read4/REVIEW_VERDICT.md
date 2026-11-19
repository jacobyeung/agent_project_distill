VERDICT: GO AFTER FIXES

Scope: round-3 delivery in `so_read/out/` (REPORT, NOTE, patches 01–04, MANIFEST, kit_parity50, operator, checks) and source `so_read/work/src/u0`. Path prefixes used below:
- `u0/` = `so_read/work/src/u0/`
- `A4/` = `so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/`
- `R/` = `.../cont_ops16/work/c15/r1route/`
- `T/` = the installed torch at `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/`

Method: I read the code and ran only in-memory, CPU-only probes (`nice -n 10`, 8 threads). I did not run the builder's suites, because they write to `so_read/work/test-artifacts`. For fail-before and pass-after I rely on the recorded outputs in `out/checks/`.

Answer to the question: the reader patches (01–03) and the operator memory patch (04) are safe to adopt once the GPU kit passes. OFF stays byte-identical, and ON answers are gated by the zero-tolerance 50-item comparison. The step-600 production build route that the NOTE prescribes is not executable as written (finding 1). Fix that, or build through cont_ops' own A4 packaging, before step 600.

## The five checks

1. OFF byte-identity holds.
   - Patches 01–03 only add files: 31 `--- /dev/null` files, all under `u0/`. The files I rebuilt from the diffs are byte-equal to `work/src/u0`, and the diff SHA256s match MANIFEST.
   - All 927 base files in `A4/src` match `base_pin`, and the recomputed pin is `813fe4c5…`.
   - Patch 04 applied to A4's bundled `7.py` (equal to `A4/tower_sequence.py`, `97c8e6df…`) reproduces `out/operator/tower_sequence.py` exactly. `out/operator/0.py` equals the bootstrap decoded from `A4/package/BATCH.sh`.
   - The OFF memory receipt is unchanged (`tower_sequence.py:101-118`). Only `operator_sha256` changes, which the NOTE states.
   - `FINAL_INTEGRITY.json` matches every hash it lists.
2. Finding 1 (per-call hashing) is fixed. Calls check identity only; the full hash runs at install (`u0/a0.py:378-384`) and at type entry and exit (`u0/a4.py:173-190`).
   - Per call, `check` (`a0.py:390-392`) and `module_identity(weights=False)` (`a0.py:324-345`) read only id, `data_ptr`, `_version`, dtype, device, shape, stride and the grad flag.
   - The torch citations are correct: `T/include/c10/core/TensorImpl.h:291,296-305,413-418,2050-2054`; `T/optim/sgd.py:378-380` (cited as 379); `T/autograd/graph.py:242`. `T/include/c10/core/InferenceMode.h:37-47` adds that in-place ops on normal tensors inside inference mode still go through `ADInplaceOrView`.
   - The run fails on a mismatch. `ModelMutationError` is a `BaseException` (`a0.py:348`). Neither `a4.main` (`a4.py:492-494`) nor the reader path catches it. The worker exits 1, `a17.py:191-193` records the failure (`round3_before.txt:20,56,64,90,98,106` are the fail-before tests for finding 1), and the job raises (`a16.py:213`) and writes `FAILED.json` (`a16.py:215-216`).
   - The processor-only switch works across settings (`a0.py:28-30`), the builder (`a12.py:145-149`) and preparation (`a18.py:75-78`). The memory proof uses 4 GiB, and no weight guard or journal is installed (`test_read_cache.py:354-358`).
3. Finding 2 (operator path) is partly fixed. The A4 bootstrap admission, `7.py` overlay activation, the `a17` runner, `a13` action-2 dispatch and the nested merge run for real with an ON payload (`test_operator_round3.py:101-152`). They fail before (`operator3_before.txt:5,79`).
   - The memory bound adds `read_cache_bytes` only when ON (`tower_sequence.py:101-118,126-131`).
   - The NOTE's sharding statement is true: `tower_sequence.py:82` refuses more than one card, IDENTITY binds `cards=1`, and `a12.py:150-152` forces scene sharding off on the operator route.
   - The step-600 profile itself is not exercised (findings 1 and 2).
4. Findings 3, 4 and 7 are fixed, and each test fails before.
   - Finding 3: `round3_before.txt:114`. Both base inventories are checked in `kit run.py:47-61`.
   - Finding 4: `lock3_before.txt` has two behavioural failures and `lock3.txt` has two passes; `f16_behavior_before.txt` fails on the real worker.
   - Finding 7: `test_off.py:22` covers a0–a18, and eight subtests fail before (`round3_before.txt:123-186`).
5. The 50-item kit is executable after staging (INFO 9 notes path nits). The NOTE's production build step is not executable as written (finding 1).

## Findings

1. **MEDIUM: the step-600 build command in the NOTE and README produces a package that A4's operations cannot run. It also silently drops the reviewed export binding.**
   - Evidence: NOTE:19 and README:63-69 say to build with `a12.py --enable-extensions --caches-only --operator-bootstrap … --operator-source …`. A4's real package was produced by `R/build_r1.py`, which post-processes a base build. The a12 route skips that step, which has three consequences.
   - (a) The run keys are missing. `a12.py:135-149` writes a `9.json` without `stage1_select_rule`, `perception_memo`, `perception_memo_verify_ids`, `save_own_depth` or `export_binding`. `R/build_r1.py:23` adds them, and `A4/package/0.tgz:9.json` contains them.
     - Action 0 receives `config=cfg` (`a16.py:182`), so `a18.py:59,61` writes `stage1_select_rule='null_argmax'` and `perception_memo='off'`.
     - `tower_sequence.py:25` then raises `unknown_stage1_select_rule`, at CPU-proof time or at action 1. This failure is fail-closed.
   - (b) The export binding check is skipped. Without `export_binding`, `export_pins.admit` skips every reviewed run, step, object and preparation check (`orchard_h10/export_pins.py:64-74`). It is reached from `a16.py:52` and from `A4/unpack_return.py:52`. A step-600 package built this way never checks that it reads the step-600 export.
   - (c) `8.py` is the unported submit helper. `a12.py:133` packages `orchard_h10/operator.py`, but `A4/src/8.py` differs from it:
     - The helper uses `hashlib.file_digest`, which needs Python 3.11 or later (`A4/src/orchard_h10/operator.py:14-15`). It also uses `capture_output` (`:81`).
     - The helper requires the package at `/project/community/jjyeung/<token>` (`:42`). A4's `0.py:24` and `a16.py:160` read `okh7/a15_cot_ap<token>`.
     - A4 runs `3.py check/submit` with `/usr/bin/python3` (`R/make_operations.py:86,135`), which is Python 3.6 (`R/build_r1.py:13`, `R/test_py36_guard.py`). `R/build_r1.py:24-30` patches exactly these lines.
   - Smallest fix, in two parts.
     - Give a12's operator route a required `--base-package` (A4 `0.tgz`) and `--export-binding` (the step-600 binding JSON). Copy A4's `8.py` bytes and the five run keys into `9.json`, and refuse `--operator-source` without an `export_binding`.
     - Alternatively, state in the NOTE that step 600 is built by cont_ops' `build_r1`-style post-processing over the a12 payload, with a new step-600 binding. Run that pipeline once on CPU, and place the patched `tower_sequence.py` where `unpack_return.py:54` hashes it.

2. **LOW: the operator CPU test hides finding 1 and does not run the adoption profile.**
   - Evidence: the action configs are built by hand, with the A4 keys injected (`test_operator_round3.py:213-216`), and `job.main` is replaced (`:120-122,129`). So `a16`'s real config construction never runs.
   - The CPU proof's memory comes straight from `memory_bound()` (`:223-227`), not from the `7.py` rehearsal with `measure_memory`.
   - Only the generic ON payload (atomic journal and merge) runs through actions 0 and 1. The `--caches-only` package, which the NOTE adopts, is only built and inspected (`:236-245`).
   - Smallest fix: build the `--caches-only` operator package, take `9.json` as-is, and let `a16` write `a/0.json` and `a/1.json` (stub storage and namespace only). Then run actions 0 and 1 and produce `MEMORY.json` through the rehearsal path. Assert that `read_cache_bytes` appears in the proof memory and that the ordinary journals carry `WEIGHTS.json` set to `verified=true`.

3. **LOW: the cache-only return path never checks `WEIGHTS.json`.**
   - Evidence: only resume (`a4.py:289-291`), merge (`a6.py:49`) and the comparator (`a10.py:76-80`) refuse an unverified journal. In cache-only mode there is no merge, and the return goes through `A4/unpack_return.py:6-19,52-56`, which never reads `WEIGHTS.json`.
   - A failed ON run writes `FAILED.json` and still publishes a partial return (`a16.py:213-217` and the `finally` that follows). Its rows computed after an untracked persistent write are unpacked like any other partial return.
   - Smallest fix: have `a17` record each type's `WEIGHTS.json` state in `SUMMARY.json` and mark the read failed if any is false. Alternatively, have the unpacker refuse a segment whose `WEIGHTS.json` exists with a value other than true.

4. **INFO: the per-call guard catches every tracked mutation; untracked writes are caught only at type boundaries, and only if they persist.** I confirmed this with in-memory probes on the installed torch 2.11.0+cpu.
   - The counter increments for: an in-place op on the parameter, including inside `inference_mode`; `_foreach_add_`; `detach()` followed by an in-place op; `load_state_dict`.
   - The counter does not increment for: `.data` followed by an in-place op; `untyped_storage().copy_`; NumPy writes.
   - The pointer guard catches `.to(dtype)`, `vector_to_parameters` and `.data` reassignment.
   - A module built inside `inference_mode` has parameters without a counter, which `a0.py:381-382` refuses.
   - A raw write restored before the next boundary goes undetected, which the REPORT states.
   - Two smaller gaps: tensor attributes whose names start with `_` are not covered (`a0.py:335`), and the guards do not cover the SAM3 or Qwen modules' non-tensor state. The reader itself performs none of these writes, because its models are evaluated frozen.

5. **INFO: per-call cost scales with the number of tensors and modules, not with weight bytes.**
   - The guard's `check` plus `module_identity` measured 21 ms for 256 tensors and 129 modules, 145 ms for 1,400 and 701, and 319 ms for 3,000 and 1,501 (CPU, this node).
   - The stub (`work/benchmark_round3.py`) has 256 tensors, far fewer than SAM3 probably has. Expect about 0.1–0.3 s per SAM detect. Over about 176 detects that is under a minute per run, which is cheap.
   - The comparator's per-item seconds (`a10.py:141-147`) exclude install and boundary hashing and the eager SAM load. Judge net savings from `RUN.json` `worker_wall_seconds` (`kit run.py:128`).

6. **INFO: ON builds SAM differently from OFF.**
   - ON loads SAM at factory time, outside inference mode (`u0/a3.py:191-192`), so its parameters are normal tensors.
   - OFF loads SAM lazily inside `encode`, which is decorated with `@torch.inference_mode()` (`A4/src/tree/student_pilot/sam3_tower.py:195-202`), so its parameters are inference tensors.
   - The guard needs ON's way. It also moves when SAM is constructed, with whatever RNG use that entails, and loads SAM even for types that never call it. Only the GPU byte gate can clear this.

7. **INFO: the sample overstates SAM reuse.**
   - In the fixed sample, all ten distance items use one clip.
   - A4 has 150 distance items on 60 clips. Clip reuse is still real: 90 of 149 adjacent distance pairs share a clip, and an LRU over 32 clips gives 377 of 636 hits across all types.
   - Hits and savings on the sample therefore do not predict the step-600 run.

8. **INFO: preemption.**
   - A4 submits to `--partition=preempt` (`R/make_operations.py:109`).
   - Under ON, a hard worker death while the job survives leaves `WEIGHTS.json` false, and a resume into that output fails (`a4.py:289-291`). OFF would resume.
   - Graceful SIGTERM and deadline stops verify and resume. The NOTE says this ("Require real persistent-storage requeue before any preempt…"). The step-600 plan should say which partition it uses.

9. **INFO: kit README nits.**
   - The commands call `work/cpu.sh` and `work/src`, which live in the so_read workspace, not in the delivery (README:11,13,35,86).
   - README:3 says the patches apply to "A4/src or B5/src", but the kit's base pin covers A4 only, so a B5 root fails `validate_roots` (fail-closed).
   - `0.py` does not require `read_cache_bytes` in an ON proof. The proof is still bound to the ON payload and plan.
