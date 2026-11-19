VERDICT: GO AFTER FIXES

**Adoption answer.** Not yet, as delivered. The patches themselves are safe to adopt. OFF stays byte-identical, every pin matches, and the weight guard catches every mutation the reader can see. But the step-400 H100 parity kit cannot pass as written. Its preflight relies on an unproven call form of the wrapper (finding 1), and nothing creates the opaque aliases that the sealed settings point at (finding 2). Fix both, run the 50-item gate on the H100, and adopt once the gate reports zero answer/trace byte differences. Findings 3 and 4 do not block adoption.

## Findings

1. **MEDIUM. The preflight calls `d/v/py` with `-c`, a call form no A4 path uses.**
   - Evidence: `out/kit_parity50/host.py:16-27,148` runs `J.namespace(root)+[inputs['python'],'-B','-I','-c',PREFLIGHT,config]`. A4 always passes a script path: `orchard_h10/job.py:185,207` and `runner.py:34` call `v/py -B -I <script> <json>`. A4's CPU proof ran `6.py` that way, `__main__` guard included.
   - Why `-c` probably fails: the pinned `v/py` is 160 B. That exactly fits `#!/bin/sh\nexec <ap>/19252904/e/bin/python -I -S <logical>/d/v/boot.py "$@"` (I computed the lengths). `boot.py` is 443 B (`r228_lists/a4.tar.list`). So `-B -I -c CODE` most likely lands in `boot.py`'s argv, and nothing shows that `boot.py` handles `-c`. This is an inference from byte counts; I have not read the wrapper itself.
   - Consequence: if `-c` is unsupported, the gate stops inside the allocation, after staging about 43 GB. It fails closed, so there is no wrong result.
   - The documentation and tests overstate it. `README.md:286` says the preflight uses "A4's `-B -I` wrapper calling convention". `test_round9` only asserts the shape of the argv, with `subprocess` mocked.
   - Smallest fix: ship PREFLIGHT as a pinned kit file (for example `u0/u5.py`, added to `kit_files` and `validate_kit`) and call `[inputs['python'],'-B','-I',kit+'/u0/u5.py',config]`. Alternatively, drop the preflight and move the `torch.cuda.is_available()` check into `u0.py` main, after `validate_environment`.

2. **MEDIUM. The prepared paths that are not opaque have no aliases on the H100 host, so the gate is not executable as written.**
   - Evidence: `a9.seal_settings`/`validate_paths` require every absolute settings path to be opaque. PRIVATE_ALIASES therefore has to remap `p/tree`, `d/p0/config.json`, `d/k/sam3.pt`, `d/k/SAM3_RECEIPT.json` and `d/v/site` (`work/src/u0/a18.py:57-60`). `README.md:213` says "map other prepared asset paths to existing opaque symlinks", but no step creates them. `host.py:132-133` creates only `d/7.json` and `d/9.json`, and `4.tgz` carries only `u0 u3 0 1.tar 2.tar` (`README.md:205`).
   - Consequence: workers would fail on missing source, config or SAM3 paths, or the env-root allow-list audit would reject `d/v/site` imports.
   - Smallest fix: fix the alias names (opaque, under `logical/d`) in one list. Use that list both in the README's PRIVATE_ALIASES example and in `host.stage`, which should `symlink_to` them as at lines 132-133. Have `u0.py` check that every absolute path in the sealed settings exists before the self-test. Add a test that stages the fixture and resolves every sealed path.

3. **LOW. Workers run in a nested bwrap.**
   - Evidence: `out/kit_parity50/run.py:145-148` wraps each worker in a second `J.namespace` from inside the parent's namespace. A4's runner starts workers directly inside the namespace (`runner.py:34`). swarm_opt decided against nesting for the sibling lane (`so_reads228_fix3.md:7`).
   - What is known: the paths do resolve, because argv[0] is `root/bwrap` under the bound `/tmp` (`orchard_job.py:120,127`). A nested bubblewrap 0.4.0 probe also succeeded on this Trinity node. Orchard's pinned bwrap and kernel remain unproven.
   - Smallest fix: when `U0_ROOT` is set (that is, already inside the namespace), have `worker_command` return `[inputs['python'],'-B','-I']+args`, keeping `J.environment`.

4. **INFO.**
   - About 33 GB of `4.tar` is read three times inside the allocation: the PYASSET hash (`README.md:240-253`), `host.py:96` and the extraction at `host.py:129`. Hash it once, during extraction.
   - `host.py` does not apply A4's `opaque()`/`install_process_guard` screen to its own argv. A probe found no FORBIDDEN hits in PREFLIGHT or the worker argv today.
   - A worker failure exits through `SystemExit(rc)` with no `ue.json`, so `5.tar` is skipped. It fails closed but leaves no failure receipt.
   - The real namespace, the `v/py` wrapper, the H100 and torch 2.13/transformers 5.19 remain unrun. Every round-9 namespace test mocks `subprocess`.

## Previous LOW 1-5

- **README commands run as written:** partly. The Trinity block now precedes `salloc` (`README.md:174-208` before 225), and `test_f3` executes the extraction block. Findings 1 and 2 still block a full run.
- **Pull and fill run detached:** unchanged and OK.
- **SUBMIT_CHECK strength stated truly:** OK. It now also requires all three self-test detections (`a20.py:186-187`), and the tests reject each miss.
- **Every copied A4 member pinned:** OK. The 6 members, the payload, 4 operator files, 15 kit files and 5 operations files all match MANIFEST. `RUNTIME_PINS.json` equals the payload's own `ORCHARD_ASSETS.json`: 3 groups, 13 parts, 10,497,433,600 B, plus bwrap.
- **GPU gate bound to the step-400 export only and to the production device:** OK. `BOUND_EXPORT.json` is byte-identical to A10b `a/export.json` (3ecf3483). `run.py:117-123` checks the device, and `config.example.json` names H100_80GB.

## Questions 1-5

1. **OFF byte-identical: OK.** The patches add 40 files and remove 0 lines. The 927 base files (excluding 12 `.pyc` caches) match BASE_PIN digest 813fe4c5.
2. **Finding 1, per-call identity: OK.**
   - Cost: the per-call stamp costs 3.21 ms at 128 tensors and 18.48 ms at 700.
   - Coverage: it catches in-place ops through `_version`. The cited Version Counter Sharing note matches the installed torch 2.11 `TensorImpl.h`. Writes through `.data` or NumPy are caught only at the boundary hash, as `FRAMEWORK_EVIDENCE.md:51-59` states.
   - A mismatch raises `ModelMutationError`, a `BaseException`, which fails the run.
   - The processor-only profile ([0], 4 GiB) validates (`run.py:65-87`).
3. **Finding 2, A4 operator path: OK.** `0.py`/`7.py` are unchanged, and the ON-payload operator test passes. The memory bound counts the read cache: 12 GiB with all caches, 4 GiB processor-only. The NOTE's statement that no multi-card A4 operator is delivered is true.
4. **Findings 3, 4 and 7: OK.** The before-controls reproduce the failures, and the after runs pass (`run_checks9.txt`).
5. **Adoption steps and the 50-item GPU gate: not executable as written** (findings 1 and 2). The step order is correct. The ON payload stays under A4's 32 MiB extraction cap: A4's payload expands to 23.5 MiB, plus 0.56 MB of `u0`.

## Ninth-review findings

- **Gate and workers in A4's namespace through `inputs['python']`:** fixed, apart from findings 1 and 3. The `stage_runtime` block equals A4's, and the data extracts to `root/sj/<logical>/d`.
- **Every runtime group pinned or listed as a prerequisite:** fixed.
- **A test that would have caught the `d/v/py` double:** replaced at the minimum level the prompt allows (an argv-shape assertion). It cannot catch finding 1.
- **In-gate guard self-test on the production interpreter:** fixed. It runs before any worker (`run.py:157-185,322-328`), receipts refuse a missing result, and SUBMIT_CHECK enforces it.
- **Trinity steps before salloc:** fixed.
- **Fresh kit token, `J.environment` (HOME/TMPDIR/OPENBLAS=1) and moved round-7 logs:** fixed.
