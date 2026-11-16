# C8r CPU rehearsal

Run these commands from the build directory. They use the operator's Python outside the sandbox. All inputs and the C8 staging tree are read-only; destinations must be fresh and under this build's `work/`. The harness writes fixture authority, uses CPU boundary stand-ins and an offline GCS executable, and never authorizes a production run.

```bash
cd /scratch/jjyeung/orch_n30/native_r2/builds/02_c8r
export PYTHONPATH=/scratch/jjyeung/orch_n30/native_r2/work/np226:/scratch/jjyeung/orch_n30/native_r2/work/pyextra
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
export XDG_CACHE_HOME=$PWD/work/cache HF_HOME=$PWD/work/hf TRITON_CACHE_DIR=$PWD/work/triton
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
nice -n 10 /scratch/jjyeung/envs/vllm/bin/python -I -s -B out/rehearsal/run_rehearsal.py --mode pilot --shards 1 --dest "$PWD/work/rh_pilot_operator" > work/rh_pilot_operator.log 2>&1
nice -n 10 /scratch/jjyeung/envs/vllm/bin/python -I -s -B out/rehearsal/run_rehearsal.py --mode full --shards 1 --dest "$PWD/work/rh_full_operator" > work/rh_full_operator.log 2>&1
```

The sharded command is explicit and fails before staging for N above one. `out/SHARDING.md` explains why the production interface cannot provide the requested shard semantics without a production change. The command does not silently start a serial run.

```bash
N=15
nice -n 10 /scratch/jjyeung/envs/vllm/bin/python -I -s -B out/rehearsal/run_rehearsal.py --mode full --shards "$N" --dest "$PWD/work/rh_full_sharded" > work/rh_full_sharded.log 2>&1
```

Inside the sandbox, use the supplied Python executable. The recorded namespace refusal is `work/rh_pilot_01/RESULT.json`; do not repeat a blocked namespace operation without an environment change.

```bash
nice -n 10 /scratch/jjyeung/orch_n30/native_r2/env312/bin/python3.12 -I -s -B out/rehearsal/run_rehearsal.py --mode pilot --shards 1 --dest "$PWD/work/rh_pilot_sandbox"
```

`LIMITS.json` records the free-space check and storage budgets for each run. The harness enforces the build budget in bytes, keeps one serving process, and sets PyTorch CPU threads to one. Production validators, geometry, binding, serving, merge, admission, report writing, terminal receipts and the return-chain APIs execute unchanged; only the documented CPU and transport boundaries use fixtures. The exact new receipt must reproduce byte-for-byte.

The harness uses coverage parallel data filenames and invokes `Coverage.combine(keep=True)` after the run, preserving process files. It records that merge in `RESULT.json`. An equivalent explicit combine command is:

```bash
nice -n 10 /scratch/jjyeung/orch_n30/native_r2/env312/bin/python3.12 -I -s -B -c 'import sys;sys.path.insert(0,"/scratch/jjyeung/orch_n30/native_r2/work/pyextra");from coverage.cmdline import main;sys.exit(main())' combine --keep --data-file=out/coverage/full/.coverage out/coverage/full
```

Run the final coverage gate after both rehearsals. The script accepts SQLite coverage data or JSON. Its output names each missed line and its classification, and fails for uncovered changes or any missing full-worker/report/admission statement.

```bash
nice -n 10 /scratch/jjyeung/orch_n30/native_r2/env312/bin/python3.12 -I -s -B out/coverage/review.py --pilot out/coverage/pilot/.coverage --full out/coverage/full/.coverage --tests out/coverage/tests/.coverage
```

The review performed during this build uses the operator's C8 pilot evidence with explicit source mapping:

```bash
nice -n 10 /scratch/jjyeung/orch_n30/native_r2/env312/bin/python3.12 -I -s -B out/coverage/review.py --pilot ../01_c8/out/coverage/pilot/coverage.json --pilot-source ../01_c8/out/c8/sources/sj/orch_cd/evalx/work/milestone --tests out/coverage/tests/coverage.json
```

No full-mode completion is inferred from the independently running C8 job. No live GCS credential, Orchard quota, GPU, upload, or production packet was checked here.
