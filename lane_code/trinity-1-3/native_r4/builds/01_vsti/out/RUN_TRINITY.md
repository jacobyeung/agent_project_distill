The runner requires completed local assets. This build does not certify the production namespace or submit a job. `out/ASSETS.json` lists the expected sources; `out/UNEXECUTED.md` lists untested lines. Run on the assigned compute node, within the user's existing allocation and IO rules.

Use the build's interpreter wrapper for host preparation:

```bash
cd /scratch/jjyeung/orch_n30/native_r4/builds/01_vsti
./work/py code/entry.py adapt --items /scratch/jjyeung/orch_n30/native_r4/in/vsti/vstibench_repr_450_v3.json --media /scratch/jjyeung/orch_n30/native_r4/in/vsti/media.json --frames /scratch/jjyeung/orch_n30/native_r4/in/vsti/frames --out work/input --logical-root /i
./work/py -c 'from pathlib import Path; Path("work/input/SPEC.json").write_bytes(Path("out/SPEC.json").read_bytes())'
```

Stage the runtime, FLA and small metadata archives into a fresh local root. The expanded runtime exceeds this build's storage allowance, so this operator command uses a separate scratch root and a larger explicit staging allowance. It was not run during the build.

```bash
./work/py code/venue.py stage --assets out/ASSETS.json --root /scratch/jjyeung/orch_n30/r01_stage --budget 48000000000
./work/py code/venue.py plan --assets /scratch/jjyeung/orch_n30/r01_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01_run --gpu 0
```

The plan must report no missing paths. It invokes the host bwrap and wraps GPU execution with the required vnice script. Its shared-memory folder lives under the private root, never in host shared memory. The runner preserves the checkpoint's logical paths through read-only mounts. Additional preparation dependencies must be supplied if the original authenticated loader rejects them; this build has not established that closure.

For a single complete job, run the integrated path so the sealed deadline includes restoration and geometry:

```bash
./work/py code/venue.py run --assets /scratch/jjyeung/orch_n30/r01_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01_run --gpu 0 -- job --bound /i/BOUND.json --spec /i/SPEC.json --out /r/cell --limit 21600
```

For shared geometry and separate item shards, prepare geometry once and then decode:

```bash
./work/py code/venue.py run --assets /scratch/jjyeung/orch_n30/r01_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01_run --gpu 0 -- geometry --bound /i/BOUND.json --spec /i/SPEC.json --out /r/g
./work/py code/venue.py run --assets /scratch/jjyeung/orch_n30/r01_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01_run --gpu 0 -- run --bound /i/BOUND.json --spec /i/SPEC.json --geometry /r/g/scaled/GEOMETRY.json --out /r/j0 --shard 0/1 --limit 21600
```

A canary-only smoke run uses a fresh output:

```bash
./work/py code/venue.py run --assets /scratch/jjyeung/orch_n30/r01_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01_run --gpu 0 -- run --bound /i/BOUND.json --spec /i/SPEC.json --geometry /r/g/scaled/GEOMETRY.json --out /r/canary --canary-only
```

For several assigned cards, use a fresh pair of outputs with the same bound inputs and geometry. Start the second command after the first shard writes a passed CANARY receipt. Each command has its own journal. A separate canary-only run is diagnostic; shard zero still executes the canonical canary.

```bash
./work/py code/venue.py run --assets /scratch/jjyeung/orch_n30/r01_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01_run --gpu 0 -- run --bound /i/BOUND.json --spec /i/SPEC.json --geometry /r/g/scaled/GEOMETRY.json --out /r/s0 --shard 0/2
./work/py code/venue.py run --assets /scratch/jjyeung/orch_n30/r01_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01_run --gpu 1 -- run --bound /i/BOUND.json --spec /i/SPEC.json --geometry /r/g/scaled/GEOMETRY.json --out /r/s1 --shard 1/2 --canary-receipt /r/s0/CANARY.json
```

Merge and report on CPU inside the same namespace so absolute pins resolve. The CPU mode uses the specified interpreter and numerical overlay.

```bash
./work/py code/venue.py run --cpu --assets /scratch/jjyeung/orch_n30/r01_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01_run -- merge --bound /i/BOUND.json --out /r/MERGED.json /r/s0 /r/s1
./work/py code/venue.py run --cpu --assets /scratch/jjyeung/orch_n30/r01_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01_run -- report --merged /r/MERGED.json --out /r/report --comparators /scratch/jjyeung/orch_n30/native_r4/in/comparators/f17.per_question_scores.jsonl /scratch/jjyeung/orch_n30/native_r4/in/comparators/p1m200.per_question_scores.jsonl
```

For interrupted reads, add `--partial` to merge. It lists missing keys and suppresses the complete primary. Interrupted journals retain their last durable completion checkpoint. A partial merge authenticates only the committed byte prefix. It ignores an unfinished append and reports its uncommitted item as missing.

Historical proof preparation and GPU repeats use a separate root and the original assets:

```bash
./work/py code/proof_stage.py --root /scratch/jjyeung/orch_n30/r01_proof_assets --assets /scratch/jjyeung/orch_n30/r01_stage/ASSETS.json --family /scratch/jjyeung/orch_n30/native_r4/work/c8r/FAMILY.json --code /scratch/jjyeung/orch_n30/native_r4/work/c8r/code_c8r.tar --objects /scratch/jjyeung/orch_n30/native_r4/from113/work/obj --reference work/proof_reference.json --request work/proof_request.json --returned /scratch/jjyeung/orch_n30/native_r4/from113/work/full_c8r/result.tar.gz
./work/py code/venue.py run --assets /scratch/jjyeung/orch_n30/r01_proof_assets/ASSETS.json --root /scratch/jjyeung/orch_n30/r01_proof_run --gpu 0 -- proof --reference /i/REFERENCE.json --request /i/REQUEST.json --spec /i/SPEC.json --out /r/proof
```

The selected keys and their source are `out/PROOF_KEYS.json`. The proof writes both runs and PROOF.json; it checks the original adapters before decoding. Neither GPU command nor large staging command was executed in this build.
