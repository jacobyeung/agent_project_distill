# F1 facing-family admission

R1 runs `673bc60f` and `05b8ac69` accept every non-empty subset of `main`, `away`, `forward`, and `a7`, with `--types direct` or no filter. Omitting `--families` selects all four. Empty selections, duplicates, unknown families and unknown filters remain invalid. Run `469ddece` still accepts only `a7` at its registered mstop/544 boundary.

The facing CLI fixtures pass all three validators, preserve the reader payload, and retain the required main+a7 plan hash. **The complete regression requirement is not satisfied by this supplied folder and environment.** It contains inactive r6 additions and lacks historical fixture directories required by inherited tests. Protected asset modes, external test dependencies and the local model-space floor also prevent complete validation. The seal authenticates these files; it does not certify that every suite passed.

## Decisions and scope

- The physical workspace and `/scratch/jjyeung/orch_n30/cont_ops/work/h1face` resolve to the same folder. All work used this folder; the operator examples use its sealed alias.
- Remove the two redundant R1 restrictions and use the existing four-family validator. Keep the independent step-544 restriction intact.
- Use `--types direct` for both facing fixtures and operator preparation because it retains every twin.
- Preserve all supplied reader files, including the inactive r6 files. Do not add r6 admission or rewrite missing historical evidence to obtain passing tests.
- Use the requested interpreter. It reports **Python 3.12.13**, rather than 3.6. Changed Python files pass a Python 3.6 grammar check. A Python 3.6 runtime was not tested; inherited tooling uses newer APIs such as `sys.addaudithook` and `hashlib.file_digest`.
- Run tests through `tools/test_fix3.py`, which confines writes and ledgers to `evidence/test_*`. Its additional read guard prevents inherited r6 tests from opening sibling kits or external source data. The seal walker prunes `build` before traversal.

No network, SSH, Slurm, GPU, Git, deletion, production preparation or submission ran. No protected hardlink was written. The only changed file from the inherited checksum manifest under `kit/` is `kit/launcher/orchard_launcher.py`. All **74 registered reader files** retain their fix-6 digests; all **76 reader files present at task start**, including `c6.py` and `r6.py`, retain their bytes. Binding, staging, transport, evaluator, scorer, assets, inventories and return pool remain unchanged.

## Changed lines

| File | Lines | Change |
|---|---|---|
| `kit/launcher/orchard_launcher.py` | Original 166–167 and 204–205 | Remove the two R1 main/a7-only checks; retain the common four-family checks and step-544 a7-only checks. |
| `tests/test_fix6.py` | 8, 180–201 | Cover all 15 non-empty subsets for both R1 runs and both filter settings, the four-family default, reversed ordering, and invalid selections. |
| `tests/test_f1.py` | 1–65 | Add population, exact payload equality and step-544 refusal tests. |
| `tools/test_fix3.py` | 21, 50–55, dispatch table | Add the F1 suite and refuse external kit reads and production-build access. |
| `tools/verify_f1.py` | Entire new file | Capture authentic fix-6 CLI baselines before changing the launcher; validate paired F1 fixtures and record exact differences. |
| `tools/seal.py` | 5, 15–20, 35, 67–76 | Prune build directories, pin F1 evidence and exclude pending logs during pre-seal. |
| `evidence/FIXF1_OPERATOR_COMMANDS.sh` | Entire new file | Record the prepare, submit, fetch and unpack commands; syntax-check without execution. |
| `DIFF.md`, `DIFF.patch`, `evidence/FINAL_PINS.json`, `SHA256SUMS.txt` | Generated files | Rebuild through the kit's own sealing tool. |
| `FIXF1.md`, `evidence/FIXF1_*` | New report and evidence | Record decisions, fixture identities, test outcomes and seal verification. |

## Direct-filter population

`read_filter.F.population` receives one `question_type` row per item in `kit/reader/e193_items.json`, exactly as launcher preparation does. `direct` excludes only `object_abs_distance` and `room_size_estimation`.

| Family | Source items | Easy | Medium | Hard | Kept | Removed |
|---|---:|---:|---:|---:|---:|---:|
| away | 150 | 50 | 50 | 50 | 150 | 0 |
| forward | 150 | 50 | 50 | 50 | 150 | 0 |

The full type names are `object_rel_direction_easy`, `object_rel_direction_medium` and `object_rel_direction_hard`. For each family, the returned population is `items=150`, the three type counts are 50, `excluded={}`, and `rooms_with_items=null` because this inventory supplies types without room identifiers. The filtered and unfiltered population dictionaries are equal. Neither family is dropped or refused. `evidence/FIXF1_AUDIT.json` records both dictionaries.

## Fixture and payload proof

The baseline command ran against the unchanged fix-6 launcher, whose source is preserved in `evidence/FIXF1_BEFORE_orchard_launcher.py.txt`. `evidence/FIXF1_BEFORE_SHA256SUMS.txt` retains the inherited fix-6 manifest; `evidence/FIXF1_BEFORE_PINS.json` retains the supplied, different FINAL_PINS file. Baselines reside under `evidence/test_f1_baseline/`.

```bash
PY=/scratch/jjyeung/envs/p1cpu/bin/python
# Executed before the launcher edit:
"$PY" -B tools/verify_f1.py baseline > evidence/FIXF1_BASELINE.log 2>&1
# Executed after the launcher edit:
"$PY" -B tools/verify_f1.py verify > evidence/FIXF1_FIXTURES.log 2>&1
```

Both commands call the actual launcher CLI entry point with `--run 673bc60f --namespace 8865619b --step 200 --types direct`. The baseline uses `--families main a7`; verification uses the selections below. Each pair uses the same token because the token appears in payload member paths. Tokens were never submitted. The facing and all-family cases use newly generated tokens; the plan check uses the mandated token.

| Destination | Token | Families | Request / payload / batch validation |
|---|---|---|---|
| `evidence/test_f1_plan` | `a8102c3207b` | main a7 | PASS / PASS / PASS |
| `evidence/test_f1_twins` | `a64ab7ce8b6` | away forward | PASS / PASS / PASS |
| `evidence/test_f1_all` | `ae91ced2eb6` | main a7 away forward | PASS / PASS / PASS |

The main+a7 plan hash is identical before and after the edit:

```text
9fc9d1f6cbe29421d87abe0a8f47c85c934900205adc21b7ccd21a6824423a54
```

For each pair, the compressed payload bytes, all 13 payload member pins and `payload_sha256` are exactly equal. The same-family main+a7 CONFIG differs only in `launcher_pins`, `launcher_review` and its authentication field `launcher_review_pin`. Only `orchard_launcher.py` changes within `launcher_pins`.

The facing and all-family CONFIGs also necessarily differ in `families`, `spec` and `plan_sha256`: within `spec`, only `families` and `population` differ. Their payloads remain identical to their same-token fix-6 main+a7 baselines. Whole-CONFIG equality across different family selections would be incorrect. Exact hashes and difference lists appear in `evidence/FIXF1_FIXTURES.log` and `evidence/FIXF1_AUDIT.json`.

## Regression commands and outputs

The following commands ran sequentially. Each suite's complete output remains in its named log. No assertion was removed or skipped to conceal a supplied-kit failure.

```bash
PY=/scratch/jjyeung/envs/p1cpu/bin/python
"$PY" -B tools/seal.py --pre-test > evidence/FIXF1_PRESEAL.log 2>&1
for suite in f1 candidate fix6 fix5 fix4 targeted ported reference refute runtime runtime_direct; do
  "$PY" -B tools/test_fix3.py "$suite" > "evidence/FIXF1_${suite^^}.log" 2>&1
done
```

| Suite | Result | Output | Full log |
|---|---|---|---|
| f1 | 3/3 pass | `Ran 3 tests; OK` | `evidence/FIXF1_F1.log` |
| candidate | 123/136 pass | `Ran 136 tests; FAILED (failures=2, errors=11)` | `evidence/FIXF1_CANDIDATE.log` |
| fix6 | 4/7 pass | `Ran 7 tests; FAILED (failures=1, errors=2)` | `evidence/FIXF1_FIX6.log` |
| fix5 | 5/6 pass | `Ran 6 tests; FAILED (errors=1)` | `evidence/FIXF1_FIX5.log` |
| fix4 | 9/10 pass | `Ran 10 tests; FAILED (errors=1)` | `evidence/FIXF1_FIX4.log` |
| targeted | 7/7 pass | `Ran 7 tests; OK` | `evidence/FIXF1_TARGETED.log` |
| ported | 53/53 pass | `Ran 53 tests; OK` | `evidence/FIXF1_PORTED.log` |
| reference | 52/53 pass | `Ran 53 tests; FAILED (errors=1)` | `evidence/FIXF1_REFERENCE.log` |
| refute | 4/4 pass | `Ran 4 tests; OK` | `evidence/FIXF1_REFUTE.log` |
| runtime | Blocked before completion | `ValueError: Model space floor` | `evidence/FIXF1_RUNTIME.log` |
| runtime_direct | Blocked before completion | `ValueError: Model space floor` | `evidence/FIXF1_RUNTIME_DIRECT.log` |

The candidate discovery run covers every `tests/test_*.py` module, including `tests/test_fixv1.py`. It reports `Ran 136 tests` and `FAILED (failures=2, errors=11)`: 123 tests pass, with no skips. The expanded FIX6 family-gate test passes all 68 accepted preparations (15 subsets, default and reversed main/a7 ordering, across two R1 runs and two filter settings). It also rejects 20 invalid selections through both preparation and embedded request validation, plus invalid filters.

The unresolved failures are concrete:

| Cause | Evidence and affected checks |
|---|---|
| Missing historical fixtures | FIX4 needs `evidence/test_fix3_targeted_a738cb8e2831495493f913ce23192669/.../CONFIG.json`; FIX5 needs `evidence/test_fix3_fix4_5281c79473cf4f04b58e160c9d2dd9f8/.../CONFIG.json`; two FIX6 checks need `evidence/test_fix6_baseline/CASES.json`. None is supplied here. |
| Inactive r6 additions | `kit/reader/c6.py` and `r6.py` make the unchanged exact 74-file inventory assertion fail. Seven `test_fixv1` cases fail or error because the four-family launcher and return inventory do not implement r6, or because their references lie outside this folder. Adding r6 would violate F1's requested scope and step-544 restriction. |
| Protected asset modes | Both `assets/d81f4a26.tar` and `assets/e52a690b.jsonl` are hardlinked files with mode `0400`. The unchanged `x7.stage_assets` requires `0600`, so the successful-local-staging test refuses. Changing their mode would modify the shared protected inode. |
| External reference dependency | The original reference suite requests `/scratch/jjyeung/orch_n30/trin_read/build_t5/milestone.py`; the scope guard refuses that read. The r6 suite similarly requests a sibling h1read kit and external source items. |
| Model-space floor | Both isolated runtime fixtures stop at the unchanged `x7.py` check with `ValueError: Model space floor`; neither completes its item loop. The guard requires 200 GiB plus its model reserve. `evidence/FIXF1_AUDIT.json` records observed local free space. |

The first ported-suite pass encountered a stale pre-seal digest for `tools/seal.py` while evidence registration was being finalized. Its output is retained in `evidence/FIXF1_PORTED_PRESEAL.log`. After source files were fixed and the pre-seal refreshed, the ported suite was rerun; the table reports that completed run. Final pin validation separately checks the final manifest. No protected file, reference test or production reader was changed to suppress these failures.

## Operator commands

These commands are recorded in `evidence/FIXF1_OPERATOR_COMMANDS.sh` and pass `bash -n`; they were **not executed**. Resolve the regression limitations above before treating this kit as fully validated. Use the pinned uploads from `UPLOAD_PLAN.md`, a completed R1 m200 export receipt and an authorized allocation. The destination stays outside `kit/build`.

```bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1face
export PYTHONDONTWRITEBYTECODE=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
L=$PWD/kit/launcher/orchard_launcher.py
export A_TRANSPORT=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
TOKEN=a$("$PY" -B -c 'import uuid; print(uuid.uuid4().hex[:10])')
R1_READ=$PWD/evidence/operator_f1_$TOKEN
"$PY" -B "$L" prepare --run 673bc60f --namespace 8865619b \
  --step 200 --families away forward --types direct \
  --token "$TOKEN" --destination "$R1_READ"
CMD=$("$PY" -B "$L" submit-command --destination "$R1_READ")
timeout 300 bash "$A_TRANSPORT" "$CMD" < "$R1_READ/BATCH.sh" \
  > "$R1_READ/SUBMIT.out" 2> "$R1_READ/SUBMIT.err"
"$PY" -B "$L" record-submission --destination "$R1_READ"
```

After completion, keep the same token and destination. In a new shell, restore `PY`, `L`, `A_TRANSPORT` and `R1_READ`.

```bash
"$PY" -B "$L" fetch --destination "$R1_READ"
# For returns >=20 MB, register the printed transfer command with the
# IO governor and execute it once before unpacking.
"$PY" -B tools/unpack_return.py --destination "$R1_READ"
```

The facing read supplies 300 direction items for comparison against the corresponding step-544 e193 facing read. This task did not inspect that completed return or establish pairing against it. The launcher's `469ddece` route remains a7-only; these commands do not generate a facing baseline through that route. Authenticate the actual baseline's family IDs and inventory before interpreting a comparison. Facing results alone do not supply the main+a7 populations required by the pooled-rule workflow in FIX6.md. Continuation `05b8ac69` retains FIX6's separate registration limitation for pooled decisions.

## Expected runtime

FIX6.md reports 1,781 a7 items in 768.974 seconds of chain time and approximately 251 seconds of other wall time. At that observed average rate, each 150-item facing family takes `769 × 150 / 1781 ≈ 64.8 seconds`; both take **129.5 seconds of chain time**. Reusing the 251-second overhead gives **380.5 seconds, or about 6.4 minutes**, after allocation. Allow roughly **10–15 minutes** for planning because prompt lengths and frame staging can differ; queue time is additional. This is an extrapolation, not a measured facing runtime. The existing six-hour allocation remains unchanged.

## Seal

```bash
"$PY" -B tools/seal.py > evidence/FIXF1_SEAL.log 2>&1
"$PY" -B tools/test_fix3.py pins > evidence/FIXF1_FINAL_PIN_TEST.log 2>&1
sha256sum -c SHA256SUMS.txt > evidence/FIXF1_SHA256_CHECK.log 2>&1
```

`evidence/test_*` remains excluded. The seal pins the bounded F1 audit, baseline/fixture logs, suite logs and operator script. FIXF1.md and post-seal logs stay outside the manifest to avoid circular hashes. The final pin test passes (1/1), and all 249 checksum entries verify. FINAL_PINS SHA256 is `ebffd1661161dc38f812cf1f519d5890b987bfced90695cbdf5a967fdb107b04`; SHA256SUMS.txt SHA256 is `cfaa8833750976c73a4f6e3bfcbbb953f6f56219fa70daffed3c19bb30053de8`. The seal reports 52 changed text files relative to readk; that count includes inherited changes and is not the number changed by F1.

## Final report — 15 lines

1. R1 now accepts every non-empty subset of main, away, forward and a7 with direct or no filter.
2. Run 469ddece remains a7-only, and unknown families remain invalid.
3. The direct filter retains all 150 away items and all 150 forward items.
4. All three CLI fixtures pass request, payload and batch validation; all 74 registered reader files remain unchanged.
5. The main+a7 plan remains 9fc9d1f6cbe29421d87abe0a8f47c85c934900205adc21b7ccd21a6824423a54.
6. The new F1 suite passes 3/3 tests, and the expanded R1 gate test passes 68 accepted preparations.
7. Candidate discovery passes 123/136 tests, with 2 failures and 11 errors; no tests are skipped.
8. FIX6 passes 4/7, FIX5 5/6, FIX4 9/10, targeted 7/7, ported 53/53 and refute 4/4 tests.
9. Reference tests pass 52/53; both runtime fixtures stop at the unchanged model-space floor.
10. Missing fixtures, incompatible r6 additions, external references and protected 0400 asset modes prevent full regression validation.
11. No protected file or production build was changed, and no read was submitted.
12. The final pin test passes 1/1, and all 249 checksum entries verify; evidence/test_* stays excluded.
13. FINAL_PINS.json SHA256 is ebffd1661161dc38f812cf1f519d5890b987bfced90695cbdf5a967fdb107b04.
14. SHA256SUMS.txt SHA256 is cfaa8833750976c73a4f6e3bfcbbb953f6f56219fa70daffed3c19bb30053de8.
15. This kit is not fully release-validated; confirm complete matched e193 facing returns before interpreting a read.
