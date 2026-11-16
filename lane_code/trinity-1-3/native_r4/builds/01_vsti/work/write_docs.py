from pathlib import Path
import ast
import sys
B=Path(__file__).resolve().parents[1];R=B.parents[1];sys.path.append(str(B/'code'))
from adapter import *

def line(file,name):
    tree=ast.parse((B/'code'/file).read_text())
    return next(n.lineno for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)

legal=f'''The read serves move, turn and pose through C8r's original response dispatcher and camera conversion. Every other recognized call, including unknown names, receives the fixed recoverable error response. The real decoder injects that response and continues.

- Dispatch policy: `code/policy.py:{line('policy.py','camera_only')}`; call records: `code/policy.py:{line('policy.py','records')}`.
- The inherited camera conversion is `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py:173`. It uses the prepared tower geometry, with no own-pose fallback for scored items.
- The tower reads the read's verified RGB frames: `code/engine.py:{line('engine.py','tower')}` and `code/adapter.py:{line('adapter.py','prepare')}`. The adapter verifies selection and PNG hashes, preserves frame ordinals and timing, and uses the same anchors as dense frames.
- The public frozen tower weight, configuration and revision identities are the constants in `from113/work/tree/student_pilot/tower_read.py:18`; their file paths and receipt are recorded by the tower phase. No tower weights are fitted by this build.
- The checkpoint loader authenticates the prepared configuration and checkpoint heads: `code/engine.py:{line('engine.py','NativeBoundary')}` and the unchanged `read_runtime.py`. Scale is estimated from tower depth and the checkpoint's own predicted depth on this read's images. Gravity comes from the checkpoint's own head. No answer labels enter either computation.
- The original scale conversion and reviewed gravity guard remain active: `code/engine.py:{line('engine.py','prepare_geometry')}`, `geometry.py:24`, and `gravity_guard.py:16`. A gravity refusal yields an explicit zero-score item with no decoded answer; it cannot silently disappear from the denominator.
- Prompt records contain no ground truth: `code/adapter.py:{line('adapter.py','prepare')}`. Labels live only in `SCORES.json`. The runtime builds prompts through the inherited trainer adapter.
- The production namespace binds only the new read inputs, the trainer tree, code, numerical libraries, frozen tower, base model and checkpoint preparation assets: `code/venue.py:{line('venue.py','trinity_plan')}`. It binds no old evaluation mask or geometry asset. Historical inputs are confined to the separate proof-stage runner.
- The proof runner deliberately restores the original inputs and serving policy for historical equality: `code/proof.py:{line('proof.py','run')}`. Its CPU comparator rehearsal is not evidence of GPU equality.

The headline includes the refusal-policy disclosure on its own line with the primary. The report also states: "only move, turn and pose are served, by frozen G3T run on this read's frames with step-544's own scale and gravity; every other call is refused".

Unchecked: real GPU prompt/cache/head parity, greedy decoding, the historical GPU repeat, full-corpus staging, and both remote return transports. The detailed line census is `out/UNEXECUTED.md`.
'''
(B/'out/LEGALITY.md').write_text(legal)
if '--legality-only' in sys.argv:raise SystemExit(0)
commands=f'''The runner requires completed local assets. This build does not certify the production namespace or submit a job. `out/ASSETS.json` lists the expected sources; `out/UNEXECUTED.md` lists untested lines. Run on the assigned compute node, within the user's existing allocation and IO rules.

Use the build's interpreter wrapper for host preparation:

```bash
cd {B}
./work/py code/entry.py adapt --items {R}/in/vsti/vstibench_repr_450_v3.json --media {R}/in/vsti/media.json --frames {R}/in/vsti/frames --out work/input --logical-root /i
./work/py -c 'from pathlib import Path; Path("work/input/SPEC.json").write_bytes(Path("out/SPEC.json").read_bytes())'
```

Stage the runtime, FLA and small metadata archives into a fresh local root. The expanded runtime exceeds this build's storage allowance, so this operator command uses a separate scratch root and a larger explicit staging allowance. It was not run during the build.

```bash
./work/py code/venue.py stage --assets out/ASSETS.json --root /scratch/jjyeung/orch_n30/r01_stage --budget 24000000000
./work/py code/venue.py plan --assets /scratch/jjyeung/orch_n30/r01_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01_run --gpu 0
```

The plan must report no missing paths. It invokes the host bwrap and wraps GPU execution with the required vnice script. Its shared-memory folder lives under the private root, never in host shared memory. The runner preserves the checkpoint's logical paths through read-only mounts. Additional preparation dependencies must be supplied if the original authenticated loader rejects them; this build has not established that closure.

Prepare geometry once, then decode the fixed canary and all remaining items:

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
./work/py code/venue.py run --cpu --assets /scratch/jjyeung/orch_n30/r01_stage/ASSETS.json --root /scratch/jjyeung/orch_n30/r01_run -- report --merged /r/MERGED.json --out /r/report --comparators {R}/in/comparators/f17.per_question_scores.jsonl {R}/in/comparators/p1m200.per_question_scores.jsonl
```

For interrupted reads, add `--partial` to merge. It lists missing keys and suppresses the complete primary. Interrupted journals retain their last durable completion checkpoint. An external interruption during a journal append can leave an unmatched tail; that tail currently requires operator review and is not silently accepted.

Historical proof preparation and GPU repeats use a separate root and the original assets:

```bash
./work/py code/proof_stage.py --root /scratch/jjyeung/orch_n30/r01_proof_assets --assets /scratch/jjyeung/orch_n30/r01_stage/ASSETS.json --family {R}/work/c8r/FAMILY.json --code {R}/work/c8r/code_c8r.tar --objects {R}/from113/work/obj --reference work/proof_reference.json --request work/proof_request.json --returned {R}/from113/work/full_c8r/result.tar.gz
./work/py code/venue.py run --assets /scratch/jjyeung/orch_n30/r01_proof_assets/ASSETS.json --root /scratch/jjyeung/orch_n30/r01_proof_run --gpu 0 -- proof --reference /i/REFERENCE.json --request /i/REQUEST.json --spec /i/SPEC.json --out /r/proof
```

The selected keys and their source are `out/PROOF_KEYS.json`. The proof writes both runs and PROOF.json; it checks the original adapters before decoding. Neither GPU command nor large staging command was executed in this build.
'''
(B/'out/RUN_TRINITY.md').write_text(commands)
(B/'out/rehearsal/RUNBOOK.md').write_text(f'''Nested bwrap was denied by the build sandbox; see `out/rehearsal/NAMESPACE.json`. The failure occurred while creating a network socket. No host shared-memory directory is bound.

The exact attempted namespace command is the `command` array in that file. To run the full CPU rehearsal outside the sandbox on the same compute node, use the same interpreter and overlays:

```bash
cd {B}
./work/py out/rehearsal/run_rehearsal.py --inner --dest {B}/work/rh_operator
```

Use a fresh destination. The script checks for the complete tower receipt. When present it attempts the real tower on CPU; otherwise it uses a pinned synthetic tower. Model loading, checkpoint depth/gravity predictions and sampled token logits remain CPU fixtures. Scale conversion, gravity guard, tool dispatch, error-response injection, replay, scoring, merge and reporting execute their production implementations.

The item source contains fewer sample-scene items than the brief states; `out/rehearsal/RESULT.json` and its bound input list record the actual membership. No synthetic benchmark item is added.

Unchecked: GPU restoration, prompt/pixel/cache parity, GPU generation and historical repeat equality. `out/UNEXECUTED.md` gives the executable-line census.
''')
(B/'out/RUN_ORCHARD.md').write_text(f'''The Orchard packet is an unlaunched candidate. Its family retains the C8r base/runtime/trainer/export provenance and return locations, replaces the evaluation assets, and omits the old mask/geometry/cohort contract. The packet is not certified launch-ready; see `out/FAMILY.json` and `out/UNEXECUTED.md`.

Build a local packet after preparing the new assets:

```bash
cd {B}
./work/py code/venue.py packet --family out/FAMILY.json --assets out/ASSETS.json --out work/operator_packet --token 3917ab0dd64f429ac1e708fb
```

The batch file is submitted only from the authorized Orchard environment after local assets have been staged there. The asset manifest must contain Orchard-local source paths; use `venue.py stage` there to extract the same pinned archives. The large assets and export must already be present. This build performs no network operation and has not produced a generation-pinned cloud upload manifest.

```bash
export READ_CODE=/tmp/r01/code
export READ_CONFIG=/tmp/r01/packet/CONFIG.json
export READ_ASSETS=/tmp/r01/stage/ASSETS.json
export READ_ROOT=/tmp/r01/job
sbatch --account=mt01 --partition=general --gres=gpu:1 --time=07:00:00 /tmp/r01/packet/BATCH.sh
```

These exact paths describe the required staged layout; they do not assert that those files already exist. The worker runs the same `entry.py job` path and uses the inherited return publisher. The bound full allowance is stored in `out/FAMILY.json`. The return pool is `/project/community/jjyeung/okh7/n2r/<token>` and the GCS prefix is `gs://cmu-gpucloud-jjyeung/q8/n2r/<token>/`.

For a canary-only run or multiple cards, invoke the commands in `out/RUN_TRINITY.md` through `entry.py` in the staged namespace. Use one shared geometry manifest, a passed canary receipt, and separate shard output folders. Merge and report with those same bound inputs and geometry pins. The selected historical proof keys are `out/PROOF_KEYS.json`; its runner remains separate from this corpus.

Not completed: generation-pinned cloud asset publication, Orchard namespace rehearsal, remote return tests, and GPU parity. The packet refuses missing local assets; it is not a drop-in replacement accepted by the unmodified C8r launcher validator.
''')
