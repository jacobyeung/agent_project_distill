# Step-600 packaging

1. Pin the native builder, source delivery, items, step-600 binding and CPU/GPU scripts. Supply a current Trinity ledger and a coherent D source/embedded release; the supplied scorer mismatch remains blocked. For r10, supply both original deliveries and A's base/filled inputs. `REQUIRED_INPUTS.json` names missing inputs. `check_required_inputs.py --manifest out/REQUIRED_INPUTS.json --group production_build` checks availability; use `r10` or `routed_harness` for those groups. Availability does not certify the missing suites.
2. Set `fill_mode: "structural"` to check native fill/resolution with tiny pinned stand-ins. Production identity remains with native fill and `job.stage`. Default mirror mode requires actual bytes: the review's B5 inventory totals **33,410,549,760 bytes**, with about **155 GB of reads estimated by the review**. Its default read budget is 1 GiB; `check_timeout` defaults to 240 seconds per probe (the example explicitly sets 300). Large Trinity IO needs authorization; transfers above 30 GB need an admin plan.
3. Run `pack.py build --enable --config CONFIG --token HEX`, then `pack.py check --enable --config CONFIG`, using the specified CPU Python with `-I -s -B`. Token adaptation requires `--enable-token`. BATCH must set `umask 077`; optional `normalize_wrapper: true` adds it and retains head-to-sed normalization. The scanner accepts system `head` without normalization. All switches default OFF. Guard, place, fill, entry check, `8.py submit` with stub sbatch, and pool predicates execute locally under `/usr/bin/python3` 3.6.8.
4. Have the Orchard lane independently stage the actual parts `0..3`, `.done` receipt `5`, and preparation `7/8/9`; configure their exact sizes in `remote_input_pins`. Native `place_fill_d.py:66–108` documents `REUSE_PARTS_FROM`, `PREP_FROM`, and verified GCS pull. Its whole driver also places/fills: **do not combine it with pack place for the same token**. Pack does not fetch inputs. Its read-only size preflight runs before placement; when running printed commands manually, run `commands/preflight.sh` first.
5. Reserve the built token and delivery SHA in the **Trinity ledger before place**; pack does not append it. `place`/`fill` require `--execute-remote` to execute. Fill detaches, polls at least 60 seconds apart, and writes `a/1.txt` last. Inspect `a/f.log` and `a/f.exit`; call timeout is at most 300 seconds and `fill_wait` defaults to 1800. Never relaunch after an uncertain timeout.
6. `submit` requires `--yes --token HEX`; it waits for CPU completion before GPU gates. After a refusal before submission, use `gpu` with the same flags to recheck COMPLETED and CPU.json. Native `a/8.txt` and persistent `a/g.lock` prevent duplicate/uncertain submission. Reconcile an existing lock manually. No remote test ran here. Production archive/RGB/environment checks, missing harnesses, GPU behavior and trainer USR1 remain unverified; see ORCHARD_ONLY_CHECKS.md. D's native fixture estimates 19,595 seconds and reports `budget_fits=false` for four hours.

## Review round 1: finding -> fix -> test

| Finding | Fix | Test |
|---|---|---|
| 1 | Detached fill and polling | test_r1_detached_slow_fill |
| 2 | Structural stand-ins | test_r2_structural_without_archive_mirrors |
| 3 | Actual D build, seven probes and D scripts | test_native.py; test_r3_actual_D_integration |
| 4 | Size preflight before placement | test_r4_readonly_preflight_precedes_place |
| 5 | Command-only utility exemption | test_r5_system_command_only |
| 6 | Staging/hash documentation and 3.6 execution | test_r6_login_runtime_guard_submit_pool; test_r6_operational_inventory |
| 7 | Production module import | test_r7_production_module_import |
| 8 | GPU-only guarded retry | test_r8_gpu_only_retry |
| 9 | Python-stdin heredocs only | test_r9_only_python_stdin_heredocs |
| 10 | Keep native source-drift refusal | test_native.py |
| 11 | Exact delivery and ledger prerequisite | test_r11_login_exact_delivery; test_r6_operational_inventory |
