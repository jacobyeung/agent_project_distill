# Step-544 R0-dev read

Run `469ddece` accepts exactly namespace `8865619b`, generation `mstop`, optimizer step 544 and family `a7` (2,169 items). Other identities for that run refuse. The claim must contain exactly `m544\n`.

The binding uses:

- Receipt: `/project/community/jjyeung/okh7/x_07ca49df/o/gcs_469ddece_m544.done`.
- Claim: `/project/community/jjyeung/okh7/x_07ca49df/o/gcs_469ddece_mstop.claim`.
- Object: `gs://cmu-gpucloud-jjyeung/q8/8865619b/469ddece_mstop.tar`, with ordered suffixes `.part00-of-04` through `.part03-of-04`.
- Supplied whole-tar receipt: 21,583,032,320 bytes; SHA256 `3ed73aead82cb0bb6468321256ea25e8fdaa5a2963da31062fdf8874bda2d4c7`.
- Supplied artifact SHA256: `1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef`.

The export facts above come from the operator. No remote receipt, claim, archive or tensor was accessed. The job still requires four complete parts, the whole-tar size and digest, safe archive members, the m544 directory, artifact step 544, the original absolute weights path, full shard hashes and native tensor compatibility. No checker was weakened. A miniature step-544 export passes the actual full checker locally; the supplied production artifact must pass admission when the operator runs the job.

## Changed lines

| File | Lines | Change |
|---|---|---|
| `kit/launcher/binding.py` | 6, 10–11, 16 | Register the deployment and admit only mstop/544; preserve prior identities, refusals and messages. |
| `kit/launcher/export_stage.py` | 42–43, 87 | Admit the exact m544 artifact path and run/step pair. Keep `T.EXPORT_RUNS` and `parse_done` unchanged so legacy unclaimed 469ddece receipts still refuse. |
| `kit/launcher/orchard_launcher.py` | 160–161, 196–197 | Require exactly `['a7']` in preparation and submitted-request validation for this run. |
| `tests/test_fix3.py` | Entire new file | Seven tests cover the supplied identity, refusal cases, CLI preparation, embedded bootstrap, reader parity, ordered parts, whole-tar checks and full miniature admission. |
| `tests/test_h1read.py`, `tests/test_kit.py` | Milestone loops and admission comparisons | Preserve D0/H1 milestone assertions; compare the admission function to the reference after normalizing only its explicitly added run/step gate. |
| `tools/test_fix3.py` | Entire new file | Run the existing suites with fixtures and test ledgers confined to `evidence/test_*`; retain the offline guard and block writes elsewhere. |
| `tools/seal.py` | Manifest evidence and exclusions | Pin FIX3 evidence, exclude pending suite logs during pre-sealing, and exclude this post-seal receipt to avoid circular hashes. |
| `REPORT.md`, `evidence/INTENDED_PORTS.md`, `DIFF.md`, `DIFF.patch` | Scope, validation and generated diff | Describe the closed identity and current validation. |

`evidence/FIX3_AUDIT.json` verifies that only the three launcher files changed among previously pinned kit files. All 73 pinned reader files remain unchanged. The new preparation has identical reader payload pins, asset registration and runtime assets to fresh D0 m200, D0 m100 and H1-1 m100 preparations. This preserves the items, prompts, 32-anchor `duplicate` layout, B2048/B4096 policy and scorer. Production preparations in `kit/build/*` were not modified.

## Test results and pins

| Check | Result | Evidence |
|---|---|---|
| Candidate suite | 101/101 pass | `evidence/FIX3_TESTS.log` |
| Ported readk suite | 53/53 pass | `evidence/FIX3_READK_PORTED.log` |
| Original readk suite | 53/53 pass | `evidence/FIX3_READK_REFERENCE.log` |
| Reviewer refute suite | 4/4 pass | `evidence/FIX3_REFUTE.log` |
| New step-544 tests | 7/7 pass | `evidence/FIX3_TARGETED.log` |
| Runtime integration | 4 items pass | `evidence/FIX3_RUNTIME.log` |
| Final manifest test | Pass | `evidence/FIX3_FINAL_PIN_TEST.log` |
| SHA256 manifest | 177/177 pass | `evidence/FIX3_SHA256_CHECK.log` |

The valid production-mode test preparation is `evidence/test_fix3_targeted_a738cb8e2831495493f913ce23192669/test_fix3_e9b77b5c8c1a44fd93d2dc2d7b0822d5/prepared/CONFIG.json`. It uses fixture token `a000000001` and was not submitted.

- Binding SHA256: `32dd8b51604d2bc4181e3e79e31b16e70c5c679e70006740c112379972d58b7d`.
- FINAL_PINS SHA256: `8cc3282a3f00acee8c699cfbf2236d6fb809f079eb4a219667aa25e99f1d4f37`.
- SHA256SUMS.txt SHA256: `f479ae1acba720aef5d4e0c64b9325b39c93efc9d0abf788cc7899ecb9304d5a`.
- Unchanged frame tar SHA256: `2ad8c67c111d5f286aa96ea688efd5c88218e116a8c09ae1a9b4bc71be893a21`.
- Unchanged item-file SHA256: `1d8b29a7f7bb5c4e486f430b1128b9fa249de24ae7a3905b9bb0ccdd778c892b`.

This file and post-seal verification logs remain outside the manifest, following the kit's receipt convention.

## Validation commands

Run from this kit. The wrapper selects the same candidate, ported, original-reference and refute suites listed in REPORT.md. It runs the original reference suite from `readk/` without editing its source or pins. Generated fixtures and preparation ledgers stay under `evidence/test_*`; logs below are final validation evidence. The old provenance audit is outside this task's directory boundary and was not rerun.

```bash
set -e
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
"$PY" -B tools/test_fix3.py targeted > evidence/FIX3_TARGETED.log 2>&1
"$PY" -B tools/test_fix3.py runtime > evidence/FIX3_RUNTIME.log 2>&1
"$PY" -B tools/seal.py --pre-test > evidence/FIX3_PRESEAL.log
"$PY" -B tools/test_fix3.py candidate > evidence/FIX3_TESTS.log 2>&1
"$PY" -B tools/test_fix3.py ported > evidence/FIX3_READK_PORTED.log 2>&1
"$PY" -B tools/test_fix3.py reference > evidence/FIX3_READK_REFERENCE.log 2>&1
"$PY" -B tools/test_fix3.py refute > evidence/FIX3_REFUTE.log 2>&1
"$PY" -B tools/seal.py > evidence/FIX3_SEAL.log
"$PY" -B tools/test_fix3.py pins > evidence/FIX3_FINAL_PIN_TEST.log 2>&1
sha256sum -c SHA256SUMS.txt > evidence/FIX3_SHA256_CHECK.log
```

## Operator prepare and submit

These commands are for the operator and were not executed. The already pinned assets and their permissions must satisfy UPLOAD_PLAN.md. Preparation requires a fresh token and destination; submission retains the existing queue, GPU, runtime, base-model, export and return-pool admission checks.

```bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1read
export PYTHONDONTWRITEBYTECODE=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
L=$PWD/kit/launcher/orchard_launcher.py
export A_TRANSPORT=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
TOKEN=a$("$PY" -B -c 'import secrets; print(secrets.token_hex(5))')
STEP544=$PWD/kit/build/$TOKEN
"$PY" -B "$L" prepare --run 469ddece --namespace 8865619b \
  --step 544 --generation mstop --families a7 \
  --token "$TOKEN" --destination "$STEP544"
```

After reviewing that preparation and confirming the allocation is authorized, submit once using the same shell variables:

```bash
CMD=$("$PY" -B "$L" submit-command --destination "$STEP544")
timeout 300 bash "$A_TRANSPORT" "$CMD" < "$STEP544/BATCH.sh" \
  > "$STEP544/SUBMIT.out" 2> "$STEP544/SUBMIT.err"
"$PY" -B "$L" record-submission --destination "$STEP544"
```

No network, SSH, Slurm, GPU, Git or deletion was used for this fix. No production preparation or submission was created.
