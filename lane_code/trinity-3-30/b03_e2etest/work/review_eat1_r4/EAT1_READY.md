# EAT-1 ready: the end-to-end acceptance test is built, CPU-tested, and run on both baselines

EAT-1 is built and passes its CPU tests. It fails C8r on A1, A2, A3, A4 and A5. It fails the next-leg tree b5 on A2, A3 and A4 on every routed type, and on A1, A3, A4 and A5 on the distance and room types. GF-1's tower passes A1; its A5 (i) fails on a config file the reader reads from the code tree. The clause definitions and the allowlist were refuted three times by another model family; every defect is fixed with a planted test, and the revised kit awaits round 4.

## What it is (`eat1/`, file hashes in `work/EAT1_FILES.sha256`)
- `run.py` wraps any reader that exposes `generate(frames, question)` and judges A1–A5. It writes A6 per type: call rate, the heads behind each response field, and seconds per item. Options: `--sandbox` (A5 i: bwrap rerun with every outside directory unmounted), `--perturb [--perturb-limit N]` (A5 ii), `--strace-log`.
- `hook.py`: an audit hook on file opens plus `/proc/self/maps` windows (A1). It also holds the model monitor, which counts model entries and classifies every fed token as prompt, model argmax, registered-handler output or injected (A2). It accepts a split LM entry (model.model + lm_head). Line scope covers reader lines executed outside module forwards (A3/A4 scope).
- `scan.py` + `allowlist.json` form the static scanner: table loads, data-file names, numeric constants, thresholds, unit conversion, guards, status literals, except-substitutes, caches, and responses written outside a module. `closure.py` computes a reader's static import closure.
- `artifact.py` holds the `eat1-artifact-v1` manifest: files by sha256 and role, and modules by path and role.
- `adapters/`: `c8r_tiny.py` and `gf1_tiny.py` (tree tiny fixtures, CPU), `b04_tiny.py` (lane b04's end-to-end reader on its tiny kit, CPU; result `out/EAT1_ON_B04_TINY.md`: A1, A2 and A5 PASS, A3 and A4 FAIL) and `c8r_native.py` (the real C8r no-MDG reader, GPU, untested).
- `toy/` holds the clean toy reader plus six planted violations (the brief's five plus a threshold hidden in a head-class method). `toy/adversarial.py` holds the reviews' 40 planted variants plus nine compliant controls. `tests/test_eat1.py` has 25 tests; the latest run is `Ran 25 … OK` in 147 s (`work/test_run_12.log`). Run: `cd L && EAT1_TMP=$L/work/tmp /scratch/jjyeung/envs/p1cpu/bin/python -m unittest eat1.tests.test_eat1`.

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

## Rules after three cross-family refute reviews (Codex gpt-6-astra, each NO-GO: `events/b03_e2etest/REVIEW_VERDICT_EAT1.md`, `_R2.md`, `_R3.md`)
Every defect has a planted variant in `eat1/toy/adversarial.py` (40 violating, 9 compliant controls: `numeric`, `memo`, `native_units`, `clamp`, `bookkeeping`, `scalar`, `relu6`, `unit_answer`, `numpy_print`), and each violating variant fails its clause for its planted reason. Tests: `Ran 25 … OK` (`work/test_run_12.log`). The rules in force, against the user's wording:
1. A3 value provenance (ruling 5, "unprojection and printing head outputs as text only"): every number a registered handler writes must be `str()` of an element that a declared head, tower, connector or `fixed_math` module (reviewed unprojection only) returned in the same item, or a number of the call itself (`A3.response_value`); `str(float(x))` and float32 shortest reprs both count as printing, and Python-scalar head outputs are recorded. Handler-side norms, rigid transforms, scales, conversions, thresholds, rounding, `%f` and `int()` therefore all fail, whatever code produced them. The toy computes displacement in a move head and depth in a head over the tower output.
2. The static scan stays as a second witness: precision choices fail `A3.reformat` (switch `format_precision`, false); constant-only expressions and multiplicative or additive chains are folded; thresholds cover numbers beyond 0 and ±1, attributes and comparison APIs, while clamps with bounds 0, ±1 or declared constants (ReLU, ReLU6) pass. On lines run inside a call handler, max/min/sort/argmax-like calls and comparisons of two computed values fail `A3.selection` (a handler that picks among head outputs is a policy).
3. Every executed line of reader code, head forwards and methods and lazily imported bodies included, is judged. Module-level numbers and tables, and instance or reader-class attributes holding numbers, or tensors that are neither parameters nor buffers and existed before the item, that an executed function reads on `self`, fail `A3.module_data` unless listed in `declared_constants` for review.
4. `if <test>: raise` validation passes; an item that raises fails A4.
5. An except-handler passes when it re-raises or only does bookkeeping (integer counters on attributes or subscripts, logging calls); any other body fails A4. `x or <numeric literal>` fails. Substitutes that reach a response also fail value provenance or the status rules.
6. A2: the key-value cache must be unchanged between model entries (content fingerprint with position-weighted sums, so permutations show).
7. A4: the scored answer is the final token run of the text generated after the last response, sign included; only closing markup, punctuation and one unit word the model wrote may follow it.
8. A5 (ii): a perturbed run that raises fails, calls that diverge before any response naming the target fail, and a target named in the baseline needs an eligible comparison. A5 (iii): a cache passes only with an equality proof on at least 50 items, and the report sets `claim_needs_live_run`.
9. A6 fails when reported calls differ from the handler's responses, or when the fields do not list exactly one entry per printed number in print order, or a field cites a module that did not produce its number.
10. A1 counts `O_RDWR`/`r+` opens, mmaps of descriptors, moved positions of descriptors opened before generate(), child processes and ctypes symbol lookups from reader code. A claimed PASS needs `claim_grade`: an strace log holding this run's nonce-marked window for every item, plus the sandbox and perturbation passes. Native units a head predicts can be declared in `native_units`, for printed labels and identifiers.

## Baselines under the revised kit
Static: C8r 1034 findings in 45 files (`work/c8r_static/SCAN_TIER1_v5.json`), b5 tree 632 in 33 (`work/nextleg/static/SCAN_READ_v5.json`). Tiny runs `work/c8r_tiny/run11`, `work/b5_tiny/run6`: A2, A3, A4, A6 FAIL, A1 and A5 PASS. GF-1 `work/b5_gf1_tiny/run9`: A2, A3, A4, A5, A6 FAIL; A5 (i) now fails because the reader reads `configs/gf1_stage1.json` from the code tree, which the claimed artifact must carry. The b04 tiny rerun waits: b04's reader refuses its kit because b04 changed `e2e_reader/artifact.py` after the kit was built.
