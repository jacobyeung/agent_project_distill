VERDICT: GO

Adoption answer: yes. cont_ops can adopt the patches for step-400 reads once the 50-item H100 gate passes on the step-400 export and the production device with zero answer and trace byte differences. Both tenth-review MEDIUM findings are fixed as `PROMPT_so_read_fix10.md` decides. No HIGH or MEDIUM defect remains. One LOW test-fixture gap and four INFO items follow.

## Findings

1. LOW. The sealed-path test uses a hand-built settings dict instead of the shape `a18.run` emits.
   - Evidence: `work/src/u0/tests/test_round10.py:110-138` writes the settings by hand and asserts `len(seen)==12`. Two of the 12 are `environment_receipt` and `export_pin` (line 123). In a real run those are config keys, and `validate_existing_paths(settings)` (`out/kit_parity50/run.py:133-140,323`) never sees them. Real prepared settings (`work/src/u0/a18.py:57`) carry 10 absolute paths.
   - Impact: none today. My probe sealed `a18`-shaped settings with A4's step-400 input paths through `a11 seal --aliases host.private_aliases(...)`. Six non-opaque paths went to zero, and every path resolved after `host.stage`. The two receipt paths exist anyway, through the `9.json` alias and `d/6.json`. The weakness is that the test would not catch a future `a18` settings key that lacks an alias.
   - Smallest fix: build the fixture's settings from `a18.run` output, or from the round-4 CPU fixture's `SETTINGS.json`. Then assert that every absolute string resolves after `stage`.

2. INFO. `4.tar` is now extracted before its hash is verified.
   - Evidence: `out/kit_parity50/host.py:28-45` hashes the stream it pipes to tar and checks size and SHA only after tar exits. It is called at `host.py:148`.
   - Impact: if the bytes are wrong, they land in `root/sj/<logical>/d`, but no aliases, `1.json` or `2.json` get written, and `runtime_context` refuses the launch. This fails closed. It is the single-read design the prompt chose, and `README.md:291` states it truthfully.
   - Smallest fix: none needed. Optionally, extract into a sibling temporary directory and rename it only after the hash matches.

3. INFO. The check log ends in a storage assertion, so child-process memory (RSS) for that runner is not recorded.
   - Evidence: `out/checks/run_checks10.txt:34-38` raises `AssertionError` at `assert report['workspace_bytes']<3_000_000_000`. `REPORT.md` discloses this. `finish_checks10.txt` passes at 2,871,926,607 bytes after sharing. All 18 workspace suites (147 tests) and 9 applied suites (66 tests) report OK.
   - Smallest fix: rerun the runner after sharing so it records RSS under the cap.

4. INFO. These limits are carried over and stated truly in REPORT and README.
   - The H100, torch 2.13, the real bwrap namespace and the real site overlay have not been executed. The GPU gate is the only proof for them.
   - A worker failure writes no receipt; the run simply fails.
   - There is no host-side argv word screen beyond `a9.opaque`.
   - `.data` and NumPy writes bypass `_version`. The boundary content digest catches them, the per-call stamp does not.
   - The fixture storage harness (`work/run_fixture5.py`) swaps `Path.open` and `Path.write_bytes` for hard-link and copy-on-write equivalents. File contents and exclusive-create behaviour are unchanged, and all delivered kit files have link count 1 with pins matching.

5. INFO. The reviewer wrote one file outside this folder.
   - An accidental stdlib-shadowed probe created `/scratch/jjyeung/orch_n30/so_read/work/src/orchard_h10/__pycache__/operator.cpython-36.pyc`.
   - It is outside `FINAL_INTEGRITY.json` scope, `u0` has no `__pycache__`, and base inventories exclude `.pyc` files. Nothing reviewed depends on it.
   - I did not delete it (no-deletion rule). The owner may remove it.

## Previous LOW 1-5

1. **README commands run as written.** Pass.
   - The `PRIVATE_ALIASES` heredoc (`README.md:187-194`) imports `host.private_aliases` with `-I -s -B -`, and I reproduced it.
   - The seal, stage-kit, `4.tgz` and the GPU block match the CLI arguments in `a11`, `a19`, `a20` and `host`.
   - The token regex accepts `a`+12 hex characters.
2. **Pull and fill run detached.** Pass.
   - `a20.py:203-221` uses nohup, a permanent lock, a PID file and an exit-status trap.
   - The wait runs once a minute and is capped at 4 h.
   - The round-6 test covers a refused duplicate and a vanished PID.
3. **SUBMIT_CHECK strength is stated truly.** Pass.
   - It checks the guard self-test, plan, profile, device, assets, `adoption_kit == gate_kit_sha256` (which now includes `u5.py`) and the environment.
   - The README claims nothing beyond those checks.
4. **Every copied A4 member is pinned.** Pass.
   - The MANIFEST pins match.
   - The base is 927 files at 813fe4c5, and all 42 extension pins match.
   - The `v/py` and `boot.py` hashes match the supplied ones. `A4_WRAPPER_PINS10.json` states truthfully that earlier rounds had no independent wrapper pins.
5. **The GPU gate is bound to step 400 only and to the production device.** Pass.
   - `a20.py:109` refuses any identity other than `DEFAULT_BOUND_EXPORT` (3ecf3483).
   - `run.py:117-123` requires exactly the H100 80GB HBM3 with 132 SMs, capability 9.0 and 79–86e9 bytes.

## Questions 1-5

1. **OFF stays byte-identical.** Pass.
   - The patches add files only.
   - The base inventory and extension pins hold.
   - `test_off` and `applied_off` pass.
2. **Per-call identity is cheap and catches what the reader can see.** Pass.
   - Mechanism: `a0.py` stamps id, data_ptr, `_version`, dtype, device, shape, stride and requires_grad, and takes a content digest at install and at boundaries.
   - Installed torch source: `TensorImpl.h` confirms that `.data` does not share the version counter, that `set_data` preserves it, and that inference tensors have none.
   - Probe results:
     - Every in-place, `copy_`, optimizer and parameter-swap mutation was caught per call.
     - `.data` and NumPy writes were caught at the boundary.
     - Inference tensors were refused.
     - Cost was 3.6 ms per call at 128 tensors and 21.5 ms at 700, which is negligible against seconds per item.
   - A mismatch raises `ModelMutationError` (a BaseException), so the worker and the run fail.
   - The processor-only switch works:
     - `a19.py:194-197` turns the vision and SAM caches off and sets 4 GiB.
     - `a19.py:246` sets the processor_only profile.
     - `a0.py:28-29` validates the switch.
3. **The A4 operator path is tested with ON payloads.** Pass.
   - `test_round4.py:162-369` runs `7.py` and `0.py` with ON configs and gets 636 completed.
   - Patch `04_operator_cache_bound.diff` adds `read_cache_bytes` to `host_budget_bytes`.
   - The NOTE's line 7 claim (single-card, no multi-card operator) is true: `a19.py:246` sets `cards=1`, and `read_scene_shards` is off (`test_round4.py:317`).
4. **Findings 3, 4 and 7 are fixed.** Pass.
   - Their round tests still pass.
   - All 14 before-controls in `run_checks10.txt` still pass, so each test fails on the pre-fix code.
   - Separately, `round10_before.txt` shows all 7 new round-10 tests fail on the round-9 code for the right reasons.
5. **The NOTE's adoption steps and the 50-item gate are executable as written.** Pass on CPU.
   - Every step's inputs are produced by an earlier step. One example: `2.tgz` carries all five receipts that `a20 gate --asset-receipts` reads.
   - The time budget fits in 5 h: about 9 worker runs of ≈650 s each, plus staging.
   - Only the H100 run itself remains unverified (finding 4).

## Tenth-review findings

1. **The preflight is a pinned script.** Fixed.
   - `host.py:165` launches `u0/u5.py` as a script path through the wrapper, and `kit_hashes` pins it (`run.py:126-130`).
   - `test_round10.py:47-108` runs the real `boot.py` bytes from `a4_vpy`. The probe refuses `-c`, forwards argv to the script, and a tampered `u5.py` is refused.
2. **One alias table covers every sealed path.** Fixed.
   - `host.ALIASES` (`host.py:18-26`) feeds both the README's `PRIVATE_ALIASES` and the symlinks `stage` creates.
   - Every sealed path is checked to exist before the self-test (`run.py:323` runs before `run.py:335`).
   - Loader admission uses realpath, so the symlink aliases pass the allow-list. The test-coverage caveat is finding 1.
3. **No nested bwrap.** Fixed. `worker_command` returns `[python,'-B','-I']+args` inside the namespace (`run.py:156-159`), and `host.gate_environment` supplies `U0_ROOT` and `U0_KIT` (`host.py:79`).
4. **`4.tar` is hashed once.** Fixed.
   - The host does one open and one read, piped to tar while hashing (`host.py:28-45`).
   - The README pre-stage check is size-only (`README.md:255`).
   - The test counts one open and refuses a bad pin.

Earlier rounds stay fixed: suites for rounds 1–9 and both applied suites pass unchanged.
