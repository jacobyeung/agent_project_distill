# EAT-1 ready: the end-to-end acceptance test is built, CPU-tested, and run on both baselines

EAT-1 is built and passes its CPU tests. It fails C8r on A1, A2, A3, A4 and A5. It fails the next-leg tree b5 on A2, A3 and A4 on every routed type, and on A1, A3, A4 and A5 on the distance and room types. GF-1's tower passes A1 and A5. The clause definitions and the allowlist are PROPOSED: they await one refute review by another model family.

## What it is (`eat1/`, file hashes in `work/EAT1_FILES.sha256`)
- `run.py` wraps any reader that exposes `generate(frames, question)` and judges A1–A5. It writes A6 per type: call rate, the heads behind each response field, and seconds per item. Options: `--sandbox` (A5 i: bwrap rerun with every outside directory unmounted), `--perturb [--perturb-limit N]` (A5 ii), `--strace-log`.
- `hook.py`: an audit hook on file opens plus `/proc/self/maps` windows (A1). It also holds the model monitor, which counts model entries and classifies every fed token as prompt, model argmax, registered-handler output or injected (A2). It accepts a split LM entry (model.model + lm_head). Line scope covers reader lines executed outside module forwards (A3/A4 scope).
- `scan.py` + `allowlist.json` form the static scanner: table loads, data-file names, numeric constants, thresholds, unit conversion, guards, status literals, except-substitutes, caches, and responses written outside a module. `closure.py` computes a reader's static import closure.
- `artifact.py` holds the `eat1-artifact-v1` manifest: files by sha256 and role, and modules by path and role.
- `adapters/`: `c8r_tiny.py` and `gf1_tiny.py` (tree tiny fixtures, CPU), `b04_tiny.py` (lane b04's end-to-end reader on its tiny kit, CPU; result `out/EAT1_ON_B04_TINY.md`: A1, A2 and A5 PASS, A3 and A4 FAIL) and `c8r_native.py` (the real C8r no-MDG reader, GPU, untested).
- `toy/` holds the clean toy reader plus six planted violations (the brief's five plus a threshold hidden in a head-class method). `tests/test_eat1.py` has 16 tests; the latest run is `Ran 16 … OK` in 23 s (`work/test_run_8.log`). Run: `cd L && EAT1_TMP=$L/work/tmp /scratch/jjyeung/envs/p1cpu/bin/python -m unittest eat1.tests.test_eat1`.

## Brief tests
| Brief requirement | Test | Result |
|---|---|---|
| passing toy reader | `ToyEndToEnd.test_clean_passes_every_clause` | PASS: all five clauses |
| one planted violation each: table, second entry, fitted threshold, guard, cache read | `test_each_planted_violation_fails_its_clause_only`, `test_offenders_point_at_the_planted_line` | each fails its clause, and the offender names the planted line |
| scanner flags all five and passes the clean toy | `test_flags_all_five_planted_violations`, `test_clean_toy_has_no_findings` | PASS |
| CPU run on a tiny model end to end | `work/c8r_tiny/run5`, `work/b5_tiny/run1`, `work/b5_gf1_tiny/run2` | run; results in the baselines |
| ruling 5: unit conversion or reformatting outside the model fails | `test_unit_conversion_outside_the_model_fails` | PASS |

## Deliverables
- `out/BASELINE_C8R.md` (+ `out/BASELINE_C8R_FINDINGS.md`, 965 static findings in 45 files).
- `out/BASELINE_A2_TREE.md` (+ `out/BASELINE_A2_TREE_FINDINGS.md`, 571 findings in 33 files).
- `out/RUN.md`: the GPU operator recipe, with 200 call-type items ranked ReVSI first, about 2.5 h on one H100 at 32 frames and about 4 h at 64 frames.

## For the refute review: interpretations to check against the user's wording
1. A3 fixed math follows USER ruling 5 (ORCH 1155Z): unprojection, rigid transforms, norms and min/argmin, and printing head outputs as text. Unit conversion and answer reformatting fail. The allowlist keeps 0, ±1, 2, 3, 4, 0.5 and π, plus `round(x, n)` precision.
2. `if <test>: raise` validation is exempt: it refuses the item with an error and writes no token. A caught error that becomes a response still fails A4.
3. Plain constants (A3.constant) inside methods of declared head, tower and connector classes count as model code: they are listed and do not fail. Thresholds, tables, guards, statuses and caches in those methods still fail; the planted `head_method` variant (a threshold in `RulePerception.adjust`) fails A3 in the tests. Call-handler classes and the root model class are never exempt. Residual hole: a fitted multiplier written as a plain constant in a head method passes.
4. `ClipCache` (GF-1, a per-row memo of the live tower forward) is flagged as A5.cache. Should it pass A5 (iii)?
5. A1 for an export that leaves out the frozen tower: it passes when the claimed manifest lists the pinned tower weights by sha256.
6. A2 counts response tokens written from Python outside a registered module as injected, even when they print head outputs exactly. This follows the brief's "a module registered on the model writes the response".
7. A typed `error:` response or a `not seen` status that no head formats fails A4. An except-handler that returns nothing (`[]`, `None`, `''`) writes no token and is not a substitute.
8. In a dynamic run, response text formatted by a function the registered handler calls does not fail A2 once the token provenance shows zero injected tokens. The static rule still applies in static-only audits.
9. A5 (ii) perturbs at noise gains 1 and 10 over 3 seeds. A response is eligible while every call up to it matches, so a response that reads earlier state (a gap over grounded boxes) must cite the modules behind that state.
10. Lines in module and class bodies executed by lazy imports inside generate() are out of the A3/A4 scope; the function lines that use those names are judged.
