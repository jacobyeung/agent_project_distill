# Isolated workers and partial diagnostic returns

The worker imports `read_filter` after adding its own directory to `sys.path`. The exact local reproduction, `/scratch/jjyeung/envs/p1cpu/bin/python -I -B kit/reader/worker.py --help`, now exits 0. The partial packer returns diagnostic tails so an early worker failure can carry its traceback home.

Eight production files change. The import changes establish local module paths without changing evaluation or admission behavior. Chain and job entry points already inserted their directories before local imports. The report inserts its vendor directory; its adapters establish the evaluator path before importing mergers. Evaluator, direct wrapper, adapter and export-checker bytes remain unchanged. `evidence/FIX5_AUDIT.json` records the per-module audit and 62 unchanged pinned runtime files.

| File and current lines | Change |
|---|---|
| `kit/reader/worker.py:13–17` | Import `read_filter` after the existing path insertion. |
| `kit/reader/x7.py:17–18` | Establish the reader path before deferred selector and records imports. |
| `kit/reader/paired_read.py:10–11` | Establish the reader path before importing `trinity_read`. |
| `kit/launcher/trace_runtime.py:12` | Establish the bootstrap path before the deferred results import. |
| `kit/launcher/orchard_stage.py:13–17` | Establish the bootstrap path before `chain_save`. |
| `kit/launcher/orchard_results.py:13–14` | Establish the bootstrap path before `chain_save`. |
| `kit/launcher/export_stage.py:15–21` | Establish the bootstrap path before local launcher imports. |
| `kit/launcher/chain_save.py:16,100–112,128,223–280` | Retain bounded log tails and record their offsets and retention metadata. |
| `tests/isolated_fixture.py:19,44,59` | Unpack a prepared payload; run guarded isolated CPU children. |
| `tests/runtime_fixture.py`, `tests/test_chain.py`, `tools/test_fix3.py`, `tests/offline_guard.py` | Run runtime and chain fixtures through the generated wrapper form; permit only exact validated local test commands. |
| `tests/test_fix5.py:25,35,53,85,113,128` | Add six isolation, plan and log-recovery regressions. |
| `tools/seal.py`, `REPORT.md`, `evidence/INTENDED_PORTS.md` | Seal new evidence and describe current behavior. |

The fixture wrapper keeps the production form `exec <python> -I "$@"`; only its interpreter path changes to the local CPU interpreter. A small guarded harness uses `runpy` to load the target without adding its directory to `sys.path`. Each of the 20 Python files in the unpacked bootstrap and payload imports in a fresh process. CLI entry points also pass `--help`. A negative control restores FIX4's broken worker import order in a test copy and verifies that the runtime fixture rejects it before installing mocks or extracting frames.

The runtime fixtures execute the packaged outer worker and actual evaluator, both budget derivations and mergers. They complete four unfiltered items and three direct-filter items. Engine, model staging and parity probes remain mocks. Chain success and failure tests use real isolated processes and import the actual packaged worker, then synthesize family results. These are offline CPU interface tests, not GPU parity or live cancellation tests.

Partial returns include `logs/launcher_chain.log`, `logs/launcher_staging.log` and each selected family's `.hex` file when available. Each file receives at most its last 256 KiB, reduced to fit the remaining archive budget. Identity, journals and metadata take priority. The packer reads only a bounded suffix and preserves complete lines, discarding a cut first line and an unfinished final line. A line larger than the available tail can be omitted entirely. `PARTIAL.json` and `SUMMARY.json` record original bytes, retained bytes and lines, offsets, truncation and omissions. The production cap remains below 89.9 MB and the proof cap below 19.9 MB. No diagnostic space is reserved at the expense of journals.

Both fixed-token step-544 preparations reproduce retained FIX4 plan bytes and `plan_sha256` exactly:

| Preparation | Canonical plan bytes | plan_sha256 |
|---|---:|---|
| Unfiltered a7 | 1,267 | `29313b5d5ad1c630e1264610bbd01e580c16dd95930c68d9864e143503b80176` |
| Direct-filter a7 | 1,704 | `29956194232e504cb1448c7f1d00adade4a5bd2a7ad56a8500d2adbd81f8941f` |

The comparison uses token `a000000001` and the retained fixture paths recorded in `evidence/FIX5_AUDIT.json`. Exactly five CONFIG fields change: `payload_pins`, `payload_sha256`, `launcher_pins`, `launcher_review`, and `launcher_review_pin`. All other fields match. A fresh operator token changes the plan's token-derived paths as usual.

| Validation | Result | Evidence |
|---|---|---|
| Candidate suite | 117/117 pass | `evidence/FIX5_TESTS.log` |
| FIX5 regressions | 6/6 pass | `evidence/FIX5_NEW_TESTS.log` |
| FIX4 regressions | 10/10 pass | `evidence/FIX5_FIX4_TESTS.log` |
| Step-544 admission | 7/7 pass | `evidence/FIX5_TARGETED.log` |
| Ported readk suite | 53/53 pass | `evidence/FIX5_READK_PORTED.log` |
| Original reference suite | 53/53 pass | `evidence/FIX5_READK_REFERENCE.log` |
| Reviewer refute suite | 4/4 pass | `evidence/FIX5_REFUTE.log` |
| Unfiltered isolated runtime | 4 items pass | `evidence/FIX5_RUNTIME.log` |
| Direct isolated runtime | 3 items pass | `evidence/FIX5_RUNTIME_DIRECT.log` |

REPORT.md contains the exact validation and sealing commands. All fixtures are under `evidence/test_*`; validation logs and audit files are retained in `evidence/`. No file in `kit/build/` was modified. No network, SSH, Slurm, GPU, Git or deletion operation was performed. No production preparation or submission was executed. FIX5.md and post-seal verification logs remain outside the manifest to avoid circular hashes.

The following operator commands prepare a fresh-token filtered step-544 a7 read. They were not executed. Use the pinned assets and permissions in UPLOAD_PLAN.md and an authorized allocation.

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
  --step 544 --generation mstop --families a7 --types direct \
  --token "$TOKEN" --destination "$STEP544"

CMD=$("$PY" -B "$L" submit-command --destination "$STEP544")
timeout 300 bash "$A_TRANSPORT" "$CMD" < "$STEP544/BATCH.sh" \
  > "$STEP544/SUBMIT.out" 2> "$STEP544/SUBMIT.err"
"$PY" -B "$L" record-submission --destination "$STEP544"
```

After the job ends, fetch the same destination. In a new shell, restore `STEP544` to the directory created above; do not generate a new token for fetch.

```bash
"$PY" -B "$L" fetch --destination "$STEP544"
# For an archive >=20 MB, fetch retains EXIT.json and prints the exact transfer
# command. Register that stream with the IO governor and execute it once.
"$PY" -B tools/unpack_return.py --destination "$STEP544"
```

The final manifest test passes, and all 203 checksum entries verify. Evidence: `evidence/FIX5_FINAL_PIN_TEST.log`, `evidence/FIX5_SHA256_CHECK.log` and `evidence/FIX5_SEAL.log`.

- FINAL_PINS SHA256: `f8911c19041a6bdb3bdf4734e2841a96fd7364675f202ddd0efabc5bc0d9203a`.
- SHA256SUMS.txt SHA256: `baf635b907e1f787aa58308ac5ec1098fac9f8be978823a3c2a844beee12eb4a`.
