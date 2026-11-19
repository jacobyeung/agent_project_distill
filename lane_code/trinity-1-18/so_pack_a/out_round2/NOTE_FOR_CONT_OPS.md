# Step-600 packaging

1. Pin the builder, source delivery, items, step-600 binding and CPU/GPU scripts. Supply a current Trinity ledger and a coherent D source/embedded release. The supplied scorer mismatch blocks use. REQUIRED_INPUTS.json names unavailable inputs; check_required_inputs.py checks the production_build, r10 and routed_harness groups by name.
2. Supply export_binding_pin.path and .sha256 for the complete builder binding: the native D delivery omits parts[].bytes from its plan. Check compares that binding with every sealed binding field and the REVIEWED triple. Set remote_input_pins to its part sizes and the exact metadata sizes. Set dependency_reference to the pinned B5 a/0.json (Orchard-proven), and native_dry to pinned dryres_d.py. The example contains the available reference and harness pins; the step-600 binding remains required.
3. Use explicit fill_mode="structural" for tiny fill/resolver stand-ins. It checks real dependency layout first and reports production_archive_identity=false. Mirror mode defaults to a 1 GiB read budget and needs actual archives. The review reports 33,410,549,760 bytes of B5 inputs and estimates 155 GB of reads. Heavy Trinity IO needs permission; transfers above 30 GB need an admin plan.
4. Run build, then check, with pack.py --enable --config CONFIG and the explicit --token HEX at build. Use the specified CPU Python with -I -s -B. All production changes are opt-in; token adaptation requires --enable-token. BATCH requires umask 077; normalize_wrapper=true adds it. check_timeout defaults to 240 seconds per probe (300 in the example).
5. Have the Orchard lane stage parts 0..3, receipt 5 and preparation 7/8/9. Native place_fill_d.py documents REUSE_PARTS_FROM / PREP_FROM or a verified GCS pull; its whole driver owns place/fill too, so do not share that token with pack place. Pack does not fetch inputs. Reserve the built token and delivery SHA in the Trinity ledger before place. Pack enforces token presence but does not append the reservation. Thus all --execute-remote refuses until this separate reservation exists. Prefer separate build/check/place calls.
6. place --execute-remote runs read-only size, .done and preparation-hash preflight before place.attempt. If using printed scripts manually, run preflight.sh first; manual scripts do not enforce the local ledger check. Fill detaches, polls at 60-second intervals and writes a/1.txt last. Inspect a/f.log and a/f.exit. Calls time out at 300 seconds; fill_wait defaults to 1800 seconds. Never relaunch after an uncertain timeout.
7. submit and gpu require --yes --token HEX. Native CPU completion and CPU.json gate GPU submission; use gpu after a safe queue refusal without repeating CPU submission. CPU terminal failures include the tails of a/4.err and a/4.log. Reconcile persistent a/g.lock manually. job.stage verifies real archives. Local 3.6.8 tests include 8.py submit with stub sbatch; no live SSH or Slurm test runs here. Remote HOME=/tmp differs from native runs. D estimates 19,595 GPU-seconds and budget_fits=false for four hours.

## Forbidden-word rule

- (a) Job name: every sbatch job name fully matches `^a15_cot_ap[a-f][0-9a-f]{10,15}$`, and no `--comment` is passed.
- (b) Terms: native `orchard_h10/common.py` FORBIDDEN, plus pack's 9 extras (pack.py:7), plus `forbidden_extra`. Match case-insensitively, as substrings.
- (c) Apply the terms to:
  - every sbatch argument and `#SBATCH` value;
  - the argv, cwd and env name=value of every login-node and job process (pack's phase-script words and fill argv, plus the native runtime guard);
  - every path component created or referenced on Orchard storage: the package dir, top-level and `a/*` names, fill outputs, staged inputs, pool, return, capture and log names.
- (d) Exempt:
  - member names and bytes inside 0.tgz, the dependency and preparation archives, and the BATCH.sh bundle;
  - file contents;
  - Python stdin heredoc bodies;
  - comments;
  - log contents;
  - the command word of the listed utilities.

  Protect these by containment instead: 0700 directories, 0600 files, `umask 077` in every phase and in BATCH.sh, and the job temp dir `/tmp/a<job><token>` created 0700.
- (e) Keep the all-bytes `old_identities` scan. It is a stale-identity gate, not a privacy rule.

The listed utilities are `head tail sed awk cat wc df hostname nvidia-smi sacct squeue sbatch python3 bash env timeout`. The sealed shell may use `--job-name="${P##*/}"`; the planner binds P to the validated package name before execution. Substring matches such as `--noheader` and `unknown` still refuse, as the rule requires.

## Review round 2: finding -> fix -> test

| Finding | Fix or remaining limit | Regression |
|---|---|---|
| 1 MEDIUM | Check each export part size against the binding and its sum against REVIEWED_ARCHIVE_BYTES. Preflight reads the REVIEWED .done triple and hashes all three preparation files before place.attempt. A missing complete binding requires export_binding_pin. | test_01_wrong_part_pins_at_check; test_01_wrong_part_sum; test_01_missing_binding_parts_names_input; test_01_wrong_done_before_place_attempt; test_01_wrong_preparation_before_place_attempt |
| 2 LOW | Hash the real dependency archives and dependency file pins against the pinned Orchard-proven B5 reference before substituting tiny archives. | test_02_dropped_real_dependency |
| 3 LOW | Require the built token in the Trinity ledger before even calling preflight. | test_03_unreserved_token_before_preflight |
| 4 LOW | Validate every --job-name / -J value; reject every --comment. | test_04_all_job_names_and_no_comments |
| 5 LOW | State the exact forbidden-word rule in NOTE and REPORT. | test_05_exact_forbidden_rule_documented |
| 6 LOW | Add check 6(a–e) rows and state that the third consecutive accounting error aborts. | test_06_five_rows_and_error_limit |
| 7 LOW | Poll tails 8192 bytes per CPU stderr/stdout file for terminal failures; the local exception includes that text. | test_07_failed_cpu_returns_log_text |
| 8 INFO | Execute the SHA-pinned native dryres_d.py unchanged under 3.6.8 on filled local inputs. dry2/dry2b predicates remain translated: their fixed production policy archive is absent. | test_08_pinned_native_harness_is_executed; positive fill results contain native_dry.result |
| 9 INFO | Pass the caller's HOME and SSH_AUTH_SOCK to the local transport. Remote HOME=/tmp remains a documented live-environment difference. | test_09_transport_uses_caller_identity |
| 10 INFO | bash -n validates the detached fill body; receipt reports its actual wrapper interpreter and its 3.6.8 predicate interpreter separately. Round-2 before-fix regressions fail on the defect, with no KeyError. The guard test observes the launched interpreter; the login test observes the SHA of the bytes passed to place. | test_10_fill_body_bash_syntax; test_10_receipt_interpreter_label; test_r6_login_runtime_guard_submit_pool; test_r11_login_exact_delivery; before.log and before_evidence.log |

The login/fill probes still run several native steps inside one isolated 3.6.8 interpreter with the pack path on sys.path. Separating each step while preserving filesystem redirection and the sbatch stub requires more than the requested small INFO fix; live process isolation remains untested. The D scorer mismatch, budget_fits=false, absent full r10 build, B4 root cause, and trainer-rank USR1 remain open.

## Review round 1: finding -> fix -> test

Detached fill, structural stand-ins, actual D checks, staged-input preflight, command-only utility exemptions, 3.6 execution, production module imports, GPU-only retry, Python-stdin heredoc restrictions and exact-delivery checks remain covered by test_review.py. Native scorer drift remains a refusal tested by test_native.py. The test suite also checks the Trinity ledger prerequisite and the operator inventory.
