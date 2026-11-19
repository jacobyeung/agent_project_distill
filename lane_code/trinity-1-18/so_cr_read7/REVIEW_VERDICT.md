VERDICT: GO AFTER FIXES

## Answer

Yes, once the GPU gate can actually be staged. Previous LOW 1–5 are fixed in code, each with a regression that failed before for the expected reason (`checks/round6_before.txt`, 31 failures). Points 1–4 hold. If an H100 gate passes, the chain that binds it to the step-600 weights, the plan, the profile and the device holds through submit. Point 5 fails at one step: the README tells the owner to stage GPU assets from the CPU proof's root after the CPU job has finished. A4 keeps that root on the job-private `/tmp`, and it disappears with the job (finding 1). The failure is closed, because no gate can mean no submit, but the gate cannot be run as written. Findings 2–3 are LOW and finding 4 is INFO.

## Checks

- **Previous LOW 1, unpack.** README:138-141 now runs `-s -B ./unpack_return.py` from `$LOCAL/step600`. `test_round6.test_f1` runs that README block as a subprocess on an authenticated fixture return, and it exits 0. Before the fix it failed with `ModuleNotFoundError: fetch_return`.
- **Previous LOW 2, detached fill.** `a20.py:191-219`: `mkdir 0.lock` is a permanent attempt lock, `nohup bash "$0" --worker </dev/null >0.log 2>&1 &` detaches the worker, its PID goes to `0.txt`, and the EXIT trap writes the exit code to `1.txt`. The whole pull, fill, `dryres2`, `3.py check` and `dry2` sequence runs in the worker. `test_f2` runs the real launcher, lock and trap: rc 0 and rc 17 both land in `1.txt`, and a second launch refuses.
- **Previous LOW 3, SUBMIT_CHECK.** `a20.py:118-148` equals `cont_ops17/work/o_sub_A4.sh:7-37` byte for byte (checked programmatically). It parses under the Python 3.6 grammar and compiles with `/usr/bin/python3` 3.6.8. The README (127) and NOTE now say "verbatim", which is true. `test_f3` refuses each mutated batch, guard, events, argv and memory field, a changed MEMORY.json, and a resealed stale BATCH.sh.
- **Previous LOW 4, member pins.** `a19.py:115-128` authenticates BATCH.sh, the decoded bootstrap, the six copied members and the three patched operator files before any output. I compared every MANIFEST `a4_member_pins` entry, `batch_sha256` and `decoded_bootstrap_sha256` with the real A4 base (`cont_ops16/.../out3/A4`), and all match. Applying patches 04–05 in memory to that base reproduces all three `operator_files` after-hashes.
- **Previous LOW 5, binding.**
  - `a20 gate` requires sha(RESTORE.json) and sha(binding.json) to equal CPU READY, and the staged export identity to equal the package's step-≥600 binding (`a20.py:86-99`).
  - Workers recheck the asset hashes and the manifest hash (`run.py:90-101,138`), and the original loader then hashes every pinned component (`b/e2e_reader/artifact.py:102-114`, `parity.py:189-196`).
  - The submit check ties `ue.json` to the plan, profile, READY pins and `h(a/export.json)` (`a20.py:166-171`).
  - The export pin is consistent across the chain. `d/6.json` is written by `common.write` (`prepare.py:37`) and `a/export.json` by the fill helper's `write` (`a/4.py:19-20,205`). Both use `sort_keys=True, indent=2` plus a newline, so the bytes match.
- **(1) OFF.** Patches 01–03 contain 36 `--- /dev/null` headers and no removed lines. Rebuilding the 36 files from the diffs equals `EXTENSION_PINS.json` and the workspace `u0/`. The real A4 `src` matches all 927 BASE_PIN hashes, and the pin digest is `813fe4c5…`. The 12 extra `__pycache__` files are ignored by `validate_roots`. Patch 05's new 5.py code runs only when `read_extensions is True`. The patch hashes match MANIFEST.
- **(2) Finding 1, the guard.** The guard code is unchanged since round 6 (only `a19`, `a20` and the tests differ). I reran an in-memory probe on torch 2.11.0+cpu:
  - Caught per call: `add_` (also under `inference_mode`), `detach().add_`, `_foreach_add_`, `copy_`, `load_state_dict`, `.data` reassignment, `.to(float64)` and a buffer `add_`.
  - Caught only at the boundary: `.data.add_` and a numpy write.
  - Not caught: a write restored before the boundary, which is documented.
  - At install: a model built in inference mode is refused.
  - Cost is 11 ms per call at 256 tensors and 56 ms at 1,400 tensors on a loaded node.
  - The cited torch source matches: `TensorImpl.h:288-305,385-418,2044-2056`, `autograd/graph.py:242-262`, `optim/sgd.py:372-380`, `VariableTypeUtils.h:159` and `cuda/__init__.py:641-695`.
  - `ModelMutationError` is a `BaseException`. The only `except BaseException` in the tree is the vendor chain wrapper, which records the failure.
  - The processor-only switch is unchanged (`a19.py:183-188`, `run.py:79-87`).
- **(3) Finding 2, operator path and sharding.** `test_round4.test_f2` still drives the real `a/5.py`, `0.py` and `7.py` path with ON payloads and passes. Patch 04 is unchanged: ON adds `read_cache_bytes` to the host budget. The sharding claim is true: `a19.py:184` disables shards and journals, and `tower_sequence.py:82` refuses more than one card.
- **(4) Findings 3, 4 and 7.** `round5_before` still fails 11 assertions. Finding 7's test now runs the command itself instead of matching README text.
- **(5) Adoption steps.** Patch application, binding, build, operations, place, detached fill, CPU proof, evidence archive, gate preflight, seal, stage-kit, receipt install, submit, fetch and unpack all line up with the code. The asset-staging step does not (finding 1), and the fill wait can hang (finding 2).

## Findings

1. **MEDIUM: GPU-gate asset staging cannot run as written.**
   - The staging heredoc (`README.md:152-168`) reads `$P/a/c/CPU.json`, takes `root`, and tars `logical/d` through `J.namespace(root)`. It is to run "on the CPU proof's compute node … while that directory remains available", after "Wait for the CPU job to finish successfully" (`README.md:84`).
   - A4 creates `root` with `mkdtemp(dir='/tmp')` and refuses to continue unless `/tmp` is the job-private mount (`a/5.py:114,128`; `orchard_job.py:81-86` requires `job_tmp` and the job ID in `mount_root`).
   - CPU.json is the job's last write before exit (`a/5.py:160-163`; the job is `--wrap="exec … 5.py"`, `a20.py:228`). Outside that job, `/tmp/a<job>…` is the node's own `/tmp`, and the job's private `/tmp` normally goes away at job end. The bwrap binary, the staged export, the frames, the environment and the manifest inputs are therefore unreachable at the moment the command can first run.
   - Unverified precondition: run.py runs outside A4's bwrap namespace, so the logical root `/scratch/jjyeung/b01ec87a6f29b` must physically exist and be writable on the H100 host. A4 itself creates `/scratch` only inside bwrap (`orchard_job.py:127-128`). The README also gives no allocation command for the gate job.
   - Fails closed: without a gate there is no `a/g.json`, so submit refuses.
   - Smallest fix: produce the asset archive inside a job. One option is patched `a/5.py`'s `read_extensions` branch: tar `logical/d` through `J.namespace(root)` to an owner-approved path before writing CPU.json, and record its sha256 in CPU.json. The other is an `o_stage.sh` CPU job that reruns A4 stage and prepare for the same package and inputs, tars `d/`, and refuses unless its READY equals CPU.json's READY. Add a fixture test that runs the staging step. Also state the H100-host path requirement.
2. **LOW: the Orchard fill-wait loop can spin forever.**
   - `README.md:75-77` sets `P=…a15_cot_ap${PACKAGE_TOKEN}` with no `:?` guard, in a block whose other inputs are guarded (`OPS_ARCHIVE`, `OPS_SHA256`, `D`). `PACKAGE_TOKEN` was set on Trinity (`README.md:51`). If it is unset on Orchard, `while test ! -f "$P/a/1.txt"` polls a nonexistent path indefinitely.
   - A SIGKILLed worker also leaves no `1.txt`, and the loop never checks the PID in `0.txt`.
   - Smallest fix: add `: "${PACKAGE_TOKEN:?…}"`, or read `P` from `$D/o_place.sh`. Bound the wait, or fail when the PID in `0.txt` is gone and `1.txt` is still missing.
3. **LOW: the device check is broader than production admission.**
   - `run.py:104-109` accepts any name starting with `NVIDIA H100`, capability 9.0 and 79–86 GB. That includes an H100 PCIe 80 GB (114 SMs).
   - Production admission requires exactly `NVIDIA H100 80GB HBM3` (`orchard_job.py:103`). Byte equality is a per-device property, so a PCIe gate does not certify the SXM read. The REPORT says the check refuses a "different GPU family".
   - Smallest fix: require `prop.name == 'NVIDIA H100 80GB HBM3'` (optionally `multi_processor_count == 132`), and add a PCIe stub to `test_f5_production_device_is_required`.
4. **INFO.**
   - `ue.json` binds the plan, profile, assets and device type, but not the kit, comparator or sample bytes (`run.py:112-116`). RUN.json records `kit_source_sha256`, but submit never sees it. A modified staged kit could therefore emit `passed=true`. One fix is to add the kit, comparator and sample hashes to `ue.json` and compare them in SUBMIT_CHECK against MANIFEST `kit_files`.
   - `a20 gate` checks only the identity fields of EXPORT_PIN.json, and `test_round6.py:196` skips its byte mutation. A byte mismatch with `a/export.json` surfaces only at submit, after the GPU spend. Adding `a/1.json` to the evidence archive and comparing it with its `export_pin.sha256` would catch it at the gate.
   - The unpack command honors `PYTHONPATH` and `PYTHONHOME` because it drops `-I`. Using `-s -E -B` keeps the sibling import and ignores the environment.
   - `README.md:227` writes `"$LOCAL/5.tar"` on the GPU host, where `LOCAL` is a Trinity-side variable.
   - Carried-over guard limits remain documented: raw writes restored between boundaries go undetected, and frozen weights are required.
