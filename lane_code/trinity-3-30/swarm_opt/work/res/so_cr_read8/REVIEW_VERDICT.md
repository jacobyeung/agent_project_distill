VERDICT: GO AFTER FIXES

## Answer

Not yet as written. The GPU parity kit cannot pass in its current form. Round 7 moved asset staging into the CPU-proof job, which fixes the previous MEDIUM. But it archives with `tar -h`, which turns the symlinks that A4's restore creates into plain copies. The reader's loader then refuses those copies on the H100 host, so every arm fails at model load (finding 1). This fails closed: no passing `ue.json` can be written, so submit refuses. The cost is a fill, a CPU proof of up to 4 h, an archive of about 73 GB (estimate) and one GPU allocation before anyone notices.

Everything else holds:
- The earlier LOW 1–5 and the previous round's LOW 2, LOW 3 and INFO 4 are fixed, each with a regression test that fails before the fix (`checks/round7_before.txt`, 10 failures).
- Points 1–4 hold.
- Once the archive keeps its symlinks and a passing gate exists, the chain from gate to submit is sound for the selected export.

Under the 2026-11-19T15:33Z ruling, the delivered default is step 400 (read A, job 173060). The step-400 default is correct. Rebuilding `a/4.py` from `operations/binding.default.json` gives `be00bdcf…`, byte for byte the source package's fill helper. Step-600 reads need an explicit reviewed binding and an explicit export, and neither is delivered (finding 3).

## Checks

- **Earlier LOW 1–5.**
  - *README commands run as written:* `test_round6.test_f1` still runs the README unpack block, now under `$LOCAL/adopted`.
  - *Pull and fill run detached:* the fill script in `a20.py:207-232` is unchanged. `test_round6.test_f2` passes.
  - *SUBMIT_CHECK strength stated truly:* `cont_ops17/work/o_sub_A4.sh:7-37` appears verbatim in `SUBMIT_CHECK` (checked programmatically). The script parses under the 3.6 grammar and compiles with `/usr/bin/python3` 3.6.8.
  - *Every copied A4 member pinned:* all six `a4_member_pins`, the BATCH.sh pin, the decoded-bootstrap pin, the payload pin and the base `tower_sequence.py` pin match the real A4 base. Every `kit_files`, `operations_files` and `operator_files` pin matches the delivered bytes.
  - *Gate bound to weights and device:* the gate is now bound to the *selected* export, defaulting to step 400 (`a20.py:110-112`). Device admission requires exactly `NVIDIA H100 80GB HBM3`, 132 SMs, capability 9.0 and 79–86 GB (`run.py:106-110`).
- **Previous round's findings.**
  - *Fill wait (LOW 2):* `README.md:89-108` guards `PACKAGE_TOKEN`, refuses a dead PID that left no `1.txt`, and stops at 14,400 s. `test_f2` runs the block itself.
  - *PCIe (LOW 3):* fixed; three PCIe or wrong-SM stubs refuse.
  - *INFO 4:* kit, comparator and sealed-sample hashes go into `ue.json` and are checked in SUBMIT_CHECK (`a20.py:186`). I recomputed the staged sample hash (`1fdb6505…`), and it is deterministic and equals MANIFEST `public_sha256`. `a/1.json` is in the evidence and checked before GPU work (`a20.py:95-101`). Unpack uses `-s -E -B`. The GPU archive path is host-local.
  - *Asset staging (MEDIUM 1):* moved inside the job (`5.py:95-107,185-190`), but see finding 1.
- **(1) OFF stays byte-identical.**
  - I rebuilt patches 01–03 in memory: 37 `/dev/null` file headers, 0 removed lines, and the result equals `EXTENSION_PINS.json` and the workspace `u0/`.
  - The real A4 `src` matches all 927 BASE_PIN hashes (digest `813fe4c5…`), with no `u0/`.
  - Applying 04–05 to the A4 base in memory reproduces all three patched `operator_files` hashes.
  - All new 5.py and unpack code runs only when `read_extensions is True`, and OFF's CPU.json is unchanged (`**extra` is empty).
  - No step-600 literal remains in `a19`, `a20`, `run.py` or `5.py`.
- **(2) Guard.** The guard code is unchanged (patch 01 is byte-identical to round 7). An in-memory probe on torch 2.11.0+cpu gave:
  - *Caught on every call:* `add_` (also under `inference_mode`), `detach().add_`, `copy_`, `_foreach_add_`, `load_state_dict`, `.data` reassignment, `.to(float64)` and a buffer `add_`.
  - *Caught only at the boundary:* `.data.add_` and a NumPy write.
  - *Not caught:* a raw write restored before the boundary (documented).
  - *Refused at install:* a model built in inference mode.
  - *Cost:* 6.9 ms per call at 256 tensors and 40 ms at 1,400.
  - *Torch citations:* they match the installed source: `TensorImpl.h:289-305` (counter sharing; `.data` and `set_data` exceptions), `:392-418` (`bump`, inference tensors), `:2040-2056` (`shallow_copy_from`), `VariableTypeUtils.h:159`, `autograd/graph.py:242-262`, `optim/sgd.py:379`, `cuda/__init__.py:673-695` and `_C/__init__.pyi:12448-12452`.
  - *Failure path:* `ModelMutationError` is a `BaseException`. The only `except BaseException` is the vendor wrapper (`orchard_job.py:203`), which records the failure.
  - *Processor-only switch:* `a19.py:186-191` and `run.py:79-87` are unchanged.
- **(3) Operator path and sharding.** `test_round4.test_f2` drives the real patched `a/5.py` with ON payloads, and its fixture now runs the tar branch (`test_round4.py:245-247`). Patch 04 adds `read_cache_bytes` to the host budget (`tower_sequence.py:101-131`). The NOTE's one-card claim is true: `a19.py:186-187` disables shards and journals, and `tower_sequence.py:82` refuses more than one card.
- **(4) Findings 3, 4 and 7.** `round5_before` still reproduces 11 failures, and the changed round-5 and round-6 tests only add a selectable export and receipts. The round-6 export-pin mutation case is now enforced, not skipped (`test_round6.py:209-213`).
- **(5) Adoption steps.** Patch application, build, operations, place, detached fill, the bounded wait, the CPU proof, the evidence archive, gate preflight, seal, stage-kit, receipt install, submit, fetch and unpack all match the code. The asset archive does not work for the loader (finding 1), and the GPU-host interpreter is undefined (finding 2).

## Findings

1. **MEDIUM: the `tar -h` asset archive breaks the restore's symlink layout, so the GPU gate cannot pass.**
   - A4's restore makes absolute symlinks in `d/e` that point to resolved files in `d/m400`:
     - `d/e/full_weights/<shard>` and `d/e/base/<shard>` point to `d/m400/full_weights/<shard>` (`b/parity_kit/stage_restore.py:73,143-144`).
     - `d/e/heads.pt` points to `d/m400/heads.pt` (`:116,150`).
     - `artifact.json` records `d/e/heads.pt` as the heads path (`:151-153`).
   - The manifest records each file's *resolved* target (`build_manifest.py:24-25`), and the loader's allow-list is built from those targets (`e2e_reader/artifact.py:79-82`).
   - `load_native` refuses any restore input whose `resolve()` is not in that allow-list (`parity.py:126-131`).
   - `5.py:103` runs `tar -chf`, which stores each symlink as a regular copy. `test_round7.py:58` asserts exactly that.
   - After `README.md:226` extracts the archive on the H100 host, `d/e/heads.pt` and every `d/e/base/<shard>` resolve to themselves. `load_native` then raises `restore input missing from artifact`, in the ORIGINAL arm first.
   - No CPU check catches this. The fixture's restore is a stub with no symlinks, and `validate_assets` hashes only RESTORE.json, the binding and the manifest.
   - `-h` also stores the shards twice more and the heads once more. From `a/1.json`, I estimate about 73 GB instead of about 33 GB (32.6 GB of expanded inputs plus about 2 × 18.8 GB of shards plus 2.8 GB of heads). The README gives no size to reserve (`README.md:187`).
   - **Smallest fix:**
     - Drop `-h` (`tar -cf - -C <logical>/d .`). The GPU host restores the exact logical root, so the absolute in-tree links resolve to the same files.
     - Before tarring, refuse any symlink under `d` whose target leaves `<logical>/d`.
     - Add a fixture with `e/heads.pt -> <logical>/d/m400/heads.pt` that runs the real `Artifact` allow-list and the `load_native` `resolve()` check after extraction.
     - State the expected archive size (about 33 GB, estimated).
2. **LOW: the GPU-host interpreter and environment are unspecified and not bound.**
   - `README.md:264` runs `"$READ_PYTHON"`, which is defined only in the Trinity block (`README.md:9,16`), where it points to the CPU environment.
   - Production uses `a/1.json` `python` = `<logical>/d/v/py`, and prepare records the exact versions in `d/ENVIRONMENT.json` (`prepare.py:20-22`).
   - `RUN.json` records the torch, transformers and CUDA versions (`run.py:200-216`), but `ue.json` omits them (`run.py:126-128`) and SUBMIT_CHECK cannot compare them. A gate run in a different environment could therefore authorize submit.
   - The GPU block also sets none of A4's cache variables (`orchard_job.py:140-151`), so the audit's `write_roots` (`parity.py:192`) differ from production.
   - It is unverified whether `d/v/py` runs outside bwrap.
   - **Smallest fix:**
     - On the H100 host, set `READ_PYTHON="$GPU_LOGICAL/d/v/py"`, and preflight its torch, transformers and CUDA versions against `d/ENVIRONMENT.json`.
     - Export `XDG_CACHE_HOME`, `HF_HOME` and `TRITON_CACHE_DIR` under the opaque kit root.
     - Add the versions and `sha(d/ENVIRONMENT.json)` to `ue.json`, and compare them in SUBMIT_CHECK.
3. **LOW: selecting a non-default export (step 600) is not executable as written and is checked late.**
   - `README.md:40,58` says to set `BOUND_EXPORT` to "that target's reviewed export.json". No step-600 export.json exists before that package's own fill writes `a/export.json` (`a20.py:228-229`).
   - The only usable value is the proof's own `EXPORT_PIN.json` (used by `gate_integration7.py`), and with it the selection check compares the package to itself.
   - If `EXPORT_BINDING` and `BOUND_EXPORT` disagree, the first refusal comes at `a20 gate` (`a20.py:110-112`). That is after four 5.4 GB pulls and the CPU proof and archive.
   - **Smallest fix:**
     - Have `a19 build` take `--bound-export` (default step 400) and refuse unless the binding's identity keys and preparation hashes equal the selected export's.
     - State in the README that a target with no prior reviewed export.json uses the proof's `EXPORT_PIN.json`, which adds no independent check.
4. **LOW: the archive-path check compares a resolved path with an unresolved one.**
   - `5.py:119` resolves `--package`, so `gate_assets.path` is a resolved path. `README.md:215` asserts it equals `str(p/'a/4.tar')` with `$P` unresolved.
   - If any component of `/project/community/...` is a symlink on Orchard, staging refuses. This fails closed, and I could not verify it here.
   - **Smallest fix:** compare `os.path.samefile`, or `Path.resolve()` on both sides.
5. **INFO.**
   - *Aliases:* `README.md:232` asks for "opaque aliases of those same files". These must be symlinks: the same `resolve()` membership checks (`parity.py:126-131,172-176`) reject copies.
   - *Lost tar errors:* `5.py:103-104` captures tar's stderr to `PIPE` and drops it. A failed staging job leaves no tar message, so write stderr to `results/4.err`.
   - *Gate job name:* `README.md:195` uses the placeholder `--job-name=ab0123456789`. Every other job uses `a15_cot_ap<token>` (`o_cpu.sh`'s `${P##*/}` and `common.submit_argv`), so use a fresh token in that form.
   - *Carried-over guard limits:* still documented. Raw writes restored between boundaries go undetected, and weights must stay frozen.
