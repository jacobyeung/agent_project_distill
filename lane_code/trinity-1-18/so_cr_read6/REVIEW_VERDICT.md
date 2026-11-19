VERDICT: GO AFTER FIXES

## Answer

Yes. cont_ops can adopt the patches for the step-600 reads after one small fix (finding 1) and a passing GPU parity gate. Previous MEDIUM 1 is closed: the step-600 BATCH.sh carries cont_ops' wrapper and passes the real bundle guard. Previous LOW 2 is mostly closed; a residual is finding 4. Points 1–4 hold. Point 5 fails as written, because the README's unpack command cannot import its own helper (finding 1). Findings 2–5 are LOW hardening items, and none blocks adoption once finding 1 is fixed.

## Checks

- **Wrapper and bundle guard.** `a19.py:19-32` `wrap_batch` is verbatim from `cont_ops17/work/build_r10.py:72-84`, and `a19.py:212` applies it. It adds the exclude line, the EXIT trap to `$P/a/x<job>` and USR1 forwarding. The built fixture's BATCH.sh passes the real `a/5.py` `check_bundle_guard` (`test_round5.test_f1`). An in-memory bash probe of the wrapped text confirmed the heredoc reaches the background Python, USR1 is forwarded (rc 7) and the exit code propagates (rc 5).
- **a19 pins.** `a19.py:100-128` refuses on any of these mismatches, before any output:
  - the reviewed payload `4498fca7…`;
  - MANIFEST `a4_payload_pin`;
  - the three operator files against `operator_files`;
  - the 35-file u0 inventory against `EXTENSION_PINS`, which must equal the MANIFEST after-hashes;
  - the four alias bases against `base_pin.inventory`.

  `test_round5.test_f2` covers each refusal.
- **(1) OFF is byte-identical.** Patches 01–03 add 35 files under `u0/`, all from `/dev/null`, and they rebuild `work/src/u0` and `EXTENSION_PINS`. The non-u0 tree equals the A4 base pin (`813fe4c5…`, 927 files). Patches 04–05 apply with fuzz 0 and reproduce the operator after-hashes, including `0.py`. OFF `memory_bound()` and the descriptors are unchanged. `FINAL_INTEGRITY.json` matches its documents, 73 checks, 5 patches, the MANIFEST and the kit and operations pins.
- **(2) Finding 1, the guard.** An in-memory probe on torch 2.11.0+cpu gave these results:
  - Caught per call: `add_` (also under `inference_mode`), `detach().add_`, `_foreach_add_`, `load_state_dict`, `.data` reassignment, `.to(float32)` and a buffer `add_`.
  - Caught only at the boundary: `.data.add_` and a numpy write.
  - At install: a model built in inference mode is refused.

  Cost is 7.6 ms per call at 256 tensors and 45 ms at 1,400, so per-call identity is cheap. `ModelMutationError` is a `BaseException`, and nothing in u0 catches it. `WEIGHTS.json` is written false first and set true only after the final boundary, and patched `unpack_return.py` refuses a non-true value. The processor-only switch installs no vision or SAM guard. The cited torch `_version` behaviour matches the installed source (`TensorImpl.h:291-305,413-418,2046-2056`, `autograd/graph.py:242-258`, `optim/sgd.py:378-380`, `InferenceMode.h`).
- **(3) Finding 2, the operator path.** `test_round4.test_f2` still runs the real `a/5.py`, `0.py` and `7.py` path with ON payloads, and it passes in the applied tree. Patch 04 adds `read_cache_bytes` under `read_extensions`. ON gives a host budget of 81,985,756,696 bytes against an allocation of 214,748,364,800, with `fits=True`. The caches store on CPU (`a0.py:94-96`), so the host bound is the right place to count them. The sharding claim is true: `a19.py:172` disables shards, and the operator refuses more than one card.
- **(4) Findings 3, 4 and 7.** All three have fixes, and `checks/round5_before` fails 11 assertions with the expected reasons.
  - Finding 3 adds `a20` (binding derivation, five operations scripts and `SUBMIT_CHECK`), and its tests exercise them.
  - Finding 4 adds `validate_profile` in the driver and in every worker (`run.py:65-87,112,194`), and the gate derives the profile from the adopted operator (`a20.py:70-90`). `work/gate_integration5.py` passes with the real CPU proof's SETTINGS.json.
  - Finding 7's test checks README text only, and that text contains the broken command (finding 1).
- **(5) Adoption steps and the GPU gate.** These are not executable as written (finding 1). The fill step is fragile (finding 2), and the gate is not bound to the step-600 weights (finding 5). The forecasts check out: 7,351.824 s, or 11.559 s per item, from `profile.json`. Every file that runs under Python 3.6 compiles under `/usr/bin/python3` 3.6.8.

## Findings

1. **LOW: the README unpack command fails as written.**
   - Evidence: `kit_parity50/README.md:121-124` runs `"$READ_PYTHON" -I -s -B "$LOCAL/step600/unpack_return.py"`. Line 3 of `unpack_return.py` is `from fetch_return import …`. Under `-I` the script's directory is not on `sys.path`, so it raises `ModuleNotFoundError`. This was reproduced on the A4 copy (`cont_ops16/.../out3/A4/unpack_return.py`); without `-I` it imports. A4's own operations ran the script with `-B` only (`make_operations.py:179`).
   - The tests mask it: `test_round4.py:367` inserts the target into `sys.path`, and `test_round5.py:163` only checks the README text.
   - The failure is closed, because the `&&` chain blocks the handoff, but the scorer cannot unpack.
   - Smallest fix: use `-s -B` (no `-I`) and run from `$LOCAL/step600`. Add a test that runs the README command as a subprocess on the fixture return.
2. **LOW: `o_pull_fill.sh` runs the ~21.6 GB pull, fill and dry checks in the foreground.**
   - Evidence: `a20.py:135-152` and `README.md:74` (`bash "$D/o_pull_fill.sh"`). Both cont_ops and A4 background this step: `cont_ops17/work/gen400b.py:62` and `make_operations.py:99` use `nohup bash … </dev/null >log 2>&1 &`.
   - A dropped or timed-out ssh session leaves a partial `$P/a/e`. Because of `test ! -e "$E"`, the step cannot be rerun without a deletion, which needs the user, or a rebuild under a new token.
   - Smallest fix: launch it with nohup to a log as `gen400b` does, then wait for `$P/a/1.txt`.
3. **LOW: `SUBMIT_CHECK` is weaker than cont_ops' A4 CPU-receipt check, but the README calls it "exact".**
   - Evidence: `a20.py:93-118` checks only the `passed`, `entry_sequence_passed` and `bundle_guard_passed` booleans, plus plan, payload, inputs, operator, memory and pool. cont_ops' `o_sub_A4.sh` also asserts these:
     - `batch_sha256 == sha(BATCH.sh)` for the guard and the entry sequence (lines 16 and 22);
     - the path, guard target and action (lines 15 and 21);
     - the events (line 19);
     - `guard_target_sha256` (line 29);
     - the requested and dispatched argv (lines 31-32);
     - MEMORY.json equality (line 34);
     - `perception_memo_modules` and `sam_measurement_required` (line 36).
   - `README.md:111` says "exact". At submit, only PACKAGE.json pins BATCH.sh (`8.py:42-44,80-83` inside `0.tgz`), and PACKAGE.json sits in the same writable package. The CPU proof's `batch_sha256` is never compared, so a BATCH.sh and PACKAGE.json rebuilt together after the proof would pass. This is defence in depth, not a live hole.
   - Smallest fix: embed `o_sub_A4.sh`'s assertions verbatim in `SUBMIT_CHECK`, keeping the added `read_cache_bytes` and pool checks.
4. **LOW: residual of previous LOW 2. a19 still copies some A4 members without a pin.**
   - Evidence: `a19.py:162-163` decodes the base BATCH.sh and checks only its `0.json`. The bundled `0.py` and BATCH.sh are never compared with MANIFEST `operator_base_pin` (`batch_sha256` and `decoded_bootstrap_sha256`), which neither a19 nor a20 reads.
   - `a19.py:187-192` copies `3.py`, `a/0.json`, `a/4.py`, `a/7.py` and `fetch_return.py` without a check. The built fixture happens to match.
   - Smallest fix: in `authenticate`, require `sha(base/package/BATCH.sh) == operator_base_pin.batch_sha256`, the bundled `0.py` against `decoded_bootstrap_sha256`, and the copied members against pinned A4 hashes in the MANIFEST.
5. **LOW: the GPU gate is not bound to the step-600 weights or the production device.**
   - Evidence: the README asks for "intended staged asset paths" but gives no staging command (`README.md:135-139`).
   - `export`, `export_pin` and `artifact_manifest` come from the private template (`config.example.json`), and `a20 gate` checks only `ready.settings`, plan, payload and operator (`a20.py:72-76`). Nothing ties them to CPU.json `ready.binding`/`ready.restore` or to `STEP600_BINDING`, so any checkpoint passes.
   - `run.py:159` records the device but does not require it.
   - Smallest fix: in `a20 gate`, require the staged export's RESTORE and manifest hashes to equal the CPU.json `ready` pins. Record the required device type in the config, and have `run.py` refuse a mismatch, or state that the gate certifies ON/OFF equality on a different GPU type.
6. **INFO.**
   - `o_pull_fill.sh` checks `.done` with an exact string, `test "$(cat "$E/5")" = 'obj bytes sha'` (`a20.py:137`). `derive_binding` and `a/4.py` split on whitespace instead. A `.done` file with different spacing fails closed.
   - The 9.json `export_binding` now carries the Orchard paths `done` and `prep_paths`. This is harmless: `verify_config` checks only the digest, and admission reads fixed keys.
   - `o_sub.sh` has no machine check that the GPU gate passed. The order of steps relies on the operator following the README.
   - Carried-over guard limits remain and are documented. `.data` in-place writes and raw storage writes are caught only at type boundaries, and a write that is restored between two boundaries goes undetected.
