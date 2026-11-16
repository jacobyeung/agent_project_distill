# Rehearsal runbook

The whole-worker rehearsal is incomplete. `namespace.stderr` records the sandbox refusal; `records_pass/RESULT.json` explicitly marks the recorded-row run as a fixture with no model decode. It is not evidence that production CONFIG works with transport-only changes.

Run the completed local component checks with the required interpreter:

```sh
cd /scratch/jjyeung/orch_n30/b01_d0guard/guard_kit/build
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export XDG_CACHE_HOME="$PWD/work/cache" HF_HOME="$PWD/work/cache/hf" TRITON_CACHE_DIR="$PWD/work/cache/triton"
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/rehearsal/run_records.py --out out/rehearsal/operator_records
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/rehearsal/run_records.py --out out/rehearsal/operator_mismatch --mismatch
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_c8r_tests.py
```

Use fresh output destinations. The recorded-row run writes proof and canary receipts, merges only the native arm, verifies a local archive copy, and invokes the unchanged report on its fixture R1 against itself. The mismatch changes a reference token and must preserve PROOF while producing no candidate arm (`records_mismatch/RESULT.json`).

The supplied boundary stand-ins are at `/scratch/jjyeung/orch_n30/b01_d0guard/work/from113/builds/02_c8r/out/rehearsal/cpu_boundary.py`. Their numpy/scipy and extra import roots are `/scratch/jjyeung/orch_n30/b01_d0guard/work/from113/work/np226` and `/scratch/jjyeung/orch_n30/b01_d0guard/work/from113/work/pyextra`. Insert them explicitly under isolated Python. The completed C8r staging assets are at `/scratch/jjyeung/orch_n30/b01_d0guard/work/from113/builds/01_c8/work/rehearsal_assets/d03de829ae52386f`.

After the candidate training closure and production coordinator are implemented, an operator outside this sandbox must run stage, prepare, historical proof, candidate canary/read, merge, admission, publish, fetch and report using the same sealed production CONFIG. Only transport and the documented model boundaries may differ. Use separate checkpoint processes because the sealed guard installs once.

There is no complete G1 whole-worker command to give yet. Reusing C8r's old harness unchanged would alter CONFIG and exercise its paired workflow; it would not satisfy this task. The namespace failure is only one blocker, not the reason to claim that missing integration is complete.
