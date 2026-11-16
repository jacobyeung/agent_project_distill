# EAT-1 ready: the end-to-end acceptance test is built, CPU-tested, and run on both baselines

EAT-1 is built and passes its CPU tests. It fails C8r on A1, A2, A3, A4 and A5. It fails the next-leg tree b5 on A2, A3 and A4 on every routed type, and on A1, A3, A4 and A5 on the distance and room types. GF-1's tower passes A1; its A5 (i) fails on a config file the reader reads from the code tree. The clause definitions and the allowlist were refuted once by another model family (NO-GO, 16 defects); all 16 are fixed and tested, and the revised kit awaits a re-review.

## What it is (`eat1/`, file hashes in `work/EAT1_FILES.sha256`)
- `run.py` wraps any reader that exposes `generate(frames, question)` and judges A1–A5. It writes A6 per type: call rate, the heads behind each response field, and seconds per item. Options: `--sandbox` (A5 i: bwrap rerun with every outside directory unmounted), `--perturb [--perturb-limit N]` (A5 ii), `--strace-log`.
- `hook.py`: an audit hook on file opens plus `/proc/self/maps` windows (A1). It also holds the model monitor, which counts model entries and classifies every fed token as prompt, model argmax, registered-handler output or injected (A2). It accepts a split LM entry (model.model + lm_head). Line scope covers reader lines executed outside module forwards (A3/A4 scope).
- `scan.py` + `allowlist.json` form the static scanner: table loads, data-file names, numeric constants, thresholds, unit conversion, guards, status literals, except-substitutes, caches, and responses written outside a module. `closure.py` computes a reader's static import closure.
- `artifact.py` holds the `eat1-artifact-v1` manifest: files by sha256 and role, and modules by path and role.
- `adapters/`: `c8r_tiny.py` and `gf1_tiny.py` (tree tiny fixtures, CPU), `b04_tiny.py` (lane b04's end-to-end reader on its tiny kit, CPU; result `out/EAT1_ON_B04_TINY.md`: A1, A2 and A5 PASS, A3 and A4 FAIL) and `c8r_native.py` (the real C8r no-MDG reader, GPU, untested).
- `toy/` holds the clean toy reader plus six planted violations (the brief's five plus a threshold hidden in a head-class method). `toy/adversarial.py` holds the review's 21 planted variants plus two clean ones. `tests/test_eat1.py` has 23 tests; the latest run is `Ran 23 … OK` in 81 s (`work/test_run_10.log`). Run: `cd L && EAT1_TMP=$L/work/tmp /scratch/jjyeung/envs/p1cpu/bin/python -m unittest eat1.tests.test_eat1`.

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

## Rules after the cross-family refute review (Codex gpt-6-astra, NO-GO, `events/b03_e2etest/REVIEW_VERDICT_EAT1.md`)
All 16 defects are fixed, each with a planted variant in `eat1/toy/adversarial.py` that fails its clause for its planted reason (`Adversarial` tests); `memo` and `numeric` pass every clause. Tests: `Ran 23 … OK` (`work/test_run_10.log`). The rules now in force, against the user's wording:
1. A3 fixed math: unprojection, rigid transforms, norms, min/argmin and printing head outputs with `str()`. Any precision choice (`round`, `.round`, format specs, `%.2f`) fails `A3.reformat` ("number formatting is done by the MODEL"); allowlist switch `format_precision` (false). Constant-only expressions and multiplicative or additive chains are folded (`(2+3)**2`, `x*4*25`, `k = 4; x*k*k`) and fail outside the allowlist. Integer shape arguments of reshape-like calls are exempt.
2. `if <test>: raise` validation stays exempt; an item that raises fails A4 (`reader_error`).
3. No class exemption: every executed line of reader code, including head forwards and head methods, is judged. Constants in model code pass only when listed in `declared_constants` (file, function, value, reason) for review; a fitted multiplier must be a weight.
4. A cache passes A5 (iii) only with an `eat1-cache-proof-v1` of at least 50 equal live/cached items; its sites are listed and the report sets `claim_needs_live_run`.
5. A1: a tower pinned by sha256 in the manifest is inside the artifact; A5 (i) must still pass.
6. A2: response tokens not written by a registered handler module are injected. The key-value cache must be unchanged between model entries (content fingerprint), so a rewritten prompt fails.
7. Every except-handler that does not re-raise fails A4 (`A4.except_substitute`), empty returns included; `x or <numeric literal>` fails `A4.or_fallback`.
8. Response text formatted by a function the handler calls passes A2 when provenance shows zero injected tokens; A3 still judges that function.
9. A5 (ii): a perturbed run that raises fails; calls that diverge before any response naming the target fail; a target named in the baseline needs at least one eligible comparison.
10. Module and class bodies run by lazy imports are in scope, and module-level numbers or tables that executed functions read fail `A3.module_data`.
Further fixes: thresholds include comparisons against attributes, constant expressions, any number but 0 and ±1, and comparison or clamp APIs (`torch.gt`, `clamp`); artifact files of role `config` read during generate() fail `A3.table_load`, as do `read_text`/`JSONDecoder` loads; A1 counts `O_RDWR` and `r+` opens as reads, mmaps of descriptors, moved positions of descriptors opened before generate(), child processes and ctypes symbol lookups from reader code; A4 requires the answer as a whole token run after the last response; A6 reconciles reported calls with the responses the handler wrote (a new clause status); the A5 (i) sandbox mounts code roots file by file, code files only; native units a head itself predicts can be declared in `native_units`. A claimed PASS needs `claim_grade` true (strace, sandbox and perturbation all ran).

## Baselines under the revised kit
Static: C8r 1035 findings in 45 files (`work/c8r_static/SCAN_TIER1_v3.json`), b5 tree 632 in 33 (`work/nextleg/static/SCAN_READ_v3.json`). Tiny runs `work/c8r_tiny/run9`, `work/b5_tiny/run4`: A2, A3, A4, A6 FAIL, A1 and A5 PASS. GF-1 `work/b5_gf1_tiny/run7`: A2, A3, A4, A5, A6 FAIL; A5 (i) now fails because the reader reads `configs/gf1_stage1.json` from the code tree, which the claimed artifact must carry. The b04 tiny rerun waits: b04's reader refuses its kit because b04 changed `e2e_reader/artifact.py` after the kit was built.
