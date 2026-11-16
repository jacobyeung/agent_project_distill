# Review verdict: C8r native routed-read kit (code f4535bc0, family 0bfae7e4)

Reviewer lane review_c8 (trinity-1-13), 2026-11-15T23:55Z. Read-only. Work files: `/scratch/jjyeung/orch_n30/review_c8/work/` (STEP1_EXPECTATIONS.md, my_diff_vs_p9.patch, MY_GUARD_CENSUS.txt, mut/MUTATION_RESULTS.json).

## Verdict

**GO for the full read on family 0bfae7e4, with no change to the code object.** Two conditions apply. Neither condition alters the family; any family change would force a new pilot, because the full packet binds the pilot's family (native_metrics.validate).

1. Pilot 170049 must return COMPLETE through at least one verified channel, and `native_metrics.from_return` must admit it. Pilot 170049 is the first run of native_job.py:190 (pool write test), native_job.py:260-261 (publish with mode and gcloud config) and gcloud on Orchard. No rehearsal executed those three; only unit tests did.
2. Before anyone reports a headline, write the native-against-direct comparison and have it reviewed (finding F1). The kit contains no such code.

**Pilot 170049: safe to let it run.** It reads dev-S1 items only. Its return goes to `/project/community/jjyeung/okh7/n2r` and `gs://…/q8/n2r/<token>`, and neither CONFIG nor FAMILY names any `/home` path. Pilot 9's timings give about 790 s of staging plus GPU work, well inside the 6,000 s worker limit and the 02:00:00 Slurm request. The worst case is a FAILED return and one lost GPU-hour.

## Step 1: what the records require, checked against the code
I wrote `STEP1_EXPECTATIONS.md` from the records, the rulings and the recovered orders before I opened the builder's notes. The code matches it on every point:
- **Denominators.** Every item counts (150/36/450). Geometry refusals score zero in both arms and keep their own column. They are left out of the no-answer and model-row unit counts.
- **R1 call rate.** It is computed over decoded items, with geometry refusals excluded from that denominator only (r1.py). The all-item rate is printed beside it.
- **Budget.** 2,048 sampled callbacks, then a deferred close (up to 96 tokens) while a call is open, then 64 answer tokens, then EOS. Calls after the trigger are tagged budget_truncated. `capped` covers the budget, call_limit, max_new_tokens and context exhaustion.
- **Logging and units.** ground_queries is digested, with full queries kept for 3 items per type. Units are reported as metre-based versus other and as metric versus non-metric; neither enters R1.
- **P1 gate.** The tie limit is max(1, checked//100). That matches the brief's ruling in force; the 14:20Z ruling said 2%.
- **The four changes.**
  - R1 fix (04:54Z, 05:02Z): program_refusal rows are skipped by the token and timing checks (project, terminal), counted in a reported field, and kept in every denominator.
  - Pilot limit: gpu_seconds is 6,000, and sbatch moves from 01:30:00 to 02:00:00 so the allocation covers it.
  - Selector (05:10Z): parity_selection picks the same probe on dev-S1, byte for byte.
  - Guard wrapper (07:16Z, 08:04Z): the reviewed a62e3975 text plus the class-identity refusal. It checks the source sha and the AST tail and intercepts only the named error. The reviewed guard decides in both cases. It is installed after the authenticated restore: in pilot mode after `restore`, in full mode after `geometry_restore`.

## Step 2: every hunk of C8r against pilot 9 (my own diff; JSON receipt checked separately)
- **Guard.** geometry.py capture context; perception.py capture context; nomdg adapter_sources, request identity and validate_request identity; worker install, reports and comparison; native_job terminal validate_gravity_guard in pilot and full; native_metrics.validate_gravity_guard; launcher PACKET identity.
  - Effect: it changes refusals, with 10 d3 captures restored. It changes no prompt, decoded token or score rule.
- **R1.** native_metrics program_refusals, the project exclusions and timing_measured; worker pilot-row fields and the full report field.
  - Effect: reporting and admission only. timing_measured can only refuse a full packet.
- **Limit.** launcher gpu_seconds 6,000 and the sbatch time.
- **Selector.** nomdg parity_selection, LOAD_RECEIPT and the parity pass rule.
  - Effect: identical on dev-S1.
- **Return path.** orchard_results rewrite, orchard_launcher fetch, native_job write_test and publish arguments, launcher return_bytes and DIRECT_DIGEST, metrics RETURN_LIMIT 300 MB−16 KiB (equal to the publish cap), local_check PACKAGING.
- **Packaging.** MASK_CACHE_C8_BOUND.json. I checked that only producer_sha256 changed and that it equals the c4a505fc nomdg pin; native_pin_graph MASK_PATH follows it.
- **Unmapped (F2).** native_worker.py about 225 drops the `near_boundary` requirement from the pilot geometry audit's raise. No order covers it.
  - Effect: it touches no prompt, response, token, refusal or score. On pilot 9's geometry, 6 captures satisfy the requirement anyway (41126645, 41291639, 41291643, 42897921, 47332556, 47332599), so restoring it would cost nothing.

## Step 4: guard
- The wrapper logic equals the 07:16Z ruling.
- I recomputed both guards myself on all 84 of pilot 9's step-544 NPZs (sha-checked against the manifest):
  - Sealed guard: 11 refusals, equal to pilot 9's recorded set.
  - Reviewed guard: 1 refusal, d3/41254810. Its frame-0 in-plane norm is 0.644 and its margin −0.031, so it is a real rolled reference, not near-nadir noise. It carries 2 distance items.
  - Reviewed-only refusals: 0.
  - The builder's counts are confirmed.
- C8 full-rehearsal coverage shows that these call sites executed: geometry_profiles.py:119, the sealed raise at :97 (caught by the wrapper), ground_v3.py:90, and the reviewed-refusal branch of the wrapper.
- geometry_profiles.py:200 is unexecuted. It is a legacy profile that these worker paths never produce.
- GUARD_CALL_SITES.md is stale: it says NOT EXECUTED on every row (F3).
- The trainer authentication (verify_trainer, authenticate) hashes files only, so the in-memory rebind cannot trip it.

## Step 5: coverage
- C8r differs from the C8 code that the full rehearsal ran (d03de829) in 6 files only. I confirmed this by diffing the sources. All reader, policy, guard, R1 and merge code is byte-identical, so the C8 full-mode coverage carries over to those files.
- **C8r statements that no pilot-mode or full-mode run executed:**
  - native_job.py:190 and :260-261: unit tests only; first executed by pilot 170049.
  - native_launcher.py:24 and :63: sealing and packaging; :63 is a recorded limit that nothing enforces.
  - native_local_check.py:30: packaging only.
  - orchard_launcher.py:365: operator fetch.
  - 172 orchard_results lines: error and GCS stand-in branches, unit-tested.
- **Full-mode-only C8r statements that the full read will execute:**
  - `mode_limit('full')` and the 300 MB archive cap, covered only by test_caps_and_full.
- **Judgement on the seven non-return lines and the packaging line:** none can change a prompt, response, token, refusal or score.
- **A C8r full-mode rehearsal is not needed,** provided condition 1 holds. The only full-only lines, `mode_limit('full')` and publish with mode='full', are already covered by test_caps_and_full, which passes.

## Step 6: pins
- I recomputed every code pin, adapter pin and bootstrap pin against the shipped tar (41, 21 and 18 pins): 0 mismatches. The kernel pins, entrypoint (#35), mask producer (#42) and code tar sha all match.
- **Orchard-only rows.** Each check compares live bytes with a pin, so a stale pin fails closed. A stale pin could pass only if the Orchard object had changed to match it.
- **Family comparison against pilot 9 (3688e987).** Diffing it myself, the only differences are the code object, the code members and pins, the entrypoint, kernel, adapter and mask pins, direct_launcher_digest and the limits. Every runtime, export, base, frames, trainer and depth pin is unchanged from a family that passed on Orchard. The comparison is an adequate stand-in for the lost native_local_check, for these rows only.

## Step 7: mutations (all 76 tests pass on unmodified code; results in mut/MUTATION_RESULTS.json)
Killed means a test failed on the mutant's meaning, not only on its changed file hash. 11 of 16 mutants were killed.
- **Killed:**
  - M1: the guard intercepts every GeometryError.
  - M2: no class-identity check.
  - M3: frame-0 sign only (the sealed rule).
  - M4: the sealed guard decides.
  - M5 (report): program_refusals counts nothing.
  - M6 (report): program_refusal rows stay in the timing.
  - M7 (report): timing_measured is always true.
  - M11: the limit goes back to 2,400.
  - M13: no request guard-identity check.
  - M15: the full cap equals the pilot cap.
  - M16 (report): close_lengths includes refusals.
- **Survived** (only the seal and packet hash tests failed, or nothing failed):
  - M8 (report): validate_gravity_guard ignores the reviewed list.
  - M9: a camera call is always required (equivalent on dev-S1).
  - M10: pilot decode_executed ignores program_refusal.
  - M12: terminal drops the pilot guard re-validation.
  - M14 (merge): full program_refusals is taken from the scripted arm.
  - None of the survivors changes a score or an R1 verdict. M8 and M14 are reporting-only gaps (F4).

## Findings
- **F1 (blocks the headline, not the GPU read; analysis code outside the kit).**
  - The brief's headline compares native against direct with paired 95% intervals over rooms. The kit computes native against scripted (R1) only.
  - The kit's only intervals (camera_report.py:25 and :74) cluster by capture and print "never physical-room clustered".
  - Failing input: dev-S1 includes d1/scene0155_00, _01 and _02, three captures of one room. Capture clusters treat them as independent, so the intervals come out too narrow.
  - The 2 items refused on d3/41254810 score 0 natively but carry a real score in the direct read. That biases the distance difference by up to −1.33 pp, unless the comparison reports all items and the passed-geometry subset side by side.
  - Fix: one reviewed script that pairs by key with the same label (released_answer for primary), uses room clusters, and reports both subsets. Needs an orchestrator ruling on the cluster unit.
- **F2 (minor).** The unmapped near_boundary removal (step 2). Leave it in place and record it.
- **F3 (doc).** GUARD_CALL_SITES.md is stale. Coverage supersedes it.
- **F4 (tests).** M8 and M14 survive. Add tests at the next reseal; they do not justify a reseal now.
- **F5 (run-time risk).**
  - Pilot 9's none_capped projection is 14,018 s with margin. C8r decodes about 19 more distance items than pilot 9 did.
  - The step-544 direct read put 62 of 150 distance items at the budget. Such items cost about 123 s each, so a capped scenario can exceed 21,600 s.
  - Choose the full-read scenario from the C8r pilot's measured capped fraction (replay_estimated), not from none_capped.
- **F6 (legality, inherited, for an orchestrator ruling).**
  - CONFIG and FAMILY on Orchard reference existing paths containing "distill" (`/project/community/jjyeung/distill/okit/in/c_fa8681cba4c0.tar`) and "qwen35" (`cp4tk_rt/kit/model_qwen35_9b_…tar`), and item keys containing "vsi590k". Every earlier pilot carried the same.
  - New in C8r: ORDER.md, shipped in the payload, says "native routed-read".
  - The job name, the new pool, the GCS prefix and the sbatch arguments are clean.
- **F7 (official read only).**
  - The selector change is probe-only.
  - native_metrics.validate still requires `parity.camera_call is True`, so a camera-free pilot can never admit a full read. The official read needs a further change.
  - Not relevant to dev-S1.

## Builder claims I could not confirm
- 15 PASS and 4 PASS-REHEARSAL pin rows: I re-derived only the code and family pins and the census; I did not rerun OBJECT_AUDIT on the GCS objects.
- The C8r pilot rehearsal passed end to end. I relied on its coverage file and did not rerun it.
- The builder reported 75 tests; I ran 76, all passing.
- The code object at GCS generation 1794780972269985 equals the local f4535bc0 tar.
- Orchard-side behaviour: gcloud writing nothing under /home, and the pool quota.

## What I did not check
- I did not rerun the whole-worker rehearsals (the node's disk floor).
- I did not read the 172 unit-test-only orchard_results lines line by line.
- I made no Orchard or GCS call.
- I did not read the parts of kernels.py's ten-pair selector or camera_report that were unchanged since pilot 9 beyond the lines cited.
- I did not trace the cause of ProgramRefusal inside the sealed runtime.
