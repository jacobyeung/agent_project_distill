VERDICT: GO AFTER FIXES

## Answer

Not yet as written. The GPU parity gate cannot start on the H100 host (finding 1).
- `READ_PYTHON="$GPU_LOGICAL/d/v/py"` is a 160-byte wrapper. The interpreter it launches exists only inside A4's bwrap namespace, but README runs it outside bwrap.
- The preflight fails closed, so no passing `ue.json` can be written and submit refuses.
- The cost is a fill, a CPU proof of up to 4 h, a 33 GB archive (estimate), and an H100 allocation that is already held before anyone notices.

Correction to the eighth review: its LOW 2 fix ("run `d/v/py` on the host") rested on a premise that review left unverified ("unverified whether `d/v/py` runs outside bwrap"). The evidence below shows it does not run outside bwrap. Round 8 implemented that decision faithfully.

Everything else holds. All five round-8 findings are fixed as `PROMPT_so_read_fix8.md` decides, each with a test that fails before the fix (`checks/round8_before.txt`: 29 failures across 10 tests). Points 1–4 hold.

Once the gate runs inside A4's namespace and passes, cont_ops can adopt patches 01–05 for step-400 reads.

## Checks

- **Earlier LOW 1–5.**
  - *README commands run as written:*
    - The unpack block (`test_round6.test_f1`), the fill wait (`test_round7`), and the PYASSET and GPU_ENVIRONMENT blocks (`test_round8`) are executed from the README text.
    - The GPU_ENVIRONMENT test, however, replaces `d/v/py` with a test double (`test_round8.py:130-133`), which hides finding 1.
  - *Pull and fill run detached:* the fill, cpu, submit and fetch scripts in `a20.py` are unchanged from round 7.
  - *SUBMIT_CHECK strength stated truly:*
    - `cont_ops17/work/o_sub_A4.sh:7-37` appears verbatim in SUBMIT_CHECK.
    - SUBMIT_CHECK, GATE_ARCHIVE and the PYASSET heredoc compile under `/usr/bin/python3` 3.6.8.
    - The environment comparison README states (`README.md:144,167`) matches `a20.py:192-196`.
  - *Every copied A4 member pinned:* these all match the real A4 base and the delivered bytes:
    - all six `a4_member_pins`, BATCH.sh, the bootstrap (`0.py` = A4's decoded bootstrap, `76036ed9…`) and the payload pin;
    - the 13 `kit_files` and 5 `operations_files`;
    - the three operator pins.
  - *Gate bound to step 400 only, and to the production device:*
    - `a19.py:154-155` refuses any binding that differs from `FIXED_BINDING` before reading the base. `test_round8.test_f3` covers 11 binding mutations.
    - `a20.py:109` requires `DEFAULT_BOUND_EXPORT`, which byte-matches A10b's `a/export.json` (1,739 B, `3ecf3483…`) and the production `EXPORT_PIN.json`.
    - The A10b archive is 21,583,032,320 B with sha `dcd49569…`, which matches `FIXED_BINDING`.
    - Device admission (`run.py:117`) requires NVIDIA H100 80GB HBM3, 132 SMs, capability 9.0 and 79–86 GB.
- **Round-8 findings.**
  - *MEDIUM 1 (archive):* fixed.
    - `5.py:95-108` archives without `-h`. It refuses escaping, dangling and cyclic links, and runs inside the namespace (`5.py:118-119`).
    - A4's real `d` contains only the restore's in-tree absolute links (`b/parity_kit/stage_restore.py:143-150`), so the check passes there.
    - `test_round8.test_f1` runs the real `Artifact.verify` and `load_native` on an extracted absolute heads link.
    - README:169 gives about 33 GB. My sum of the expanded inputs in `a/1.json` is 32.6 GB, which agrees.
  - *LOW 2 (interpreter and environment):* the environment receipts are bound, but the interpreter itself is not usable (finding 1).
    - The ENVIRONMENT.json sha goes into READY (`a18`).
    - The gate checks it (`a20.py:111-117`); SUBMIT_CHECK checks it (`a20.py:192-196`); the kit parent, workers and receipt writer check it (`run.py:104-114`).
    - Cache roots are set (`README.md:253`).
  - *LOW 3 (step 400 only):* fixed, refused at build time (see above). No step-600 or other-target text remains in the NOTE, README, `run.py`, operations or operator files.
  - *LOW 4:* fixed. `README.md:197` resolves both paths.
  - *INFO 5:* fixed.
    - The aliases are symlinks (`README.md:212-214`).
    - tar's stderr goes to `results/4.err` (`5.py:118`).
    - The job name is `a15_cot_ap` plus `token_hex(6)` (`README.md:175-178`).
- **(1) OFF stays byte-identical.**
  - The A4 `src` matches all 927 BASE_PIN hashes (digest `813fe4c5…`) and contains no `u0/`.
  - Patches 01–03 contain 38 `/dev/null` headers and 0 removed lines. The rebuilt files equal `EXTENSION_PINS` and the workspace `u0/`.
  - Applying patches 04–05 to the base reproduces the operator pins.
  - In round 8, only `package/a/5.py` changed among the operator files, and its new code runs only when `read_extensions is True`.
  - `checks/OFF_BYTES.json` passes.
- **(2) Guard.** I ran an in-memory probe on the installed torch 2.11.0+cpu.
  - *Caught by `check()` on every call:* `add_` (also under no_grad and inference_mode), `detach().add_`, `copy_`, `load_state_dict`, `.data` reassignment, `.to(float64)` and a `requires_grad` flip.
  - *Caught only at the boundary:* `.data.add_` and a NumPy write.
  - *Refused at install:* a model built in inference mode.
  - *Cost:* 7.09 ms per call at 256 tensors and 43.56 ms at 1,400.
  - *Torch citations:* `TensorImpl.h:291,303,392,413,2051`, `VariableTypeUtils.h:159`, `graph.py:242` and `sgd.py:379` match the installed source.
  - *Failure path:* `ModelMutationError` is a BaseException. The only `except BaseException` is `orchard_job.py:203`. The reader child's non-zero exit raises a RuntimeError, so the run fails.
  - *Processor-only switch:* `a19.py:192-197` and `run.py:79-87` are correct.
- **(3) Operator path and sharding.**
  - `test_round4.test_f2_bound_real_job_and_rehearsal_memory` drives the real `5.py`, `0.py` and `7.py` with ON payloads and asserts the 12 GiB cache allowance. Its fixture runs GATE_ARCHIVE.
  - `tower_sequence.py` is unchanged from round 7: it counts `read_cache_bytes` and refuses more than one card. `a19` disables shards and journals. The NOTE's one-card claim is true.
- **(4) Findings 3, 4 and 7.** The before-fix controls reproduce for every round (`checks/run_checks8.txt`). The round 3–7 test edits only adapt fixtures to step 400 and to the environment field.
- **Test counts.** 129 workspace tests pass. 48 fresh-application tests pass: the seven `applied_*` logs from this round sum to 48.
- **(5) Adoption steps.** Patch application, build, operations, place, detached fill, the bounded wait, the CPU proof with archive, PYASSET extraction, gate, seal, stage-kit, receipt install, submit, fetch and unpack all match the code. The exceptions are finding 1 and finding 3.

## Findings

1. **MEDIUM: the GPU-host interpreter runs only inside A4's namespace, so the gate cannot start as written.**
   - Step 400's pinned environment (`a/1.json` `env`, sha `e46a9a59…`, identical in A4 and A10b) records:
     - `python`: `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904/e/bin/python`
     - torch 2.13.0+cu130 and transformers 5.19.0
   - The A4 worker log loads transformers from that `/lustre/.../19252904/e` tree.
   - That interpreter links to `/home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12` (`vendor/orchard_stage.py:22-23`).
   - Both paths exist only through namespace binds from the job-private runtime groups: `vendor/orchard_job.py:129-131` binds `root/m/ap` and `root/sj/uv-python/...`, staged at `job.py:110-117`.
   - `4.tar` holds only `logical/d`. Its `v/` contains just `py` (160 B), `boot.py` and the `site/` overlay.
   - `README.md:252,258,270` therefore run `d/v/py` on the bare host, and `README.md:275` ("runs the archived production interpreter outside bwrap") is false.
   - The workers also bypass the wrapper. `run.py:271,277,284` relaunch with `sys.executable`, while A4's own runner uses the wrapper (`runner.py:34`, `config['python']`).
     - The `v/site` overlay supplies scipy 1.14.1, timm, iopath, pycocotools and ftfy.
     - Whether workers lose the overlay depends on the `v/py` and `boot.py` bytes, which I could not inspect.
   - **Smallest fix:**
     - On the H100 host, stage A4's runtime groups and bwrap into a host-local root with A4's own `job.stage` code.
     - Extract `4.tar` to `root/sj/<logical>/d`.
     - Run the preflight and `u0.py` as `J.namespace(root) + [inputs['python'], …]` with `J.environment(root)` plus the cache variables.
     - Spawn workers through the same `inputs['python']`.
     - Replace the test double with a test that runs the real wrapper layout, or at least asserts that the gate command is wrapped in the namespace.
2. **LOW: the guard and framework evidence cover a different torch and transformers than the production reader.**
   - `FRAMEWORK_EVIDENCE.md` and the CPU checks use torch 2.11 and transformers 5.12.1 (`checks/RESULTS.json`).
   - The production reader runs torch 2.13.0+cu130 and transformers 5.19.0 (finding 1).
   - The byte-parity gate covers output parity, but not the guard's per-call detection, which depends on `_version` behaviour.
   - **Smallest fix:**
     - State the version gap in FRAMEWORK_EVIDENCE.
     - Add a short in-gate guard self-test on the production interpreter that mutates a scratch module with `add_`, `copy_` and `load_state_dict` and requires each to raise, or cite the 2.13 source.
3. **LOW: the H100 allocation sits idle while the Trinity-side steps and the transfer run.**
   - `salloc` comes first (`README.md:176`), but the gate, seal and stage-kit (`README.md:219-241`) and the kit transfer come after it. None of those depends on the allocation.
   - Staging the kit and the two 927-file source roots onto the host has no commands, only prose (`README.md:181,243`).
   - The five-hour limit has to absorb that time.
   - **Smallest fix:** run the gate, seal, stage-kit and transfer before `salloc`, and give the commands that extract the kit and sources.
4. **INFO.**
   - *Literal kit root:* `GPU_KIT=/scratch/jjyeung/ab0123456789` is used as a literal (`README.md:251,270-272`, `config.example.json`). Two gates would collide, so derive it from a fresh token.
   - *Environment differences from A4:* A4's environment also sets `HOME`, `TMPDIR` and `OPENBLAS_NUM_THREADS=1` (`orchard_job.py:140-151`). README sets 8 threads and no HOME or TMPDIR. Running inside `J.environment` (finding 1) removes the difference.
   - *Stale logs:* eight `checks/applied_*.txt` logs from round 7 (07:31–07:32) sit beside this round's. Label them or move them.
   - *Carried-over guard limits:* still documented. Raw writes restored between boundaries go undetected, and weights must stay frozen.
